from typing import Protocol

from app.domain.user.value_objects import UserId
from app.application.session.dto import ChatSessionInfoDTO

class SessionQuery(Protocol):
    """
    负责查询用户所有会话的总结信息
    """

    def query_session_list(self, user_id: UserId) -> list[ChatSessionInfoDTO]:
        """
        查询用户 id 对应的所有会话总结信息
        Args:
            user_id (UserId): 用户 id
        Returns: list[ChatSessionInfoDTO]
            包含会话总结信息的列表，以 created_at 降序排列
        """
        ...
