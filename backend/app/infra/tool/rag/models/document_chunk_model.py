import uuid
from sqlalchemy import ForeignKey, func, Integer, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from pgvector.sqlalchemy import Vector

from app.domain.common.value_objects import TimeStamp
from app.infra.tool.rag.types import SourceDocumentId, DocumentChunkId
from app.infra.tool.rag.vector_database import Base
from shared.config import RAG_EMBEDDING_DIM, RAG_RETRIVE_HNSW_M, RAG_RETRIVE_HNSW_EF_CONSTRUCTION

class DocumentChunk(Base):
    __tablename__ = 'document_chunks'

    # 主键
    id: Mapped[DocumentChunkId] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # 源文档 id
    document_id: Mapped[SourceDocumentId] = mapped_column(
        ForeignKey('source_documents.id', ondelete='CASCADE'),
        nullable=False
    )

    # 分块索引
    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    # 内容
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    # 编码
    embedding: Mapped[list[float]] = mapped_column(
        Vector(RAG_EMBEDDING_DIM),
        nullable=False
    )

    # 创建时间
    created_at: Mapped[TimeStamp] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    # 反向关系：源文档
    document: Mapped['SourceDocument'] = relationship(back_populates='chunks')  # type: ignore

    # 余弦距离 HNSW 索引
    __table_args__ = (
        Index(
            'idx_embedding_hnsw',
            'embedding',
            postgresql_using='hnsw',
            postgresql_with={'m': RAG_RETRIVE_HNSW_M, 'ef_construction': RAG_RETRIVE_HNSW_EF_CONSTRUCTION},
            postgresql_ops={'embedding': 'vector_cosine_ops'},
        ),
    )
