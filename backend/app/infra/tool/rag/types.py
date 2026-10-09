import uuid
from typing import NewType
from dataclasses import dataclass

SourceDocumentId = NewType('SourceDocumentId', uuid.UUID)
DocumentChunkId = NewType('DocumentChunkId', uuid.UUID)

@dataclass
class RetrievedChunk:
    id: DocumentChunkId
    document_id: SourceDocumentId
    content: str

@dataclass
class RerankedChunk:
    content: str
    score: float
