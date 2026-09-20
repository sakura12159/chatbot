import time
import logging

import yaml

from app.domain.message.value_objects import ChatMessageRole
from app.domain.llm.value_objects import LLMMessage
from app.application.common.exceptions import PromptLoadingFailsError
from shared.config import CHAT_PROMPT_PATH, LLM_CHAT_MODEL, SESSION_TITLE_SUMMARIZATION_PROMPT_PATH, SESSION_HISTORY_COMPRESSION_PROMPT_PATH
from shared.utils import get_root_directory, get_time_duration

logger = logging.getLogger(__name__)

class PromptLoader:
    """
    提示词仓库
    负责加载提示词
    """

    def _load_yaml(self, path: str, **kwargs) -> dict:
        """
        加载 yaml 格式的提示词
        Args:
            path (str): 提示词文件路径
            **kwargs:   提示词模板中可能需要的参数
        Returns: dict
            读取的提示词字典
        """
        p = get_root_directory() / path

        logger.debug(
            '加载 yaml 格式提示词',
            extra={
                'path': p.resolve(),
                'kwargs': kwargs
            }
        )
        start_time = time.perf_counter()
        
        try:
            with open(p, 'r', encoding='utf-8') as f:
                prompt = yaml.safe_load(f)

            # 渲染变量
            fmap = {}
            for key, value in prompt.items():
                if isinstance(value, str):
                    fmap[key] = value.format(**kwargs)
                else:
                    fmap[key] = value
            logger.debug(
                '加载 yaml 格式提示词成功',
                extra={
                    'path': p.resolve(),
                    'kwargs': kwargs,
                    'duration_ms': get_time_duration(start_time=start_time)
                }
            )

            return fmap
        
        except Exception as e:
            logger.exception(
                '加载 yaml 格式提示词失败',
                extra={
                    'path': p.resolve(),
                    'kwargs': kwargs,
                    'duration_ms': get_time_duration(start_time=start_time)
                }
            )

            raise PromptLoadingFailsError(f'读取提示词 {p.resolve()} 失败') from e

    def load_chat_prompt(self, summary: str) -> list[LLMMessage]:
        """
        加载系统提示词
        Args:
            summary (str): 会话历史
        Returns: list[LLMMessage]
            包含提示词信息的列表
        """
        fmap = self._load_yaml(
            path=CHAT_PROMPT_PATH, 
            model_name=LLM_CHAT_MODEL, 
            cur_date=time.strftime('%Y-%m-%d'),
            summary=summary
        )
        return [LLMMessage(role=ChatMessageRole.SYSTEM, content=fmap.get('system', ''))]

    def load_session_title_summarization_prompt(self, query: str) -> list[LLMMessage]:
        """
        加载会话总结提示词
        Args:
            query (str): 用户输入
        Returns: list[LLMMessage]
            包含提示词信息的列表
        """
        fmap = self._load_yaml(
            path=SESSION_TITLE_SUMMARIZATION_PROMPT_PATH,
            query=query
        )
        return [
            LLMMessage(role=ChatMessageRole.SYSTEM, content=fmap.get('system', '')),
            LLMMessage(role=ChatMessageRole.USER, content=fmap.get('user', '')),
        ]

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
        fmap = self._load_yaml(
            path=SESSION_HISTORY_COMPRESSION_PROMPT_PATH,
            conversation_text=conversation_text,
            previous_summary=previous_summary
        )
        return [
            LLMMessage(role=ChatMessageRole.SYSTEM, content=fmap.get('system', '')),
            LLMMessage(role=ChatMessageRole.USER, content=fmap.get('user', '')),
        ]
