from dataclasses import dataclass

from app.domain.common.value_objects import TimeStamp
from app.domain.user.value_objects import UserId
from app.domain.user.entities import User

@dataclass
class UserDTO:
    """ 用户 dto """
    id: UserId
    name: str
    created_at: TimeStamp

    @staticmethod
    def from_user(user: User) -> 'UserDTO':
        """
        从用户实体创建 UserDTO
        Args:
            user (User): 用户实体
        Returns: UserDTO
            UserDTO
        """
        return UserDTO(
            id=user.id,
            name=user.name,
            created_at=user.created_at
        )
