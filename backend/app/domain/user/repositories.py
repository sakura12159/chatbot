from typing import Protocol

from app.domain.user.value_objects import UserId
from app.domain.user.entities import User

class UserRepository(Protocol):
    """
    用户表操作类
    负责查找、删除和保存新建或修改的用户
    """

    def find_by_id(self, id: UserId) -> User | None:
        """
        通过用户 id 查找用户
        Args:
            name (UserId): 用户 id
        Returns: User | None
            用户实体，未找到返回 None
        """
        ...

    def find_by_name(self, name: str) -> User | None:
        """
        通过用户名查找用户
        Args:
            name (UserId): 用户名
        Returns: User | None
            用户实体，未找到返回 None
        """
        ...

    def delete_by_id(self, id: UserId) -> None:
        """
        通过用户 id 删除用户
        Args:
            name (UserId): 用户 id
        """
        ...

    def save(self, user: User) -> None:
        """
        保存用户及更新内容
        Args:
            user (User): 用户实体
        """
        ...
