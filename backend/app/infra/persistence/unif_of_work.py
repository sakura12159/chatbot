from sqlalchemy.orm import Session

from app.domain.user.repositories import UserRepository
from app.domain.session.repositories import ChatSessionRepository

from app.infra.persistence.repositories.user_repo import UserRepository as UserRepositoryImpl
from app.infra.persistence.repositories.session_repo import ChatSessionRepository as ChatSessionRepositoryImpl

class UnitOfWork:
    """ 管理 sqlalchemy 事务 """
    def __init__(self, orm_session: Session) -> None:
        self._orm_session = orm_session
        self.user_repo: UserRepository = UserRepositoryImpl(orm_session=orm_session)
        self.session_repo: ChatSessionRepository = ChatSessionRepositoryImpl(orm_session=orm_session)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()

    def commit(self) -> None:
        """ 事务提交 """
        self._orm_session.commit()

    def rollback(self) -> None:
        """ 事务回滚 """
        self._orm_session.rollback()
