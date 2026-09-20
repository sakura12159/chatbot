import uuid
from enum import Enum
from typing import NewType
from dataclasses import dataclass

from app.domain.common.value_objects import TimeStamp
from app.domain.session.value_objects import ChatSessionId
from app.domain.tool.value_objects import ToolCall, ToolCallId

ChatMessageId = NewType('ChatMessageId', uuid.UUID)

class ChatMessageRole(Enum):
    """ 消息角色 """
    SYSTEM = 'system'
    USER = 'user'
    ASSISTANT = 'assistant'
    TOOL = 'tool'

@dataclass
class ChatMessage:
    """ 聊天消息 """
    id: ChatMessageId
    session_id: ChatSessionId
    role: ChatMessageRole
    content: str
    created_at: TimeStamp
    reasoning_content: str | None = None
    reasoning_time: float | None = None
    tool_call_id: ToolCallId | None = None
    tool_calls: list[ToolCall] | None = None
    is_compressed: bool = False

    def mark_as_compressed(self) -> None:
        """ 将当前消息标记为已压缩 """
        self.is_compressed = True
