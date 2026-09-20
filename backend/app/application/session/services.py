import time
import logging

from app.domain.common.exceptions import SessionNotFoundError
from app.domain.user.value_objects import UserId
from app.domain.session.value_objects import ChatSessionId
from app.domain.session.entities import ChatSession
from app.application.common.unit_of_work import UnitOfWork
from app.application.session.dto import ChatSessionDTO, ChatSessionInfoDTO
from app.application.session.queries import SessionQuery
from shared.utils import get_time_duration

logger = logging.getLogger(__name__)

class SessionService:
    """
    会话服务
    负责创建、查询、修改和删除会话
    """
    def __init__(self, uow: UnitOfWork, session_query: SessionQuery) -> None:
        self.uow = uow
        self.session_query = session_query

    def create_session(self, user_id: UserId) -> ChatSessionDTO:
        """
        根据用户创建会话
        Args:
            user_id (UserId): 用户 id
        Returns: ChatSession
            会话 dto
        """
        logger.info(
            '调用创建会话',
            extra={
                'user_id': user_id
            }
        )
        start_time = time.perf_counter()

        session = ChatSession.create(user_id=user_id)
        with self.uow:
            self.uow.session_repo.save(session=session)

        logger.info(
            '创建会话成功',
            extra={
                'user_id': user_id,
                'session_id': session.id,
                'duration_ms': get_time_duration(start_time=start_time)
            }
        )

        return ChatSessionDTO.from_session(session=session)

    def get_session(self, session_id: ChatSessionId) -> ChatSessionDTO:
        """
        获取指定会话信息
        Args:
            session_id (ChatSessionId): 会话 id
        Returns: ChatSessionInfoDTO
            会话信息
        """
        logger.info(
            '调用查询会话',
            extra={
                'session_id': session_id
            }
        )
        start_time = time.perf_counter()

        session = self.uow.session_repo.find_by_id(id=session_id)
        if session is None:
            logger.exception(
                '查询会话失败',
                extra={
                    'session_id': session_id,
                    'duration_ms': get_time_duration(start_time=start_time)
                }
            )

            raise SessionNotFoundError(message=f'会话 id {id} 不存在')

        logger.info(
            '查询会话成功',
            extra={
                'user_id': session.user_id,
                'session_id': session_id,
                'duration_ms': get_time_duration(start_time=start_time)
            }
        )

        return ChatSessionDTO.from_session(session=session)

    def list_sessions(self, user_id: UserId) -> list[ChatSessionInfoDTO]:
        """
        列出用户所有会话信息
        Args:
            user_id (UserId): 用户 id
        Returns: list[ChatSessionInfoDTO]
            会话信息列表
        """
        return self.session_query.query_session_list(user_id=user_id)

    def delete_session(self, session_id: ChatSessionId) -> None:
        """
        删除会话
        Args:
            session_id (ChatSessionId): 会话 id
        """
        logger.info(
            '调用删除会话',
            extra={
                'session_id': session_id
            }
        )
        start_time = time.perf_counter()

        with self.uow:
            self.uow.session_repo.delete_by_id(id=session_id)

        logger.info(
            '删除会话成功',
            extra={
                'session_id': session_id,
                'duration_ms': get_time_duration(start_time=start_time)
            }
        )
