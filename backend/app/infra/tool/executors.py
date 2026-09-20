import time
import logging

from app.domain.tool.value_objects import ToolCall, ToolMessage
from app.domain.common.exceptions import ToolCallFailsError
from app.domain.tool.registries import ToolRegistry
from shared.utils import get_time_duration

logger = logging.getLogger(__name__)

class ToolExecutor:
    """
    工具执行类
    负责根据工具调用信息执行工具，返回工具执行信息
    """

    def __init__(self, registry: ToolRegistry) -> None:
        self.registry = registry

    def execute(self, tool_call: ToolCall) -> ToolMessage:
        """
        执行工具，返回结果
        Args:
            tool_call (ToolCall): 工具调用
        Returns: ToolMessage
            工具执行结果信息
        """
        name = tool_call.name
        func = self.registry.get_tool_by_name(name=name).function
        arguments = tool_call.arguments

        logger.info(
            '调用工具',
            extra={
                'tool_name': name,
                'arguments': arguments
            }
        )
        start_time = time.perf_counter()

        try:
            result = func(**arguments)
            logger.info(
                '调用工具成功',
                extra={
                    'tool_name': name,
                    'arguments': arguments,
                    'duration_ms': get_time_duration(start_time=start_time),
                    'success': result.success,
                    'error_message': result.error_message
                }
            )

            return ToolMessage.from_tool_call_and_result(tool_call=tool_call, result=result)
        
        except Exception as e:
            logger.exception(
                '调用工具失败',
                extra={
                    'tool_name': name,
                    'arguments': arguments,
                    'duration_ms': get_time_duration(start_time=start_time)
                }
            )

            raise ToolCallFailsError(f'调用工具 {name} 失败: {e}') from e
