from dataclasses import dataclass

from app.domain.llm.value_objects import LLMMessage, TokenUsage
from app.domain.message.value_objects import ChatMessageRole
from app.domain.tool.value_objects import ToolCall, ToolCallChunk
from app.domain.tool.entities import Tool
from app.application.llm.value_objects import LLMFinishReasonType

@dataclass(frozen=True)
class LLMRequestDTO:
    """ 模型请求 dto """
    messages: list[LLMMessage]
    thinking: bool = False
    tools: list[Tool] | None = None
    token_usage: bool = False
    json_output: bool = False

@dataclass(frozen=True)
class LLMStreamResponseChunkDTO:
    """ 流式模型响应块 dto """
    content: str | None
    reasoning_content: str | None
    tool_calls: list[ToolCallChunk] | None
    finish_reason: LLMFinishReasonType | None
    usage: TokenUsage | None
    role: ChatMessageRole = ChatMessageRole.ASSISTANT

@dataclass(frozen=True)
class LLMResponseDTO:
    """ 非流式模型响应 dto """
    content: str
    reasoning_content: str | None
    tool_calls: list[ToolCall] | None
    finish_reason: LLMFinishReasonType
    usage: TokenUsage | None
    role: ChatMessageRole = ChatMessageRole.ASSISTANT

@dataclass(frozen=True)
class InquireBalanceResponseDTO:
    """ 查询账户余额 dto """
    is_available: bool
    currency: str
    total_balance: str
