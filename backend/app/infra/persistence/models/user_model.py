from __future__ import annotations

import uuid
from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP

from app.domain.common.value_objects import TimeStamp
from app.domain.user.value_objects import UserId
from app.infra.persistence.database import Base

class UserModel(Base):
    __tablename__ = 'users'

    # 用户 id
    id: Mapped[UserId] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # 用户名
    name: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False
    )
    
    # 创建时间
    created_at: Mapped[TimeStamp] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    # 绑定其他表所需关键字
    sessions: Mapped[list['ChatSessionModel']] = relationship(  # type: ignore
        'ChatSessionModel',
        back_populates='user',
        passive_deletes=True  # 让数据库处理级联删除，ORM 不额外操作
    )
