from typing import Protocol

from app.domain.tool.entities import Tool

class ToolRegistry(Protocol):
    """
    工具注册类
    负责注册、注销、查找、更改工具状态以及返回已注册的工具
    """
    web_tools: list[Tool]

    def list_tools(self, include_disabled: bool = False) -> list[Tool]:
        """
        返回所有已注册的工具
        Args:
            include_disabled (bool): 结果中是否包含已被禁用的工具
        Returns: list[Tool]
            工具实体列表
        """
        ...

    def get_tool_by_name(self, name: str) -> Tool:
        """
        通过工具名获取工具
        Args:
            name (str): 工具名
        Returns: Tool
            工具实体
        """
        ...

    def find_tool_by_name(self, name: str) -> Tool | None:
        """
        通过工具名查找工具
        Args:
            name (str): 工具名
        Returns: Tool | None
            工具实体，未注册则返回 None
        """
        ...

    def set_web_tools_status(self, enabled: bool) -> None:
        """
        根据状态设置内置网络搜索工具的可使用性
        Args:
            enabled (bool): 是否可使用
        """
        ...

    def enable_tool(self, tool: Tool) -> None:
        """
        激活工具
        Args:
            tool (Tool): 工具实体
        """
        ...

    def disable_tool(self, tool: Tool) -> None:
        """
        禁用工具
        Args:
            tool (Tool): 工具实体
        """
        ...

    def register_tool(self, tool: Tool) -> None:
        """
        注册工具，提取 tool_function 的 schema，组合为 Tool，将[函数名: Tool]作为键值对添加到 tools_mapping 中
        Args:
            tool (Tool): 工具实体
        """
        ...

    def unregister_tool(self, tool: Tool) -> None:
        """
        注销工具
        Args:
            tool (Tool): 工具实体
        """
        ...
