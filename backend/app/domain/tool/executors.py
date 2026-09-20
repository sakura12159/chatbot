from typing import Protocol

from app.domain.tool.value_objects import ToolMessage, ToolCall

class ToolExecutor(Protocol):
    """
    工具执行类
    负责根据工具调用信息执行工具，返回工具执行信息
    """

    def execute(self, tool_call: ToolCall) -> ToolMessage:
        """
        执行工具，返回结果
        Args:
            tool_call (ToolCall): 工具调用
        Returns: ToolMessage
            工具执行结果信息
        """
        ...
