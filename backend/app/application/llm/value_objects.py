from enum import Enum

class LLMFinishReasonType(Enum):
    """ 模型停止原因类型 """
    STOP = 'stop'
    LENGTH = 'length'
    CONTENT_FILTER = 'content_filter'
    TOOL_CALLS = 'tool_calls'
    INSUFFICIENT_SYSTEM_RESOURCE = 'insufficient_system_resource'
