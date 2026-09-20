import time
import logging
from sqlalchemy import select
from sqlalchemy.orm import Session as ORMSession

from app.domain.user.value_objects import UserId
from app.infra.common.exceptions import PersistenceError
from app.infra.persistence.models.session_model import ChatSessionModel
from app.application.session.dto import ChatSessionInfoDTO
from shared.utils import get_time_duration

logger = logging.getLogger(__name__)

class SessionQueryImpl:
    def __init__(self, orm_session: ORMSession) -> None:
        self.orm_session = orm_session

    def query_session_list(self, user_id: UserId) -> list[ChatSessionInfoDTO]:
        """
        查询用户 id 对应的所有会话总结信息
        Args:
            user_id (UserId): 用户 id
        Returns: list[ChatSessionInfoDTO]
            包含会话总结信息的列表，以 created_at 降序排列
        """
        logger.info(
            '查询会话列表',
            extra={
                'user_id': user_id
            }
        )
        start_time = time.perf_counter()

        try:
            stmt = (
                select(
                    ChatSessionModel.id,
                    ChatSessionModel.title,
                    ChatSessionModel.total_tokens
                )
                .where(ChatSessionModel.user_id == user_id)
                .order_by(ChatSessionModel.updated_at.desc())   # 按更新时间降序
            )
            rows = self.orm_session.execute(stmt).all()

            logger.info(
                '查询会话列表成功',
                extra={
                    'user_id': user_id,
                    'duration_ms': get_time_duration(start_time=start_time)
                }
            )

            return [
                ChatSessionInfoDTO(
                    id=row.id,
                    title=row.title,
                    total_tokens=row.total_tokens
                ) 
                for row in rows
            ]

        except Exception as e:
            logger.exception(
                '查询会话列表失败',
                extra={
                    'user_id': user_id,
                    'duration_ms': get_time_duration(start_time=start_time)
                }
            )

            raise PersistenceError(f'数据库查询异常: {e}') from e
