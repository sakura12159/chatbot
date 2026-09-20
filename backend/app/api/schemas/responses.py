import uuid

from datetime import datetime

from app.api.schemas.base import ResponseModel
from app.api.schemas.value_objects import ChatSessionInfo, ChatMessageInfo

class UserSignInResponse(ResponseModel):
    id: uuid.UUID           # 用户 id
    name: str               # 用户名
    created_at: datetime    # 创建时间

class CreateSessionResponse(ResponseModel):
    id: uuid.UUID                   # 会话 id
    user_id: uuid.UUID              # 用户 id
    title: str                      # 会话标题
    total_tokens: int               # 会话消耗 token 数
    created_at: datetime            # 创建时间
    messages: list[ChatMessageInfo] # 消息

class GetSessionResponse(ResponseModel):
    id: uuid.UUID                       # 会话 id
    user_id: uuid.UUID                  # 用户 id
    title: str                          # 会话标题
    total_tokens: int                   # 会话消耗 token 数
    created_at: datetime                # 创建时间
    messages: list[ChatMessageInfo]     # 消息

class ListSessionsResponse(ResponseModel):
    user_id: uuid.UUID
    sessions: list[ChatSessionInfo]  # 会话信息对象

class InquireBalanceResponse(ResponseModel):
    is_available: bool  # 账户是否可用
    currency: str       # 余额货币类型
    total_balance: str  # 余额数值

class ChatResponseChunk(ResponseModel):
    session_id: uuid.UUID           # 会话 id
    type: str                       # 响应块类型
    content: str | None             # 响应内容
    reasoning_content: str | None   # 响应推理内容
    reasoning_time: float | None    # 推理时间
    done: bool                      # 响应是否完成
