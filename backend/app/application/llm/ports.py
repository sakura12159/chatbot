from typing import Protocol, Iterator

from app.domain.message.value_objects import ChatMessage
from app.application.llm.dto import LLMRequestDTO, LLMResponseDTO, LLMStreamResponseChunkDTO, InquireBalanceResponseDTO

class LLMClient(Protocol):
    """
    大模型端口
    负责模型聊天内容生成与账户查询等
    """

    def generate(self, request: LLMRequestDTO) -> LLMResponseDTO:
        """
        模型非流式生成
        Args:
            request (LLMRequestDTO): 模型请求值对象
        Returns: LLMResponseDTO
            模型响应值对象
        """
        ...

    def generate_stream(self, request: LLMRequestDTO) -> Iterator[LLMStreamResponseChunkDTO]:
        """
        模型流式生成
        Args:
            request (LLMRequestDTO): 模型请求值对象
        Returns: Iterator[LLMStreamResponseChunkDTO]
            模型流式响应块值对象生成器
        """
        ...

    def inquire_balance(self) -> InquireBalanceResponseDTO:
        """
        账户余额查询
        Returns: InquireBalanceResponseDTO
            账户余额信息
        """
        ...

class TextSummarizer(Protocol):
    """
    文本总结器
    负责调用 llm 进行各种文本总结工作
    """

    def summarize_session_title(self, query: str) -> LLMResponseDTO:
        """
        总结会话标题
        Args:
            query (str): 用户输入
        Returns: LLMResponseDTO
            包含 llm 生成会话标题的响应
        """
        ...

    def summarize_messages(self, messages: list[ChatMessage], previous_summary: str) -> LLMResponseDTO:
        """
        结合当前会话与之前的总结重新生成会话历史总结
        Args:
            messages (list[ChatMessage]):   当前的会话
            previous_summary (str):         之前总结的会话历史
        Returns: LLMResponseDTO
            包含 llm 生成新总结会话历史的响应
        """
        ...
