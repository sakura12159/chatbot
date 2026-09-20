from dataclasses import dataclass

from app.domain.message.value_objects import ChatMessage, ChatMessageRole
from app.domain.session.entities import ChatSession
from app.domain.tool.value_objects import ToolCall, ToolCallId


@dataclass(frozen=True)
class TokenUsage:
    """ token 消耗 """
    total_tokens: int               # 总消耗 token 数
    prompt_tokens: int              # 提示词消耗的 token 数
    prompt_cache_hit_tokens: int    # 输入缓存命中的 token 数
    prompt_cache_miss_tokens: int   # 输入缓存未命中的 token
    completion_tokens: int          # 输出消耗的 token 数
    reasoning_tokens: int = 0       # 推理消耗的 token 数

@dataclass(frozen=True)
class LLMMessage:
    """ 大模型消息，用于模型交互 """
    role: ChatMessageRole
    content: str
    reasoning_content: str | None = None
    tool_call_id: ToolCallId | None = None 
    tool_calls: list[ToolCall] | None = None

    @staticmethod
    def from_chat_message(message: ChatMessage) -> 'LLMMessage':
        """
        从 ChatMessage 创建 LLMMessage
        Args:
            message (ChatMessage): ChatMessage
        Returns: LLMMessage
            模型消息
        """            
        return LLMMessage(
            role=message.role,
            content=message.content,
            reasoning_content=message.reasoning_content,
            tool_calls=message.tool_calls,
            tool_call_id=message.tool_call_id
        )

@dataclass(frozen=True)
class ChatContext:
    """ 聊天上下文 """
    messages: list[LLMMessage]

    @staticmethod
    def from_chat_session(session: ChatSession) -> 'ChatContext':
        """
        从 ChatSession 创建 ChatContext
        Args:
            session (ChatSession): 会话实体
        Returns: ChatContext
            聊天上下文
        """
        messages = []
        # 添加总结的 message
        if session.summary:
            messages.append(
                session.create_chat_message(
                    role=ChatMessageRole.SYSTEM,
                    content=session.summary
                )
            )
        # 添加历史消息
        messages += [
            LLMMessage.from_chat_message(message=message) 
            for message in session.messages if not message.is_compressed
        ]

        return ChatContext(
            messages=messages
        )

    def with_prompt(self, prompt_messages: list[LLMMessage]) -> list[LLMMessage]:
        """
        添加提示词
        Args:
            prompt_messages (list[LLMMessage]): 系统提示词或任务提示词列表
        Returns: list[LLMMessage]
            带有提示词的消息列表
        """
        return prompt_messages + self.messages
