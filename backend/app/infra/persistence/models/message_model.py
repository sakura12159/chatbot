from __future__ import annotations

import uuid

from sqlalchemy import String, ForeignKey, func, Boolean, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP

from app.domain.common.value_objects import TimeStamp
from app.domain.message.value_objects import ChatMessageId
from app.domain.session.value_objects import ChatSessionId
from app.domain.tool.value_objects import ToolCall, ToolCallId
from app.infra.persistence.database import Base
from app.infra.persistence.models.decorators import ListOfType

class ChatMessageModel(Base):
    __tablename__ = 'chat_messages'

    # 主键
    id: Mapped[ChatMessageId] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    # 外键：关联 sessions 表
    session_id: Mapped[ChatSessionId] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('chat_sessions.id', ondelete='CASCADE'),
        nullable=False
    )
    
    # 消息角色
    role: Mapped[str] = mapped_column(
        String(15),  # 给个长度限制，便于索引
        nullable=False
    )
    
    # 消息内容
    content: Mapped[str] = mapped_column(
        String(),
        nullable=False
    )

    # 推理内容
    reasoning_content: Mapped[str | None] = mapped_column(
        String(),
        nullable=True,
        server_default=None
    )

    # 推理时间，单位 秒
    reasoning_time: Mapped[float | None] = mapped_column(
        Float(),
        nullable=True,
        server_default=None
    )

    # 创建时间
    created_at: Mapped[TimeStamp] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    # 工具调用
    tool_calls: Mapped[list[ToolCall] | None] = mapped_column(
        ListOfType(ToolCall),
        nullable=True,
        server_default=None
    )

    # 工具调用 id
    tool_call_id: Mapped[ToolCallId | None] = mapped_column(
        String(255),
        nullable=True,
        server_default=None
    ) 

    # 是否已进行过历史压缩
    is_compressed: Mapped[bool] = mapped_column(
        Boolean(),
        nullable=False,
        default=False
    )

    # 绑定其他表
    session: Mapped['ChatSessionModel'] = relationship(  # type: ignore
        'ChatSessionModel',
        back_populates='messages'
    )
