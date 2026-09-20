import uuid
from dataclasses import dataclass

from datetime import datetime, timezone

from app.domain.common.value_objects import TimeStamp
from app.domain.user.value_objects import UserId

@dataclass(frozen=True)
class User:
    """ 用户实体 """
    id: UserId
    name: str
    created_at: TimeStamp

    @staticmethod
    def create(name: str) -> 'User':
        """
        根据 name 创建 User 的静态方法
        Args:
            name (str): 用户名称
        Returns: User
            用户
        """
        return User(
            id=UserId(uuid.uuid4()),
            name=name,
            created_at=datetime.now(timezone.utc)
        )
