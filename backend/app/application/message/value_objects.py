from enum import Enum

class ChatMessageDTOType(Enum):
    """ 聊天消息类型 """
    IGNORED = 'ignored'

    TEXT = 'text'
    MARKDOWN = 'markdown'
    THINKING = 'thinking'
    TOOL_CALL = 'tool_call'
