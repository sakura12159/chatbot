import time
import logging

from app.domain.tool.registries import ToolRegistry
from app.infra.tool.builtin_tools import builtin_tools
from app.infra.external.tool.clients import SandBoxClient
from shared.utils import get_time_duration

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
