from sqlalchemy.orm import Session as ORMSession
from fastapi import Depends, Request

from app.domain.tool.registries import ToolRegistry
from app.domain.tool.executors import ToolExecutor
from app.application.prompt.loaders import PromptLoader
from app.application.common.unit_of_work import UnitOfWork
from app.application.llm.ports import LLMClient, TextSummarizer
from app.application.user.services import UserService
from app.application.session.queries import SessionQuery
from app.application.session.services import SessionService
from app.application.chat.services import ChatService, BalanceService
from app.infra.persistence.database import get_orm_session
from app.infra.persistence.unif_of_work import UnitOfWork as UnitOfWorkImpl
from app.infra.persistence.queries.session_queries import SessionQueryImpl

# ========== 从 app.state 中获取的单例 ==========
def get_tool_registry(req: Request) -> ToolRegistry:
    """ 工具注册依赖 """
    return req.app.state.tool_registry

def get_tool_executor(req: Request) -> ToolExecutor:
    """ 工具执行依赖 """
    return req.app.state.tool_executor

def get_prompt_loader(req: Request) -> PromptLoader:
    """ 提示词加载器依赖 """
    return req.app.state.prompt_loader

def get_text_summarizer(req: Request) -> TextSummarizer:
    """ 文本总结依赖 """
    return req.app.state.text_summarizer

def get_llm_client(req: Request) -> LLMClient:
    """ 模型客户端依赖 """
    return req.app.state.llm_client

def get_balance_service(req: Request) -> BalanceService:
    """ 账户服务依赖 """
    return req.app.state.balance_service

# ========== 每次请求重新创建 ==========
def get_uow(orm_session: ORMSession = Depends(get_orm_session)) -> UnitOfWork:
    """ 事务工作单元依赖 """
    return UnitOfWorkImpl(orm_session=orm_session)

def get_user_service(uow: UnitOfWork = Depends(get_uow)) -> UserService:
    """ 用户服务依赖 """
    return UserService(uow=uow)

def get_session_query(orm_session: ORMSession = Depends(get_orm_session)) -> SessionQuery:
    """ 会话查询依赖 """
    return SessionQueryImpl(orm_session=orm_session)

def get_session_service(
    uow: UnitOfWork = Depends(get_uow), 
    session_query: SessionQuery = Depends(get_session_query)
) -> SessionService:
    """ 会话服务依赖 """
    return SessionService(
        uow=uow,
        session_query=session_query
    )

def get_chat_service(
    uow: UnitOfWork = Depends(get_uow),
    llm_client: LLMClient = Depends(get_llm_client),
    text_summarizer: TextSummarizer = Depends(get_text_summarizer),
    prompt_loader: PromptLoader = Depends(get_prompt_loader),
    tool_registry: ToolRegistry = Depends(get_tool_registry),
    tool_executor: ToolExecutor = Depends(get_tool_executor)
) -> ChatService:
    """ 聊天服务依赖 """
    return ChatService(
        uow=uow,
        llm_client=llm_client,
        text_summarizer=text_summarizer,
        prompt_loader=prompt_loader,
        tool_registry=tool_registry,
        tool_executor=tool_executor
    )
