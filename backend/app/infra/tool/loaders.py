import time
import logging
from pathlib import Path

from app.domain.tool.registries import ToolRegistry
from app.infra.tool.builtin_tools import builtin_tools
from app.infra.external.tool.clients import SandBoxClient, RagClient
from shared.utils import get_time_duration, get_root_directory
from shared.config import RAG_DOCUMENT_PATH

logger = logging.getLogger(__name__)

class ToolBuiltinLoader:
    """
    内置工具注册类
    负责内置工具的注册
    """

    @staticmethod
    def init_external_dependencies() -> None:
        """ 初始化外部依赖 """
        SandBoxClient.build_template()  # 创建沙盒模板

    @staticmethod
    def load(registry: ToolRegistry) -> None:
        """
        加载并注册内置的工具
        Args:
            registry (ToolRegistry): 工具注册类
        """
        logger.info(
            '注册内置工具'
        )
        start_time = time.perf_counter()

        for tool in builtin_tools:
            registry.register_tool(tool=tool)

        logger.info(
            '注册内置工具成功',
            extra={
                'duration_ms': get_time_duration(start_time=start_time)
            }
        )

class RagDocumentLoader:
    """
    rag 文档类
    负责文档切分与入库
    """

    @staticmethod
    def init() -> None:
        logger.info(
            '开始读取 rag 文档并切分入库'
        )
        start_time = time.perf_counter()

        file_count = 0
        txt_files = (get_root_directory() / RAG_DOCUMENT_PATH).glob('*.txt')
        for file in txt_files:
            file_count += 1
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
                RagClient.ingest(name=file.stem, content=content, source_url=str(file.resolve()))
            break

        logger.info(
            '读取 rag 文档并切分入库成功',
            extra={
                'file_count': file_count,
                'duration_ms': get_time_duration(start_time=start_time)
            }
        )
