import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.domain.common.exceptions import (
    DomainError,
    UserNotFoundError,
    UserAlreadyExistsError,
    SessionNotFoundError,
    ToolNotFoundError,
    ToolAlreadyExistsError,
    TooManyToolCallsError,
    ToolCallFailsError,
    ToolCreationFailsError
)
from app.application.common.exceptions import (
    ApplicationError,
    LLMError,
    PromptLoadingFailsError,
    UnexpectedFinishReasonError
)
from app.infra.common.exceptions import (
    InfrastructureError,
    PersistenceError,
    ExternalError,
    HttpClientError,
)

logger = logging.getLogger(__name__)

def register_exception_handlers(app: FastAPI) -> None:
    """ 注册所有全局异常处理器 """

    # ========== Domain 异常 ==========
    @app.exception_handler(UserNotFoundError)
    @app.exception_handler(SessionNotFoundError)
    @app.exception_handler(ToolNotFoundError)
    async def not_found_handler(request: Request, exc: DomainError):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={'code': exc.code, 'message': exc.message},
        )

    @app.exception_handler(UserAlreadyExistsError)
    @app.exception_handler(ToolAlreadyExistsError)
    async def conflict_handler(request: Request, exc: DomainError):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={'code': exc.code, 'message': exc.message},
        )

    @app.exception_handler(TooManyToolCallsError)
    async def too_many_tool_calls_handler(request: Request, exc: TooManyToolCallsError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={'code': exc.code, 'message': exc.message},
        )

    @app.exception_handler(ToolCallFailsError)
    @app.exception_handler(ToolCreationFailsError)
    async def tool_internal_error_handler(request: Request, exc: DomainError):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={'code': exc.code, 'message': exc.message}
        )

    # ========== Application 异常 ==========
    @app.exception_handler(PromptLoadingFailsError)
    @app.exception_handler(UnexpectedFinishReasonError)
    async def llm_internal_error_handler(request: Request, exc: LLMError):
        logger.error(f'LLM error: {exc}', exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={'code': exc.code, 'message': exc.message},
        )

    # ========== Infrastructure 异常 ==========
    @app.exception_handler(PersistenceError)
    async def persistence_handler(request: Request, exc: PersistenceError):
        logger.error(f'Persistence error: {exc}', exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={'code': exc.code, 'message': '数据库操作失败，请稍后重试'},
        )

    @app.exception_handler(ExternalError)
    @app.exception_handler(HttpClientError)
    async def external_handler(request: Request, exc: ExternalError):
        logger.error(f'External error: {exc}', exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={'code': exc.code, 'message': '外部服务暂时不可用'},
        )

    # ========== FastAPI 内置校验异常 ==========
    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                'code': 422,
                'message': '请求参数校验失败',
                'errors': exc.errors(),
            },
        )

    # ========== 通用兜底 ==========
    @app.exception_handler(Exception)
    async def generic_handler(request: Request, exc: Exception):
        logger.exception(f'未知错误: {exc}')
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={'code': 500, 'message': '未知的内部服务器错误'},
        )
