import time
import json
import logging
from typing import Literal, Any, Iterator, Literal

from app.domain.message.value_objects import ChatMessageRole, ChatMessage
from app.domain.tool.value_objects import ToolCall, ToolCallChunk
from app.domain.tool.entities import Tool
from app.domain.llm.value_objects import LLMMessage, ChatContext, TokenUsage
from app.infra.external.http.http_client import HttpClient
from app.application.common.exceptions import LLMError
from app.application.prompt.loaders import PromptLoader
from app.application.llm.ports import LLMClient as LLMClientPTC
from app.application.llm.dto import LLMRequestDTO, LLMResponseDTO, LLMStreamResponseChunkDTO, InquireBalanceResponseDTO
from shared.config import LLM_BASE_URL, LLM_CHAT_COMPLETIONS_PATH, LLM_BALANCE_INQUERY_PATH, LLM_API_KEY, LLM_CHAT_MODEL, LLM_MAX_TOKENS_PER_GENERATION, \
    LLM_REASONING_EFFORT, LLM_TEMPERATURE, LLM_TOP_P, LLM_TIMEOUT_SECONDS
from shared.utils import get_time_duration

logger = logging.getLogger(__name__)

class LLMClient(HttpClient):
    """
    大模型端口，遵循 OpenAI Chat Completions API 规则
    负责模型聊天内容生成与账户余额查询
    """
    def __init__(self):
        if LLM_API_KEY is None:
            logger.error('初始化聊天客户端失败: 环境变量中不存在 LLM api key')
            raise LLMError('初始化聊天客户端失败: 环境变量中不存在 LLM api key')

        super().__init__(
            base_url=LLM_BASE_URL, 
            timeout=LLM_TIMEOUT_SECONDS, 
            headers={
                'Authorization': f'Bearer {LLM_API_KEY}'
            }
        )

    def _tool_call_to_dict(self, tool_call: ToolCall) -> dict[str, Any]:
        """
        将 ToolCall 按规则转换为字典
        Args:
            tool_call (ToolCall): 工具调用
        Returns: dict[str, Any]
            符合 api 输入格式的字典
        """
        res: dict[str, Any] = {
            'id': tool_call.id,
            'type': 'function',
            'function': {
                'name': tool_call.name,
                'arguments': json.dumps(tool_call.arguments, ensure_ascii=False)
            }
        }
        if tool_call.index is not None:
            res['index'] = tool_call.index
            
        return res

    def _llm_message_to_dict(self, message: LLMMessage) -> dict[str, Any]:
        """
        将 LLMMessage 按规则转换为字典
        Args:
            message (LLMMessage): LLMMessage
        Returns: dict[str, Any]
            符合 api 输入格式的字典
        """
        res: dict[str, Any] = {
            'role': message.role.value,
            'content': message.content
        }
        if message.reasoning_content is not None:
            res['reasoning_content'] = message.reasoning_content
        if message.tool_call_id is not None:
            res['tool_call_id'] = message.tool_call_id
        if message.tool_calls is not None:
            res['tool_calls'] = list(map(self._tool_call_to_dict, message.tool_calls))
        return res

    def _request_chat_completions(
        self,
        *,
        messages: list[dict[str, str]],
        model: Literal['deepseek-v4-flash', 'deepseek-v4-pro'] = LLM_CHAT_MODEL,
        thinking: dict[str, str] | None = None,
        reasoning_effort: Literal['high', 'max'] = LLM_REASONING_EFFORT,
        max_tokens: int | None = LLM_MAX_TOKENS_PER_GENERATION,
        response_format: dict[str, str] | None = None,
        stop: str | list[str] | None = None,
        temperature: float | None = LLM_TEMPERATURE,
        top_p: float | None = LLM_TOP_P,
        tools: list[dict[str, Any]] | None = None,
        tool_choice:  Literal['none', 'auto', 'required'] | dict[str, Any] | None = None,
        logprobs: bool | None = None,
        top_logprobs: int | None = None,
        user_id: str | None = None
    ) -> dict:
        """
        非流式模型对话补全，参数见 https://api-docs.deepseek.com/zh-cn/api/create-chat-completion
        Args:
            messages (list[dict[str, str]]):                                                模型输入
            api_key (str | None):                                                       deepseek api key
            model (Literal['deepseek-v4-flash', 'deepseek-v4-pro']):                    模型名称
            thinking (dict[str, str] | None):                                           是否开启思考模式
            reasoning_effort (Literal['high', 'max']):                                  推理强度
            max_tokens (int | None):                                                    模型最大生成 token 数
            response_format (dict[str, str] | None):                                    补全格式
            stop (str | list[str] | None):                                              停止 token
            temperature (float | None):                                                 模型采样温度
            top_p (float | None):                                                       模型采样 topp
            tools (list[dict[str, Any]] | None):                                        可调用的工具
            tool_choice (Literal['none', 'auto', 'required'] | dict[str, Any] | None):  工具选择参数
            logprobs (bool | None):                                                     是否返回 token 对数概率分布
            top_logprobs (int | None):                                                  返回概率 topk 高的 token
            user_id (str | None):                                                       自定义的 user id
        Returns: dict
            非流式模型对话补全响应
        """
        payload = {
            'messages': messages,
            'model': model,
            'thinking': thinking,
            'reasoning_effort': reasoning_effort,
            'max_tokens': max_tokens,
            'response_format': response_format,
            'stop': stop,
            'stream': False,
            'stream_options': None,
            'temperature': temperature,
            'top_p': top_p,
            'tools': tools,
            'tool_choice': tool_choice,
            'logprobs': logprobs,
            'top_logprobs': top_logprobs,
            'user_id': user_id
        }

        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        return self.post(
            path=LLM_CHAT_COMPLETIONS_PATH,
            json=payload,
            headers=headers
        )

    def _stream_chat_completions(
        self,
        *,
        messages: list[dict[str, str]],
        model: Literal['deepseek-v4-flash', 'deepseek-v4-pro'] = LLM_CHAT_MODEL,
        thinking: dict[str, str] | None = None,
        reasoning_effort: Literal['high', 'max'] = LLM_REASONING_EFFORT,
        max_tokens: int | None = LLM_MAX_TOKENS_PER_GENERATION,
        response_format: dict[str, str] | None = None,
        stop: str | list[str] | None = None,
        stream_options: dict[str, bool] | None = None,
        temperature: float | None = LLM_TEMPERATURE,
        top_p: float | None = LLM_TOP_P,
        tools: list[dict[str, Any]] | None = None,
        tool_choice:  Literal['none', 'auto', 'required'] | dict[str, Any] | None = None,
        logprobs: bool | None = None,
        top_logprobs: int | None = None,
        user_id: str | None = None
    ) -> Iterator[str]:
        """
        流式模型对话补全，参数见 https://api-docs.deepseek.com/zh-cn/api/create-chat-completion
        Args:
            messages (list[dict[str, str]]):                                            模型输入
            api_key (str | None):                                                       deepseek api key
            model (Literal['deepseek-v4-flash', 'deepseek-v4-pro']):                    模型名称
            thinking (dict[str, str] | None):                                           是否开启思考模式
            reasoning_effort (Literal['high', 'max']):                                  推理强度
            max_tokens (int | None):                                                    模型最大生成 token 数
            response_format (dict[str, str] | None):                                    补全格式
            stop (str | list[str] | None):                                              停止 token
            stream_options (dict[str, bool] | None):                                    流式生成参数
            temperature (float | None):                                                 模型采样温度
            top_p (float | None):                                                       模型采样 topp
            tools (list[dict[str, Any]] | None):                                        可调用的工具
            tool_choice (Literal['none', 'auto', 'required'] | dict[str, Any] | None):  工具选择参数
            logprobs (bool | None):                                                     是否返回 token 对数概率分布
            top_logprobs (int | None):                                                  返回概率 topk 高的 token
            user_id (str | None):                                                       自定义的 user id
        Returns: Iterator[str]
            模型流式对话补全响应
        """
        payload = {
            'messages': messages,
            'model': model,
            'thinking': thinking,
            'reasoning_effort': reasoning_effort,
            'max_tokens': max_tokens,
            'response_format': response_format,
            'stop': stop,
            'stream': True,
            'stream_options': stream_options,
            'temperature': temperature,
            'top_p': top_p,
            'tools': tools,
            'tool_choice': tool_choice,
            'logprobs': logprobs,
            'top_logprobs': top_logprobs,
            'user_id': user_id
        }
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'text/event-stream'
        }
        for chunk in self.stream(
            method='POST',
            path=LLM_CHAT_COMPLETIONS_PATH,
            json=payload,
            headers=headers
        ):
            yield chunk

    def _generate(
        self,
        *,
        messages: list[LLMMessage],
        thinking: bool = False,
        include_usage: bool = False,
        tools: list[Tool] | None = None,
        json_output: bool = False,
        **kwargs
    ) -> dict:
        """
        非流式模型生成
        Args:
            messages (list[LLMMessage]):            上下文
            thinking (bool):                        是否开启思考模式
            include_usage (bool):                   是否在流式生成时返回 token 消耗信息
            tools (list[ToolSchema] | None):        可调用的工具
            json_output (bool):                     是否输出强制为 json 结构
        Returns: dict
            非流式模型生成结果
        """
        logger.debug(
            '调用模型非流式生成',
            extra={
                'messages_count': len(messages),
                'thinking': thinking,
                'include_usage': include_usage,
                'json_output': json_output
            }
        )
        start_time = time.perf_counter()

        res = self._request_chat_completions(
            messages=list(map(self._llm_message_to_dict, messages)),
            thinking={'type': 'enabled' if thinking else 'disabled'},
            tools=[tool.schema for tool in (tools or [])],
            response_format={'type': 'json_object' if json_output else 'text'},
            **kwargs
        )

        logger.debug(
            '模型非流式生成成功',
            extra={
                'messages_count': len(messages),
                'thinking': thinking,
                'include_usage': include_usage,
                'json_output': json_output,
                'duration_ms': get_time_duration(start_time=start_time)
            }
        )
        
        return res

    def _generate_stream(
        self,
        *,
        messages: list[LLMMessage],
        thinking: bool = False,
        include_usage: bool = False,
        tools: list[Tool] | None = None,
        json_output: bool = False,
        **kwargs
    ) -> Iterator[str]:
        """
        模型流式生成
        Args:
            messages (list[LLMMessage]):            上下文
            thinking (bool):                        是否开启思考模式
            include_usage (bool):                   是否在流式生成时返回 token 消耗信息
            tools (list[ToolSchema] | None):        可调用的工具
            json_output (bool):                     是否输出强制为 json 结构
        Returns: Iterator[str]
            模型流式生成结果
        """
        logger.debug(
            '调用模型流式生成',
            extra={
                'messages_count': len(messages),
                'thinking': thinking,
                'include_usage': include_usage,
                'json_output': json_output
            }
        )
        start_time = time.perf_counter()

        for chunk in self._stream_chat_completions(
            messages=list(map(self._llm_message_to_dict, messages)),
            thinking={'type': 'enabled' if thinking else 'disabled'},
            stream_options={'include_usage': True} if include_usage else None,
            tools=[tool.schema for tool in (tools or [])],
            response_format={'type': 'json_object' if json_output else 'text'},
            **kwargs
        ):
            yield chunk

        logger.debug(
            '模型流式生成成功',
            extra={
                'messages_count': len(messages),
                'thinking': thinking,
                'include_usage': include_usage,
                'json_output': json_output,
                'duration_ms': get_time_duration(start_time=start_time)
            }
        )
        
    def generate(self, request: LLMRequestDTO) -> LLMResponseDTO:
        """
        模型非流式生成
        Args:
            request (LLMRequestDTO): 模型请求值对象
        Returns: LLMResponseDTO
            模型响应值对象
        """
        completions = self._generate(
            messages=request.messages,
            thinking=request.thinking,
            include_usage=request.token_usage,
            tools=request.tools,
            json_output=request.json_output
        )
        usage = completions['usage'] if request.token_usage else None
        if usage is not None:
            usage = TokenUsage(
                total_tokens=usage['total_tokens'],
                prompt_tokens=usage['prompt_tokens'],
                completion_tokens=usage['completion_tokens'],
                prompt_cache_hit_tokens=usage['prompt_cache_hit_tokens'],
                prompt_cache_miss_tokens=usage['prompt_cache_miss_tokens'],
                reasoning_tokens=usage.get('completion_tokens_details', {}).get('reasoning_tokens', 0)
            )

        completion = completions['choices'][0]
        finish_reason = completion['finish_reason']
        message = completion['message']

        content = message['content']
        reasoning_content = message.get('reasoning_content', None)
        tool_calls = message.get('tool_calls', None)
        if tool_calls is not None:
            tool_calls = [
                ToolCall(
                    index=None,
                    id=tool_call['id'],
                    name=tool_call['function']['name'],
                    arguments=tool_call['function']['arguments']
                ) for tool_call in message['tool_calls']
            ]

        return LLMResponseDTO(
            role=ChatMessageRole.ASSISTANT,
            content=content,
            reasoning_content=reasoning_content,
            tool_calls=tool_calls,
            finish_reason=finish_reason,
            usage=usage
        )

    def generate_stream(self, request: LLMRequestDTO) -> Iterator[LLMStreamResponseChunkDTO]:
        """
        模型流式生成
        Args:
            request (LLMRequestDTO): 模型请求值对象
        Returns: Iterator[LLMStreamResponseChunkDTO]
            模型流式响应块值对象生成器
        """
        for chunk in self._generate_stream(
            messages=request.messages,
            thinking=request.thinking,
            include_usage=request.token_usage,
            tools=request.tools,
            json_output=request.json_output
        ):
            if not chunk:
                continue

            chunk = chunk[6:]
            if chunk == '[DONE]':
                break

            data = json.loads(chunk)
            usage = data.get('usage', None)

            completion = data['choices'][0]
            delta = completion['delta']
            finish_reason = completion.get('finish_reason', None)
            if usage is not None:
                usage = TokenUsage(
                    total_tokens=usage['total_tokens'],
                    prompt_tokens=usage['prompt_tokens'],
                    completion_tokens=usage['completion_tokens'],
                    prompt_cache_hit_tokens=usage['prompt_cache_hit_tokens'],
                    prompt_cache_miss_tokens=usage['prompt_cache_miss_tokens'],
                    reasoning_tokens=usage.get('completion_tokens_details', {}).get('reasoning_tokens', 0)
                )

            content = delta.get('content', None)
            reasoning_content = delta.get('reasoning_content', None)
            tool_calls = delta.get('tool_calls', None)
            if tool_calls is not None:
                tool_calls = [
                    ToolCallChunk(
                        index=tool_call['index'],
                        id=tool_call.get('id', None),
                        name=tool_call['function'].get('name', None),
                        arguments=tool_call['function'].get('arguments', None)
                    ) for tool_call in tool_calls
                ]
            
            yield LLMStreamResponseChunkDTO(
                role=ChatMessageRole.ASSISTANT,
                content=content,
                reasoning_content=reasoning_content,
                tool_calls=tool_calls,
                usage=usage,
                finish_reason=finish_reason
            )

    def inquire_balance(self) -> InquireBalanceResponseDTO:
        """
        账号余额信息查询
        Returns: InquireBalanceResponseDTO
            账号余额查询响应
        """
        logger.info('调用账户余额查询')
        start_time = time.perf_counter()

        headers = {
            'Accept': 'application/json'
        }
        res = self.get(path=LLM_BALANCE_INQUERY_PATH, headers=headers)

        logger.info(
            '账户余额查询成功',
            extra={
                'duration_ms': get_time_duration(start_time=start_time)
            }
        )

        return InquireBalanceResponseDTO(
            is_available=res['is_available'],
            currency=res['balance_infos'][0]['currency'],
            total_balance=res['balance_infos'][0]['total_balance'],
        )

class TextSummarizer:
    """
    基于 OpenAI Chat Completions API 格式的文本总结器
    负责调用 llm 进行各种文本总结工作
    """
    def __init__(self, llm_client: LLMClientPTC, prompt_loader: PromptLoader) -> None:
        self.llm_client = llm_client
        self.prompt_loader = prompt_loader

    def summarize_session_title(self, query: str) -> LLMResponseDTO:
        """
        总结会话标题
        Args:
            query (str): 用户输入
        Returns: LLMResponseDTO
            包含 llm 生成会话标题的响应
        """
        logger.info(
            '调用会话标题总结',
            extra={
                'query': query
            }
        )
        start_time = time.perf_counter()

        messages = ChatContext(
            messages=[LLMMessage(role=ChatMessageRole.USER, content=query)]
        ).with_prompt(
            prompt_messages=self.prompt_loader.load_session_title_summarization_prompt(query=query)
        )
        request = LLMRequestDTO(messages=messages, token_usage=True)
        response = self.llm_client.generate(request=request)

        logger.info(
            '会话标题总结成功',
            extra={
                'query': query,
                'duration_ms': get_time_duration(start_time=start_time)
            }
        )

        return response

    def summarize_messages(self, messages: list[ChatMessage], previous_summary: str) -> LLMResponseDTO:
        """
        结合当前会话与之前的总结重新生成会话历史总结
        Args:
            messages (list[ChatMessage]):   当前的会话
            previous_summary (str):         之前总结的会话历史
        Returns: LLMResponseDTO
            包含 llm 生成新总结会话历史的响应
        """
        logger.info(
            '调用会话历史压缩',
            extra={
                'messages_count': len(messages),
                'previous_summary': previous_summary
            }
        )
        start_time = time.perf_counter()

        llm_messages = ChatContext(
            messages=list(map(LLMMessage.from_chat_message, messages))
        ).with_prompt(
            prompt_messages=self.prompt_loader.load_session_history_compression_prompt(
                conversation_text='\n'.join(f'{message.role}: {message.content}' for message in messages),
                previous_summary=previous_summary
            )
        )
        request = LLMRequestDTO(
            messages=llm_messages,
            thinking=True,
            token_usage=True
        )
        response = self.llm_client.generate(request=request)
        
        logger.info(
            '会话历史压缩成功',
            extra={
                'messages_count': len(messages),
                'previous_summary': previous_summary,
                'current_summary': response.content,
                'duration_ms': get_time_duration(start_time=start_time)
            }
        )

        return response
