import time
import logging

from app.domain.user.value_objects import UserId
from app.domain.user.entities import User
from app.application.user.dto import UserDTO
from app.application.common.unit_of_work import UnitOfWork
from shared.utils import get_time_duration

logger = logging.getLogger(__name__)

class UserService:
    """
    用户服务
    负责创建和删除用户
    """
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    def sign_in(self, name: str) -> UserDTO:
        """
        用户登录，如果该用户不存在则创建新用户
        Args:
            name (str): 用户名
        Returns: UserDTO
            UserDTO
        """
        logger.info(
            '调用用户登录',
            extra={
                'user_name': name
            }
        )
        start_time = time.perf_counter()

        user = self.uow.user_repo.find_by_name(name=name)
        if user is None:
            user = User.create(name=name)
            with self.uow:
                self.uow.user_repo.save(user=user)

        logger.info(
            '用户登录成功',
            extra={
                'user_id': user.id,
                'user_name': name,
                'duration_ms': get_time_duration(start_time=start_time)
            }
        )
        
        return UserDTO.from_user(user=user)

    def deregister(self, user_id: UserId) -> None:
        """
        注销用户
        Args:
            user_id (UserId): 用户 id 
        """
        logger.info(
            '调用用户注销',
            extra={
                'user_id': user_id
            }
        )
        start_time = time.perf_counter()

        with self.uow:
            self.uow.user_repo.delete_by_id(id=user_id)

        logger.info(
            '用户注销成功',
            extra={
                'user_id': user_id,
                'duration_ms': get_time_duration(start_time=start_time)
            }
        )
