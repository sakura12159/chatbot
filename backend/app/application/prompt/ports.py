from typing import Protocol

from app.domain.llm.value_objects import LLMMessage

class PromptLoader(Protocol):
    """
    提示词仓库
    负责加载提示词
    """
    def load_chat_prompt(self, summary: str) -> list[LLMMessage]:
        """
        加载系统提示词
        Args:
            summary (str): 会话历史
        Returns: list[LLMMessage]
            包含提示词信息的列表
        """
        ...

    def load_session_title_summarization_prompt(self, query: str) -> list[LLMMessage]:
        """
        加载会话总结提示词
        Args:
            query (str): 用户输入
        Returns: list[LLMMessage]
            包含提示词信息的列表
        """
        ...

    def load_session_history_compression_prompt(
        self, 
        conversation_text: str,
        previous_summary: str
    ) -> list[LLMMessage]:
        """
        加载会话历史压缩提示词
        Args:
            conversation_text (str):  当前会话文本
            previous_summary (str): 旧的总结
        Returns: list[LLMMessage]
            包含提示词信息的列表
        """
        ...
