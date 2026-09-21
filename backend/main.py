from contextlib import asynccontextmanager

from fastapi import FastAPI, APIRouter

from app.infra.external.llm.clients import LLMClient, TextSummarizer
from app.infra.prompt.loaders import PromptLoader
from app.infra.tool.registries import ToolRegistry
from app.infra.tool.executors import ToolExecutor
from app.infra.tool.loaders import ToolBuiltinLoader
from app.infra.persistence.database import init_database
from app.application.chat.services import BalanceService
from app.api.middlewares import add_middlewares
from app.api.routers import user_router, session_router, chat_router
from app.api.exception_handlers import register_exception_handlers
from shared.logging import init_logging

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 配置记录文件设置
    init_logging()

    # 初始化数据库
    # init_database(by_force=True)

    # 初始化内置工具所需要的外部依赖
    # ToolBuiltinLoader.init_external_dependencies()

    # 创建单例，存入 app.state
    tool_registry = ToolRegistry()
    ToolBuiltinLoader.load(registry=tool_registry)

    app.state.tool_registry = tool_registry
    app.state.tool_executor = ToolExecutor(registry=tool_registry)
    app.state.prompt_loader = PromptLoader()
    app.state.llm_client = LLMClient()
    app.state.text_summarizer = TextSummarizer(
        llm_client=app.state.llm_client,
        prompt_loader=app.state.prompt_loader
    )
    app.state.balance_service = BalanceService(
        llm_client=app.state.llm_client
    )
    
    yield

    app.state.llm_client.close()

# 创建实例
app = FastAPI(
    title='Chatbot API',
    version='1.0',
    description='A chatbot backend based on deepseek llm model api',
    lifespan=lifespan
)

# 添加中间件
add_middlewares(app=app)

# 添加异常处理
register_exception_handlers(app=app)

# 路由挂载
router_v1 = APIRouter(prefix='/api/v1')
for router in (user_router.router, session_router.router, chat_router.router):
    router_v1.include_router(router)
app.include_router(router_v1)
