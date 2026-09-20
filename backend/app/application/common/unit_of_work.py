from typing import Protocol, Any

from app.domain.user.repositories import UserRepository
from app.domain.session.repositories import ChatSessionRepository

class UnitOfWork(Protocol):
    """
    事务工作单元
    负责事务的提交与回滚
    """
    user_repo: UserRepository
    session_repo: ChatSessionRepository

    def __enter__(self) -> Any:
        """ 上下文管理 进入 """
        ...

    def __exit__(self, exc_type, exc, tb) -> Any:
        """ 上下文管理 退出 """
        ...

    def commit(self) -> Any:
        """ 事务提交 """
        ...

    def rollback(self) -> Any:
        """ 事务回滚 """
        ...
