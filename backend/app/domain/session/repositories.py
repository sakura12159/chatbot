from typing import Protocol

from app.domain.session.entities import ChatSession
from app.domain.session.value_objects import ChatSessionId

class ChatSessionRepository(Protocol):
    """
    会话表操作类
    负责查找、删除和保存新建或修改的会话
    """
    
    def find_by_id(self, id: ChatSessionId) -> ChatSession | None:
        """
        查询会话 id 对应会话
        Args:
            id (ChatSessionId): 会话 id
        Returns: ChatSession
            会话实体
        """
        ...

    def delete_by_id(self, id: ChatSessionId) -> None:
        """
        删除会话
        Args:
            id (ChatSessionId): 会话 id
        """
        ...

    def save(self, session: ChatSession) -> None:
        """
        保存会话及更新内容
        Args:
            session (ChatSession): 会话实体
        """
        ...
