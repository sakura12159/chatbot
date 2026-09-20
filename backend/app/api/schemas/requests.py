import uuid

from app.api.schemas.base import RequestModel

class UserSignInRequest(RequestModel):
    name: str  # 用户名

class UserDeregisterRequest(RequestModel):
    user_id: uuid.UUID  # 用户 id

class CreateSessionRequest(RequestModel):
    user_id: uuid.UUID  # 用户 id

class DeleteSessionRequest(RequestModel):
    session_id: uuid.UUID  # 会话 id

class ChatRequest(RequestModel):
    session_id: uuid.UUID
    query: str
    thinking: bool
    web: bool
    regenerate: bool
