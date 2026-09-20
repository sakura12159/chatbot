from enum import Enum
from dataclasses import dataclass

class ChatStreamResponseChunkDTOType(Enum):
    """ 聊天流式响应块 dto 类型 """
    IGNORED = 'ignored'

    TEXT = 'text'
    MARKDOWN = 'markdown'
    THINKING = 'thinking'
    TOOL_CALL = 'tool_call'

@dataclass(frozen=True)
class ChatStreamResponseChunkDTO:
    """ 聊天流式响应块 dto """
    type: ChatStreamResponseChunkDTOType
    content: str | None
    reasoning_content: str | None
    reasoning_time: float | None
    done: bool

@dataclass(frozen=True)
class BalanceInfoDTO:
    """ 账户余额信息 dto """
    is_available: bool
    currency: str
    total_balance: str
