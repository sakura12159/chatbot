import logging

from app.domain.tool.entities import Tool
from app.domain.common.exceptions import ToolNotFoundError, ToolAlreadyExistsError
from app.infra.tool.builtin_tools import web_tools

logger = logging.getLogger(__name__)

class ToolRegistry:
    """
    工具注册类
    负责注册、注销、查找、更改工具状态以及返回已注册的工具
    """

    def __init__(self) -> None:
        self.tools_mapping: dict[str, Tool] = {}
        self.web_tools: list[Tool] = web_tools

    def list_tools(self, include_disabled: bool = False) -> list[Tool]:
        """
        返回所有已注册的工具
        Args:
            include_disabled (bool): 结果中是否包含已被禁用的工具
        Returns: list[Tool]
            工具实体列表
        """
        return [tool for tool in self.tools_mapping.values()] if include_disabled \
                else [tool for tool in self.tools_mapping.values() if tool.is_enabled]

    def get_tool_by_name(self, name: str) -> Tool:
        """
        通过工具名获取工具
        Args:
            name (str): 工具名
        Returns: Tool
            工具实体
        """
        logger.info(
            '查询工具',
            extra={
                'tool_name': name
            }
        )

        tool = self.find_tool_by_name(name=name)
        if not tool:
            logger.exception(
                '查询工具失败',
                extra={
                    'tool_name': name
                }
            )

            raise ToolNotFoundError(f'获取工具 {name} 失败: 该工具未注册')

        logger.exception(
            '查询工具成功',
            extra={
                'tool_name': name
            }
        )

        return tool

    def find_tool_by_name(self, name: str) -> Tool | None:
        """
        通过工具名查找工具
        Args:
            name (str): 工具名
        Returns: Tool | None
            工具实体，未注册则返回 None
        """
        return self.tools_mapping.get(name)

    def set_web_tools_status(self, enabled: bool) -> None:
        """
        根据状态设置内置网络搜索工具的可使用性
        Args:
            enabled (bool): 是否可使用
        """
        logger.info(
            '设置内置网络搜索工具状态',
            extra={
                'enabled': enabled
            }
        )

        func = self.enable_tool if enabled else self.disable_tool
        for tool in self.web_tools:
            func(tool=tool)

        logger.info(
            '设置内置网络搜索工具状态成功',
            extra={
                'enabled': enabled
            }
        )

    def enable_tool(self, tool: Tool) -> None:
        """
        激活工具
        Args:
            tool (Tool): 工具实体
        """
        logger.debug(
            '启用工具',
            extra={
                'tool_name': tool.name
            }
        )

        tool = self.get_tool_by_name(name=tool.name)
        tool.enable()

        logger.debug(
            '启用工具成功',
            extra={
                'tool_name': tool.name
            }
        )

    def disable_tool(self, tool: Tool) -> None:
        """
        禁用工具
        Args:
            tool (Tool): 工具实体
        """
        logger.debug(
            '禁用工具',
            extra={
                'tool_name': tool.name
            }
        )

        tool = self.get_tool_by_name(name=tool.name)
        tool.disable()

        logger.debug(
            '禁用工具成功',
            extra={
                'tool_name': tool.name
            }
        )

    def register_tool(self, tool: Tool) -> None:
        """
        注册工具，提取 tool_function 的 schema，组合为 Tool，将[函数名: Tool]作为键值对添加到 tools_mapping 中
        Args:
            tool (Tool): 工具实体
        """
        logger.debug(
            '注册工具',
            extra={
                'tool_name': tool.name
            }
        )

        if self.find_tool_by_name(name=tool.name) is not None:
            logger.exception(
                '注册工具失败',
                extra={
                    'tool_name': tool.name
                }
            )

            raise ToolAlreadyExistsError(f'工具 {tool.name} 已注册')
        
        self.tools_mapping[tool.name] = tool

        logger.debug(
            '注册工具成功',
            extra={
                'tool_name': tool.name
            }
        )

    def unregister_tool(self, tool: Tool) -> None:
        """
        注销工具
        Args:
            tool (Tool): 工具实体
        """
        logger.debug(
            '注销工具',
            extra={
                'tool_name': tool.name
            }
        )
        
        if self.find_tool_by_name(name=tool.name) is None:
            logger.exception(
                '注销工具失败',
                extra={
                    'tool_name': tool.name
                }
            )
            
            raise ToolNotFoundError(f'工具 {tool.name} 未注册')

        del self.tools_mapping[tool.name]

        logger.debug(
            '注销工具成功',
            extra={
                'tool_name': tool.name
            }
        )
