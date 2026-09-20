import time
import logging
import json
from typing import Iterator

from app.domain.common.exceptions import SessionNotFoundError, TooManyToolCallsError
from app.domain.message.value_objects import ChatMessageRole
from app.domain.session.value_objects import ChatSessionId
from app.domain.session.entities import ChatSession
from app.domain.llm.value_objects import ChatContext
from app.domain.tool.value_objects import ToolCall
from app.domain.tool.registries import ToolRegistry
from app.domain.tool.executors import ToolExecutor
from app.application.common.exceptions import UnexpectedFinishReasonError
from app.application.common.unit_of_work import UnitOfWork
from app.application.llm.ports import LLMClient, TextSummarizer
from app.application.llm.dto import LLMRequestDTO
from app.application.llm.value_objects import LLMFinishReasonType
from app.application.chat.dto import ChatStreamResponseChunkDTOType, ChatStreamResponseChunkDTO, BalanceInfoDTO
from app.application.prompt.loaders import PromptLoader
from shared.config import LLM_MAX_REACT_ITERATIONS, LLM_COMPRESSION_TRIGGER_HISTORY_TURNS, LLM_COMPRESSION_TRIGGER_TOKENS, LLM_COMPRESSION_TURNS_PER_LOOP
from shared.utils import get_time_duration

logger = logging.getLogger(__name__)

class BalanceService:
    """
    账户服务
    负责查询账户信息
    """
    def __init__(self, llm_client: LLMClient) -> None:
        self.llm_client = llm_client

    def inquire_balance(self) -> BalanceInfoDTO:
        """ 账户余额查询 """
        response = self.llm_client.inquire_balance()
        return BalanceInfoDTO(
            is_available=response.is_available,
            currency=response.currency,
            total_balance=response.total_balance
        )

class ChatService:
    """
    聊天服务
    负责根据用户输入生成输出、总结会话、查询账户余额等
    """
    def __init__(
        self, 
        uow: UnitOfWork,
        llm_client: LLMClient,
        text_summarizer: TextSummarizer,
        prompt_loader: PromptLoader,
        tool_registry: ToolRegistry,
        tool_executor: ToolExecutor
    ) -> None:
        self.uow = uow

        self.llm_client = llm_client
        self.text_summarizer = text_summarizer
        self.prompt_loader = prompt_loader

        self.tool_registry = tool_registry
        self.tool_executor = tool_executor

    def _summarize_session_title_if_needed(self, session: ChatSession, query: str) -> None:
        """
        按需总结会话标题
        Args:
            session (ChatSession):  会话实体
            query (str):            用户输入
        """
        if session.is_new():
            logger.info(
                '调用会话标题总结',
                extra={
                    'query': query,
                    'user_id': session.user_id,
                    'session_id': session.id
                }
            )
            start_time = time.perf_counter()

            response = self.text_summarizer.summarize_session_title(query=query)
            # 增加 token 消耗计数
            if response.usage is not None:
                session.add_total_tokens(tokens=response.usage.total_tokens)
            session.set_title(title=response.content or 'New Session')

            logger.info(
                '会话标题总结成功',
                extra={
                    'query': query,
                    'user_id': session.user_id,
                    'session_id': session.id,
                    'duration_ms': get_time_duration(start_time=start_time)
                }
            )

    def _delete_last_turn_when_regenerating(self, session: ChatSession, regenerate: bool) -> None:
        """
        按需删除最近一轮消息
        Args:
            session (ChatSession):  会话实体
            regenerate (bool):          是否删除
        """
        if not regenerate:
            return

        logger.info(
            '调用删除最近一轮消息',
            extra={
                'session_id': session.id,
                'user_id': session.user_id,
                'messages_count': len(session.messages)
            }
        )
        start_time = time.perf_counter()

        session.remove_last_turn_messages()

        logger.info(
            '删除最近一轮消息成功',
            extra={
                'session_id': session.id,
                'user_id': session.user_id,
                'messages_count': len(session.messages),
                'duration_ms': get_time_duration(start_time=start_time)
            }
        )

    def _compress_session_history_if_needed(self, session: ChatSession, tokens: int = 0) -> None:
        """
        按需压缩会话历史
        Args:
            session (ChatSession):  会话实体
            tokens (int | None):    当前会话消耗的 token 数
        """
        uncompressed_turns = sum(message.role == ChatMessageRole.USER and not message.is_compressed for message in session.messages)
        # 未压缩的历史轮数小于阈值或作为下一次输入的当前轮消耗 token 数小于阈值时不进行历史压缩
        if uncompressed_turns < LLM_COMPRESSION_TRIGGER_HISTORY_TURNS and tokens < LLM_COMPRESSION_TRIGGER_TOKENS:
            return

        # 如果 tokens 超限，压缩一次；如果轮数超限，每次压缩 LLM_COMPRESSION_TURNS_PER_LOOP 轮数直到未压缩的历史轮数小于阈值
        if tokens >= LLM_COMPRESSION_TRIGGER_TOKENS:
            logger.info(
                '输出 tokens 超限，调用会话历史压缩', 
                extra={
                    'user_id': session.user_id,
                    'session_id': session.id,
                    'tokens': tokens
                }
            )
            self._compress_session_history_once(session=session)  # 压缩一次即可

        while True:
            uncompressed_turns = sum(message.role == ChatMessageRole.USER and not message.is_compressed for message in session.messages)
            if uncompressed_turns < LLM_COMPRESSION_TRIGGER_HISTORY_TURNS:
                break

            logger.info(
                '会话历史轮数超限，调用会话历史压缩', 
                extra={
                    'user_id': session.user_id,
                    'session_id': session.id,
                    'uncompressed_turns': uncompressed_turns
                }
            )
            self._compress_session_history_once(session=session)

    def _compress_session_history_once(self, session: ChatSession) -> None:
        """
        进行一次会话历史压缩，压缩较早的 LLM_COMPRESSION_TURNS_PER_LOOP 轮会话
        Args:
            session (ChatSession): 会话实体
        """
        cnt = LLM_COMPRESSION_TURNS_PER_LOOP
        start_idx, end_idx = None, len(session.messages)  # [start_idx, end_idx)
        for i, message in enumerate(session.messages):
            if message.is_compressed:
                continue
            if message.role == ChatMessageRole.USER:
                if start_idx is None:
                    start_idx = i
                else:
                    cnt -= 1
                    if cnt == 0:
                        end_idx = i
                        break

        if start_idx is None:  # 都被压缩过了
            return

        logger.info(
            '进行单次会话历史压缩',
            extra={
                'user_id': session.user_id,
                'session_id': session.id
            }
        )
        start_time = time.perf_counter()

        # 压缩最多 LLM_COMPRESSION_TURNS_PER_LOOP 个对话轮次
        messages_for_compress = session.messages[start_idx:end_idx]
        response = self.text_summarizer.summarize_messages(messages=messages_for_compress, previous_summary=session.summary)
        if response.usage is not None:
            session.add_total_tokens(tokens=response.usage.total_tokens)
        session.apply_history_compression(messages=messages_for_compress, summary=response.content)

        logger.info(
            '单次会话历史压缩成功',
            extra={
                'user_id': session.user_id,
                'session_id': session.id,
                'duration_ms': get_time_duration(start_time=start_time)
            }
        )
        
    def chat(
        self, 
        session_id: ChatSessionId, 
        query: str, 
        thinking: bool,
        web: bool,
        regenerate: bool = False
    ) -> Iterator[ChatStreamResponseChunkDTO]:
        """
        聊天方法
        Args:
            session_id (ChatSessionId): 会话 id
            query (str):                用户输入
            thinking (bool):            是否进行推理
            web (bool):                 是否可以使用网络工具进行搜索
            regenerate (bool):          是否为重新生成
        Returns: Iterator[ChatStreamResponseChunkDTO]
            流式生成的数据对象流
        """
        logger.info(
            '调用聊天',
            extra={
                'session_id': session_id,
                'query': query,
                'thinking': thinking,
                'web': web,
                'regenerate': regenerate
            }
        )
        start_time = time.perf_counter()

        with self.uow:
            # 查找对应 session 实体
            chat_session = self.uow.session_repo.find_by_id(id=session_id)
            if chat_session is None:
                logger.exception(
                    '调用聊天失败，查询不到对应会话',
                    extra={
                        'session_id': session_id,
                        'query': query,
                        'thinking': thinking,
                        'web': web,
                        'duration_ms': get_time_duration(start_time=start_time)
                    }
                )

                raise SessionNotFoundError(f'会话 id {session_id} 不存在')

            # 如果当前为重新生成，且上一轮消息已保存至数据库，先删除最近一轮消息
            self._delete_last_turn_when_regenerating(session=chat_session, regenerate=regenerate)

            # 如果当前会话中的轮数过多，压缩会话历史
            self._compress_session_history_if_needed(session=chat_session)

            # 如果当前会话是新建会话，根据用户输入总结会话标题
            self._summarize_session_title_if_needed(session=chat_session, query=query)

            # 添加当前的 message
            chat_session.append_message(
                chat_session.create_chat_message(
                    role=ChatMessageRole.USER, 
                    content=query
                )
            )

            # 控制网络相关工具的可使用状态
            self.tool_registry.set_web_tools_status(enabled=web)
            tools = self.tool_registry.list_tools()

            # 推理计时
            reasoning_start_time = time.perf_counter()
            reasoning_time = None

            # ReAct loop
            for _ in range(LLM_MAX_REACT_ITERATIONS):
                chat_context = ChatContext.from_chat_session(session=chat_session)
                messages = chat_context.with_prompt(prompt_messages=self.prompt_loader.load_chat_prompt(chat_session.summary))

                # 需要收集的信息
                content = ''
                reasoning_content = ''
                tool_calls_map = {}
                finish_reason = ''
                token_usage = None

                # 请求与响应
                request = LLMRequestDTO(
                    messages=messages,
                    thinking=thinking,
                    tools=tools,
                    token_usage=True
                )
                response = self.llm_client.generate_stream(request=request)
                for chunk in response:
                    chunk_type = ChatStreamResponseChunkDTOType.IGNORED
                    if chunk.content:
                        content += chunk.content
                        chunk_type = ChatStreamResponseChunkDTOType.MARKDOWN
                    if chunk.reasoning_content is not None:
                        reasoning_content += chunk.reasoning_content
                        chunk_type = ChatStreamResponseChunkDTOType.THINKING
                    if chunk.finish_reason is not None:
                        finish_reason = chunk.finish_reason
                    if chunk.usage is not None:
                        token_usage = chunk.usage
                    if chunk.tool_calls is not None:
                        chunk_type = ChatStreamResponseChunkDTOType.TOOL_CALL
                        for tool_call in chunk.tool_calls:
                            idx = tool_call.index
                            if idx not in tool_calls_map:
                                tool_calls_map[idx] = {
                                    'index': idx,
                                    'id': '',
                                    'type': 'function',
                                    'function': {
                                        'name': '',
                                        'arguments': ''
                                    }
                                }
                            if tool_call.id is not None:
                                tool_calls_map[idx]['id'] = tool_call.id
                            if tool_call.name is not None:
                                tool_calls_map[idx]['function']['name'] += tool_call.name
                            if tool_call.arguments is not None:
                                tool_calls_map[idx]['function']['arguments'] += tool_call.arguments

                    # 判断推理是否结束，如果此时结束统计推理时间，返回一个包含推理时间的空 chunk
                    if thinking and chunk_type == ChatStreamResponseChunkDTOType.MARKDOWN:
                        thinking = False
                        reasoning_time = time.perf_counter() - reasoning_start_time
                        yield ChatStreamResponseChunkDTO(
                            type=ChatStreamResponseChunkDTOType.THINKING,
                            content=None,
                            reasoning_content=None,
                            reasoning_time=reasoning_time,
                            done=False
                        )

                    yield ChatStreamResponseChunkDTO(
                        type=chunk_type,
                        content=chunk.content,
                        reasoning_content=chunk.reasoning_content,
                        reasoning_time=None,
                        done=False
                    )

                # 根据 finish reason 判断是应该调用工具还是结束 loop
                if finish_reason == LLMFinishReasonType.STOP.value:
                    # 结束 chunk
                    yield ChatStreamResponseChunkDTO(
                        type=ChatStreamResponseChunkDTOType.IGNORED,
                        content=None,
                        reasoning_content=None,
                        reasoning_time=None,
                        done=True
                    )

                    break
                
                elif finish_reason == LLMFinishReasonType.TOOL_CALLS.value:
                    # 添加工具调用信息
                    tool_calls = [ToolCall(
                        index=tool_call['index'],
                        id=tool_call['id'],
                        name=tool_call['function']['name'],
                        arguments=json.loads(tool_call['function']['arguments'])
                    ) for tool_call in tool_calls_map.values()]
                    chat_session.append_message(
                        chat_session.create_chat_message(
                            role=ChatMessageRole.ASSISTANT,
                            content=content,
                            reasoning_content=reasoning_content or None,
                            tool_calls=tool_calls
                        )
                    )
                    # 执行工具并添加工具调用结果
                    for tool_call in tool_calls:
                        tool_message = self.tool_executor.execute(tool_call=tool_call)
                        chat_session.append_message(
                            chat_session.create_chat_message(
                                role=ChatMessageRole.TOOL,
                                content=json.dumps(tool_message.result, ensure_ascii=False),
                                tool_call_id=tool_message.id
                            )
                        )

                else:
                    logger.exception(
                        '调用聊天失败，模型生成异常停止',
                        extra={
                            'session_id': session_id,
                            'query': query,
                            'thinking': thinking,
                            'web': web,
                            'duration_ms': get_time_duration(start_time=start_time)
                        }
                    )

                    raise UnexpectedFinishReasonError(f'模型生成异常停止: {finish_reason}')
            else:
                logger.exception(
                    '调用聊天失败，模型调用工具轮数过多',
                    extra={
                        'session_id': session_id,
                        'query': query,
                        'thinking': thinking,
                        'web': web,
                        'duration_ms': get_time_duration(start_time=start_time)
                    }
                )
                
                raise TooManyToolCallsError(f'调用工具轮数过多')

            # 添加 llm 回复消息
            chat_session.append_message(
                chat_session.create_chat_message(
                    role=ChatMessageRole.ASSISTANT,
                    content=content,
                    reasoning_content=reasoning_content or None,
                    reasoning_time=reasoning_time
                )
            )

            tokens = 0
            # 增加 token 消耗计数
            if token_usage is not None:
                tokens = token_usage.total_tokens
                chat_session.add_total_tokens(token_usage.total_tokens)

            # 压缩会话历史
            self._compress_session_history_if_needed(session=chat_session, tokens=tokens)

            # 保存 session
            self.uow.session_repo.save(session=chat_session)

            logger.info(
                '调用聊天完毕',
                extra={
                    'session_id': session_id,
                    'query': query,
                    'thinking': thinking,
                    'web': web,
                    'duration_ms': get_time_duration(start_time=start_time)
                }
            )
