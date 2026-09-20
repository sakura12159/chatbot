from dataclasses import asdict, is_dataclass
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from dacite import from_dict
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import TypeDecorator

from shared.config import DACITE_CONFIG

class ListOfType(TypeDecorator):
    impl = JSONB
    cache_ok = True

    def __init__(self, element_type: Any, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.element_type = element_type

    def _to_jsonable(self, value: Any) -> Any:
        """把 asdict 输出中的 UUID/datetime/Enum 转成 JSON 兼容类型"""
        if isinstance(value, dict):
            return {k: self._to_jsonable(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self._to_jsonable(v) for v in value]
        if isinstance(value, UUID):
            return str(value)
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, Enum):
            return value.value
        return value

    def _serialize(self, item: Any) -> dict:
        if is_dataclass(item):
            return self._to_jsonable(asdict(item))  # type: ignore
        raise TypeError(f'Unsupported type: {type(item)}')

    def _deserialize(self, data: dict) -> Any:
        if is_dataclass(self.element_type):
            return from_dict(self.element_type, data, config=DACITE_CONFIG)  # type: ignore
        raise TypeError(f'Unsupported element type: {self.element_type}')

    def process_bind_param(self, value: Any | None, dialect) -> Any:
        if value is None:
            return None
        return [self._serialize(item) for item in value]

    def process_result_value(self, value, dialect) -> Any:
        if value is None:
            return None
        return [self._deserialize(item) for item in value]
