import uuid
from dataclasses import dataclass, field

from datetime import datetime, timezone

from app.domain.session.value_objects import ChatSessionId
from app.domain.common.value_objects import TimeStamp
from app.domain.user.value_objects import UserId
from app.domain.message.value_objects import ChatMessage, ChatMessageId, ChatMessageRole
from app.domain.tool.value_objects import ToolCall, ToolCallId

@dataclass
class ChatSession:
    """ 会话实体 """
    id: ChatSessionId
    user_id: UserId
    title: str
    created_at: TimeStamp
    summary: str = ''
    total_tokens: int = 0

    messages: list[ChatMessage] = field(default_factory=list)

    def is_new(self) -> bool:
        """ 当前会话是否为新会话 """
        return len(self.messages) == 0

    @staticmethod
    def create(user_id: UserId) -> 'ChatSession':
        """
        根据已有 user id 创建 ChatSession
        Args:
            user_id (UserId): 用户 id
        Returns: ChatSession
            创建的会话
        """
        return ChatSession(
            id=ChatSessionId(uuid.uuid4()),
            user_id=user_id,
            title='New Session',
            created_at=datetime.now(timezone.utc)
        )

    def create_chat_message(
        self, 
        role: ChatMessageRole, 
        content: str, 
        reasoning_content: str | None = None,
        reasoning_time: float | None = None,
        tool_calls: list[ToolCall] | None = None,
        tool_call_id: ToolCallId | None = None
    ) -> ChatMessage:
        """
        创建 ChatMessage
        Args:
            role (ChatMessageRole):             消息角色
            content (str):                      消息内容
            reasoning_content (str | None):     推理内容
            reasoning_time (float | None):      推理时间
            tool_calls (list[ToolCall] | None): 工具调用
            tool_call_id (ToolCallId | None):   工具调用 id
        Returns: ChatMessage
            创建的消息
        """        
        return ChatMessage(
            id=ChatMessageId(uuid.uuid4()),
            session_id=self.id,
            role=role,
            content=content,
            reasoning_content=reasoning_content,
            reasoning_time=reasoning_time,
            created_at=datetime.now(timezone.utc),
            tool_calls=tool_calls,
            tool_call_id=tool_call_id,
            is_compressed=False
        )

    def append_message(self, message: ChatMessage) -> None:
        """
        向 messages 列表中添加消息
        Args:
            message (ChatMessage): 要添加的消息
        """
        self.messages.append(message)

    def remove_last_turn_messages(self) -> None:
        """ 删除最后一轮对话消息 """
        start_idx = 0
        for i in range(len(self.messages) - 1, -1, -1):
            if self.messages[i].role == ChatMessageRole.USER:
                start_idx = i
                break

        self.messages = self.messages[:start_idx]            

    def set_title(self, title: str) -> None:
        """
        设置 title 字段
        Args:
            title (str): 新 title
        """
        self.title = title

    def set_summary(self, summary: str) -> None:
        """
        设置 summary 字段
        Args:
            summary (str): 新 summary
        """
        self.summary = summary

    def add_total_tokens(self, tokens: int) -> None:
        """
        累加总消耗 token 数
        Args:
            tokens (int): 消耗 token 数
        """
        self.total_tokens += tokens

    def apply_history_compression(self, messages: list[ChatMessage], summary: str) -> None:
        """
        进行历史压缩相关操作
        Args:
            messages (list[ChatMessage]):   需要标记为已压缩的消息列表
            summary (str):           新的会话历史总结
        """
        for message in messages:
            message.mark_as_compressed()
        self.set_summary(summary=summary)
