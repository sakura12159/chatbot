from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

class APIModel(BaseModel):
    """ 通用配置 """
    model_config = ConfigDict(
        alias_generator=to_camel,  # camel 与 snake 命名法互转
        populate_by_name=True,
    )

class RequestModel(APIModel):
    """ 前端 -> 后端 """
    # model_config = ConfigDict(
    #     extra='forbid'
    # )

class ResponseModel(APIModel):
    """ 后端 -> 前端 """
    model_config = ConfigDict(
        from_attributes=True
    )
