from dataclasses import dataclass, field

from app.domain.common.value_objects import TimeStamp
from app.domain.user.value_objects import UserId
from app.domain.session.value_objects import ChatSessionId
from app.domain.session.entities import ChatSession
from app.application.message.dto import ChatMessageDTO

@dataclass
class ChatSessionDTO:
    """ 会话 dto """
    id: ChatSessionId
    user_id: UserId
    title: str
    created_at: TimeStamp
    total_tokens: int
    
    messages: list[ChatMessageDTO] = field(default_factory=list)

    @staticmethod
    def from_session(session: ChatSession) -> 'ChatSessionDTO':
        """
        从会话实体创建 ChatSessionDTO
        Args:
            session (ChatSession): 会话实体
        Returns: ChatSessionDTO
            ChatSessionDTO
        """
        return ChatSessionDTO(
            id=session.id,
            user_id=session.user_id,
            title=session.title,
            created_at=session.created_at,
            total_tokens=session.total_tokens,
            messages=list(map(ChatMessageDTO.from_chat_message, session.messages))
        )

@dataclass
class ChatSessionInfoDTO:
    id: ChatSessionId
    title: str
    total_tokens: int
