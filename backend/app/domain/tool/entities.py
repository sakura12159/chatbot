
import inspect
from enum import Enum
from typing import get_origin, get_args, Literal, Union, Any, get_type_hints
from dataclasses import dataclass

from app.domain.tool.value_objects import ToolFunction, ToolSchema
from app.domain.common.exceptions import ToolCreationFailsError

@dataclass
class Tool:
    name: str
    function: ToolFunction
    schema: ToolSchema
    is_enabled: bool

    @staticmethod
    def _pytype_to_schema(t: type | None, add_null: bool = False) -> dict[str, Any]:
        """
        strict 模式下 python 类型转 json schema
        Args:
            t (type | None): python 类型或 pydantic model
            add_null (bool): strict 模式下在可选参数的 type 中添加 null
        Returns: dict[str, Any]
            该 type 对应的 json schema
        """
        origin = get_origin(t)  # 获取无下标类型，如 list[int] -> list
        args = get_args(t)  # 获取下标类型元组，如 list[int] -> (int,)

        # Union/Optional[T] -> Union
        if origin is Union:
            non_none = [a for a in args if a is not type(None)]

            # Optional[T]
            if len(non_none) == 1:
                return Tool._pytype_to_schema(non_none[0], add_null=True)

            # Union
            return {'anyOf': [Tool._pytype_to_schema(a) for a in args]}

        # list[T] / List[T] -> python3.9及以后 get_origin 均返回 list
        if origin is list:
            return {
                'type': 'array',
                'items': Tool._pytype_to_schema(args[0])
            }

        # dict[str, T] / Dict[str, T] -> python3.9及以后 get_origin 均返回 dict
        if origin is dict:
            return {
                'type': 'object',
                'additionalProperties': Tool._pytype_to_schema(args[1])
            }

        # Literal
        if origin is Literal:
            return {'enum': list(args)}
        
        # Enum
        if isinstance(t, type) and issubclass(t, Enum):
            return {
                'type': 'enum',
                'items': [x.value for x in t]
            }

        # 基础类型
        json_type = {
            int: 'integer',
            float: 'number',
            str: 'string',
            bool: 'boolean',
        }.get(t, 'string')  # 其他类型默认 string

        # strict：可选参数 type 中添加 null
        if add_null:
            return {
                'type': [json_type, 'null']
            }

        return {'type': json_type}

    @staticmethod
    def create(tool_function: ToolFunction, *tool_arg_descriptions: str) -> 'Tool':
        """
        创建工具，提取 tool_function 的 schema，组合为 Tool
        Args:
            tool_function (ToolFunction):   函数主体
            tool_arg_descriptions (str):    函数各参数的作用描述
        Retruns: Tool
            工具
        """
        try:
            sig = inspect.signature(tool_function)
            type_hints = get_type_hints(tool_function, include_extras=True)  # 包含可能存在的 Field 中的额外信息

            properties = {}
            required = []
            for (name, param), arg_description in zip(sig.parameters.items(), tool_arg_descriptions, strict=True):
                t = type_hints.get(name, str)  # 获取参数类型，默认为 str

                # py 类型转换
                properties[name] = Tool._pytype_to_schema(t, add_null=param.default is not inspect._empty)
                properties[name]['description'] = arg_description

                # strict：所有字段都 required
                required.append(name)

            schema = {
                'type': 'function',
                'function': {
                    'name': tool_function.__name__,
                    'description': tool_function.__doc__ or tool_function.__name__,
                    'strict': True,
                    'parameters': {
                        'type': 'object',
                        'properties': properties,
                        'required': required,
                        'additionalProperties': False
                    }
                }
            }
            return Tool(
                name=tool_function.__name__,
                function=tool_function,
                schema=schema,
                is_enabled=True
            )

        except Exception as e:
            raise ToolCreationFailsError(message=f'创建工具失败: {e}') from e

    def enable(self) -> None:
        """ 启用工具 """
        self.is_enabled = True

    def disable(self) -> None:
        """ 禁用工具 """
        self.is_enabled = False
