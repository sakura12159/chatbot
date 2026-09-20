import uuid
from fastapi import APIRouter, Depends

from app.domain.user.value_objects import UserId
from app.domain.session.value_objects import ChatSessionId
from app.api.schemas.value_objects import ChatMessageInfo
from app.api.schemas.requests import CreateSessionRequest, DeleteSessionRequest
from app.api.schemas.responses import CreateSessionResponse, GetSessionResponse
from app.api.dependencies import get_session_service
from app.application.session.services import SessionService

router = APIRouter(
    prefix='/sessions',
    tags=['sessions']
)

@router.post(path='', response_model=CreateSessionResponse)
def create_session(
    req: CreateSessionRequest,
    service: SessionService = Depends(get_session_service)
) -> CreateSessionResponse:
    """ 创建会话 """
    dto = service.create_session(user_id=UserId(req.user_id))
    return CreateSessionResponse(
        id=dto.id,
        user_id=dto.user_id,
        title=dto.title,
        total_tokens=dto.total_tokens,
        created_at=dto.created_at,
        messages=[
            ChatMessageInfo(
                id=message.id,
                session_id=message.session_id,
                type=message.type.value,
                role=message.role.value,
                content=message.content,
                created_at=message.created_at,
                reasoning_content=message.reasoning_content,
                reasoning_time=message.reasoning_time,
                is_compressed=message.is_compressed
            ) for message in dto.messages
        ]
    )

@router.get(path='/{session_id}', response_model=GetSessionResponse)
def get_session(
    session_id: str,
    service: SessionService = Depends(get_session_service)
) -> GetSessionResponse:
    """ 加载会话 """
    dto = service.get_session(session_id=ChatSessionId(uuid.UUID(session_id)))
    return GetSessionResponse(
        id=dto.id,
        user_id=dto.user_id,
        title=dto.title,
        total_tokens=dto.total_tokens,
        created_at=dto.created_at,
        messages=[
            ChatMessageInfo(
                id=message.id,
                session_id=message.session_id,
                type=message.type.value,
                role=message.role.value,
                content=message.content,
                created_at=message.created_at,
                reasoning_content=message.reasoning_content,
                reasoning_time=message.reasoning_time,
                is_compressed=message.is_compressed
            ) for message in dto.messages
        ]
    )

@router.delete(path='/{session_id}')
def delete_session(
    req: DeleteSessionRequest,
    service: SessionService = Depends(get_session_service)
) -> None:
    """ 删除会话 """
    service.delete_session(session_id=ChatSessionId(req.session_id))
