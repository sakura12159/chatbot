import time
import logging

from sqlalchemy import select
from sqlalchemy.orm import Session as ORMSession
from sqlalchemy.exc import IntegrityError

from app.domain.common.exceptions import UserNotFoundError, UserAlreadyExistsError
from app.domain.user.value_objects import UserId
from app.domain.user.entities import User
from app.infra.common.exceptions import PersistenceError
from app.infra.persistence.models.user_model import UserModel
from shared.utils import get_time_duration

logger = logging.getLogger()

class UserRepository:
    """
    用户表操作类
    负责查找、删除和保存新建或修改的用户
    """
    
    def __init__(self, orm_session: ORMSession) -> None:
        self.orm_session = orm_session

    def _to_model(self, domain: User) -> UserModel:
        """
        将 User 转为 UserModel
        Args:
            domain (User): 用户实体
        Returns: UserModel
            orm UserModel
        """
        return UserModel(
            id=domain.id,
            name=domain.name,
            created_at=domain.created_at
        )

    def _to_domain(self, model: UserModel) -> User:
        """
        将 UserModel 转为 domain User
        Args:
            model (UserModel): 用户模型
        Returns: User
            用户实体
        """
        return User(
            id=model.id,
            name=model.name,
            created_at=model.created_at
        )

    def find_by_id(self, id: UserId) -> User | None:
        """
        通过用户 id 查找用户
        Args:
            name (UserId): 用户 id
        Returns: User | None
            用户实体，未找到返回 None
        """
        logging.debug(
            '查询用户',
            extra={
                'user_id': id
            }
        )
        start_time = time.perf_counter()

        try:
            model = self.orm_session.get(UserModel, id)
            if model:
                logging.debug(
                    '查询用户成功',
                    extra={
                        'user_id': id,
                        'duration_ms': get_time_duration(start_time=start_time)
                    }
                )

                return self._to_domain(model=model)
            
        except Exception as e:
            logging.exception(
                '查询用户失败',
                extra={
                    'user_id': id,
                    'duration_ms': get_time_duration(start_time=start_time)
                }
            )

            raise PersistenceError(f'数据库查询异常: {e}') from e

    def find_by_name(self, name: str) -> User | None:
        """
        通过用户名查找用户
        Args:
            name (UserId): 用户名
        Returns: User | None
            用户实体，未找到返回 None
        """
        logging.debug(
            '查询用户',
            extra={
                'user_name': name
            }
        )
        start_time = time.perf_counter()

        try:
            stmt = select(UserModel).where(UserModel.name == name)
            model = self.orm_session.execute(stmt).scalar_one_or_none()
            if model:
                logging.debug(
                    '查询用户成功',
                    extra={
                        'user_id': model.id,
                        'user_name': name,
                        'duration_ms': get_time_duration(start_time=start_time)
                    }
                )

                return self._to_domain(model=model)
            
        except Exception as e:
            logging.exception(
                '查询用户失败',
                extra={
                    'user_name': name,
                    'duration_ms': get_time_duration(start_time=start_time)
                }
            )
            
            raise PersistenceError(f'数据库查询异常: {e}') from e

    def delete_by_id(self, id: UserId) -> None:
        """
        通过用户 id 删除用户
        Args:
            name (UserId): 用户 id
        """
        logging.debug(
            '提交删除用户事务',
            extra={
                'user_id': id
            }
        )
        start_time = time.perf_counter()

        try:
            model = self.orm_session.get(UserModel, id)
            if not model:
                logging.exception(
                    '提交删除用户事务失败',
                    extra={
                        'user_id': id,
                        'duration_ms': get_time_duration(start_time=start_time)
                    }
                )

                raise UserNotFoundError(f'用户 id {id} 不存在')
            
            self.orm_session.delete(model)
            self.orm_session.flush()
            logging.debug(
                '提交删除用户事务成功',
                extra={
                    'user_id': id,
                    'user_name': model.name,
                    'duration_ms': get_time_duration(start_time=start_time)
                }
            )
            
        except Exception as e:
            logging.exception(
                '提交删除用户事务失败',
                extra={
                    'user_id': id,
                    'duration_ms': get_time_duration(start_time=start_time)
                }
            )

            raise PersistenceError(f'数据库删除异常: {e}') from e

    def save(self, user: User) -> None:
        """
        保存用户及更新内容
        Args:
            user (User): 用户实体
        """
        logging.debug(
            '提交保存用户事务',
            extra={
                'user_id': user.id,
                'user_name': user.name
            }
        )
        start_time = time.perf_counter()

        try:
            model = self._to_model(domain=user)
            self.orm_session.merge(model)
            self.orm_session.flush()
            logging.debug(
                '提交保存用户事务成功',
                extra={
                    'user_id': user.id,
                    'user_name': user.name,
                    'duration_ms': get_time_duration(start_time=start_time)
                }
            )

        except IntegrityError as e:
            logging.exception(
                '提交保存用户事务失败',
                extra={
                    'user_id': user.id,
                    'user_name': user.name,
                    'duration_ms': get_time_duration(start_time=start_time)
                }
            )

            raise UserAlreadyExistsError(f'用户 {user.name} 已存在')
        
        except Exception as e:
            logging.exception(
                '提交保存用户事务失败',
                extra={
                    'user_id': user.id,
                    'user_name': user.name,
                    'duration_ms': get_time_duration(start_time=start_time)
                }
            )
            
            raise PersistenceError(f'数据库插入失败: {e}') from e
