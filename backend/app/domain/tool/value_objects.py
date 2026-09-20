from typing import Callable, Any, NewType
from dataclasses import dataclass

ToolCallId = NewType('ToolCallId', str)
type ToolFunction = Callable[..., ToolCallResult]
type ToolSchema = dict[str, Any]

@dataclass(frozen=True)
class ToolCallChunk:
    """ 流式传输时 tool call 信息 """
    index: int
    id: ToolCallId | None
    name: str | None
    arguments: str | None

@dataclass(frozen=True)
class ToolCall:
    """ 完整 tool call 信息 """
    index: int | None
    id: ToolCallId
    name: str
    arguments: dict[str, Any]

@dataclass(frozen=True)
class ToolCallResult:
    """ 工具调用结果 """
    success: bool
    data: dict[str, Any] | None
    error_message: str | None

@dataclass(frozen=True)
class ToolMessage:
    """ 工具调用汇总信息 """
    id: ToolCallId
    tool_call: ToolCall
    result: dict[str, Any]

    @staticmethod
    def from_tool_call_and_result(tool_call: ToolCall, result: ToolCallResult) -> 'ToolMessage':
        """
        从 ToolCall 和 ToolCallResult 生成 ToolMessage
        Args:
            tool_call (ToolCall):    工具调用
            result (ToolCallResult): 工具调用结果
        Returns: ToolMessage
            工具调用信息
        """
        if result.success:
            return ToolMessage(
                id=tool_call.id,
                tool_call=tool_call,
                result=result.data or {}
            )
        return ToolMessage(
            id=tool_call.id,
            tool_call=tool_call,
            result={'reason': result.error_message}
        )
