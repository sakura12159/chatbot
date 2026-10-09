import uuid
from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP

from app.domain.common.value_objects import TimeStamp
from app.infra.tool.rag.types import SourceDocumentId
from app.infra.tool.rag.vector_database import Base

class SourceDocument(Base):
    __tablename__ = 'source_documents'

    # 主键
    id: Mapped[SourceDocumentId] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # 文档名
    name: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    # 文档链接
    source_url: Mapped[str | None] = mapped_column(
        String
    )

    # 创建时间
    created_at: Mapped[TimeStamp] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    # 正向关系：多个分块
    chunks: Mapped[list['DocumentChunk']] = relationship(  # type: ignore
        back_populates='document',
        cascade='all, delete-orphan'
    )
