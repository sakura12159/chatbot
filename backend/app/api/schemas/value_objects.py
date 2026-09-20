import uuid

from datetime import datetime

from app.api.schemas.base import ResponseModel

class ChatSessionInfo(ResponseModel):
    id: uuid.UUID       # 会话 id
    title: str          # 会话标题
    total_tokens: int   # 消耗的总 token 数

class ChatMessageInfo(ResponseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    type: str
    role: str
    content: str
    created_at: datetime
    reasoning_content: str | None
    reasoning_time: float | None
    is_compressed: bool
