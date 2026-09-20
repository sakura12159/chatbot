from __future__ import annotations

import uuid
from sqlalchemy import String, ForeignKey, func, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP

from app.domain.common.value_objects import TimeStamp
from app.domain.user.value_objects import UserId
from app.domain.session.value_objects import ChatSessionId
from app.infra.persistence.database import Base

class ChatSessionModel(Base):
    __tablename__ = 'chat_sessions'

    # 主键
    id: Mapped[ChatSessionId] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    # 关联 users 表，ON DELETE CASCADE
    user_id: Mapped[UserId] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False
    )
    
    # 会话标题，默认值 New Session
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    
    # 时间戳
    created_at: Mapped[TimeStamp] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    
    # 更新时间，默认 now()，且每次更新时自动刷新
    updated_at: Mapped[TimeStamp] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()  # 更新时自动设置此值
    )

    # 历史压缩得到的会话历史总结
    summary: Mapped[str] = mapped_column(
        Text(),
        nullable=False
    )

    # 总消耗 token 数量
    total_tokens: Mapped[int] = mapped_column(
        Integer(),
        nullable=False
    )

    # 绑定其他表
    user: Mapped['UserModel'] = relationship(  # type: ignore
        'UserModel',
        back_populates='sessions'
    )
    
    messages: Mapped[list['ChatMessageModel']] = relationship(  # type: ignore
        'ChatMessageModel',
        back_populates='session',
        cascade='all, delete-orphan',   # 子对象不在父对象列表中自动删除
        passive_deletes=True            # 父对象删除时让数据库处理级联删除
    )
