import uuid
from fastapi import APIRouter, Depends

from app.domain.user.value_objects import UserId
from app.application.user.services import UserService
from app.application.session.services import SessionService
from app.application.chat.services import BalanceService
from app.api.schemas.requests import UserSignInRequest, UserDeregisterRequest
from app.api.schemas.responses import UserSignInResponse, ChatSessionInfo, ListSessionsResponse, InquireBalanceResponse
from app.api.dependencies import get_user_service, get_session_service, get_balance_service

router = APIRouter(
    prefix='/users',
    tags=['users']
)

@router.post(path='', response_model=UserSignInResponse)
def sign_in(
    req: UserSignInRequest, 
    service: UserService = Depends(get_user_service)
) -> UserSignInResponse:
    """ 用户登录 """
    dto = service.sign_in(name=req.name)
    return UserSignInResponse(
        id=dto.id,
        name=dto.name,
        created_at=dto.created_at
    )

@router.delete(path='/{user_id}')
def deregister(
    req: UserDeregisterRequest,
    service: UserService = Depends(get_user_service)
) -> None:
    """ 删除用户 """
    service.deregister(user_id=UserId(req.user_id))

@router.get(path='/{user_id}/sessions', response_model=ListSessionsResponse)
def list_sessions(
    user_id: str,
    service: SessionService = Depends(get_session_service)
) -> ListSessionsResponse:
    """ 获取用户会话信息 """
    dto_ls = service.list_sessions(user_id=UserId(uuid.UUID(user_id)))
    return ListSessionsResponse(
        user_id=uuid.UUID(user_id),
        sessions=[
            ChatSessionInfo(
                id=session.id,
                title=session.title,
                total_tokens=session.total_tokens
            ) for session in dto_ls
        ]
    )

@router.get(path='/{user_id}/balance', response_model=InquireBalanceResponse)
def inquire_balance(
    user_id: str,
    service: BalanceService = Depends(get_balance_service)
) -> InquireBalanceResponse:
    dto = service.inquire_balance()
    return InquireBalanceResponse(
        is_available=dto.is_available,
        currency=dto.currency,
        total_balance=dto.total_balance
    )
