from dataclasses import dataclass

from app.domain.common.value_objects import TimeStamp
from app.domain.message.value_objects import ChatMessageId, ChatMessage, ChatMessageRole
from app.domain.session.value_objects import ChatSessionId
from app.application.message.value_objects import ChatMessageDTOType
    
@dataclass
class ChatMessageDTO:
    """ 聊天消息 dto """
    id: ChatMessageId
    session_id: ChatSessionId
    role: ChatMessageRole
    content: str
    created_at: TimeStamp
    reasoning_content: str | None
    reasoning_time: float | None
    is_compressed: bool

    type: ChatMessageDTOType = ChatMessageDTOType.IGNORED

    def __post_init__(self):
        """ 判断该信息的类型 """
        if self.role == ChatMessageRole.USER:
            self.type = ChatMessageDTOType.TEXT  # 用户输入
        elif self.role == ChatMessageRole.ASSISTANT:
            self.type = ChatMessageDTOType.MARKDOWN  # 模型回复
            if self.reasoning_content is not None:
                self.type = ChatMessageDTOType.THINKING  # 推理过程
        elif self.role == ChatMessageRole.TOOL:
            self.type = ChatMessageDTOType.TOOL_CALL
        else:  # 系统提示词等标记为忽略
            # self.type = ChatMessageDTOType.IGNORED
            pass

    @staticmethod
    def from_chat_message(message: ChatMessage) -> 'ChatMessageDTO':
        """
        从 ChatMessage 创建 ChatMessageDTO
        Args:
            message (ChatMessage): ChatMessage
        Returns: ChatMessageDTO
            ChatMessageDTO
        """
        return ChatMessageDTO(
            id=message.id,
            session_id=message.session_id,
            role=message.role,
            content=message.content,
            created_at=message.created_at,
            reasoning_content=message.reasoning_content,
            reasoning_time=message.reasoning_time,
            is_compressed=message.is_compressed
        )
