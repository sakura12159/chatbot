import logging
import time
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session as ORMSession

from app.domain.common.exceptions import SessionNotFoundError
from app.domain.message.value_objects import ChatMessage, ChatMessageRole
from app.domain.session.value_objects import ChatSessionId
from app.domain.session.entities import ChatSession
from app.infra.common.exceptions import PersistenceError
from app.infra.persistence.models.session_model import ChatSessionModel
from app.infra.persistence.models.message_model import ChatMessageModel
from shared.config import LLM_MAX_HISTORY_TURNS
from shared.utils import get_time_duration

logger = logging.getLogger(__name__)

class ChatSessionRepository:
    """
    会话表操作类
    负责查找、删除和保存新建或修改的会话
    """
    
    def __init__(self, orm_session: ORMSession) -> None:
        self.orm_session = orm_session

    def _to_model(self, session_domain: ChatSession, message_domains: list[ChatMessage]) -> ChatSessionModel:
        """
        将 ChatSession 转为 ChatSessionModel，将消息列表中的各 ChatMessage 转为 ChatMessageModel
        Args:
            session_domain (ChatSession):           会话实体
            message_domains (list[ChatMessage]):    消息列表
        Returns: ChatSessionModel
            orm ChatSessionModel
        """
        session_model= ChatSessionModel(
            id=session_domain.id,
            user_id=session_domain.user_id,
            title=session_domain.title,
            created_at=session_domain.created_at,
            summary=session_domain.summary,
            total_tokens=session_domain.total_tokens
        )

        for message in message_domains:
            session_model.messages.append(
                ChatMessageModel(
                id=message.id,
                session_id=message.session_id,
                role=message.role.value,
                content=message.content,
                reasoning_content=message.reasoning_content,
                reasoning_time=message.reasoning_time,
                created_at=message.created_at,
                tool_calls = message.tool_calls,
                tool_call_id=message.tool_call_id,
                is_compressed=message.is_compressed
            )
        )
        return session_model

    def _to_domain(self, session_model: ChatSessionModel, message_models: Sequence[ChatMessageModel]) -> ChatSession:
        """
        将 ChatSessionModel 转为 domain ChatSession，将列表中的各 ChatMessageModel 转为 ChatMessage
        Args:
            session_model (ChatSessionModel):           会话模型
            message_models (list[ChatMessageModel]):    消息模型列表
        Returns: ChatSession
            会话实体
        """
        session_domain = ChatSession(
            id=session_model.id,
            user_id=session_model.user_id,
            title=session_model.title,
            created_at=session_model.created_at,
            summary=session_model.summary,
            total_tokens=session_model.total_tokens
        )
        for message in message_models:
            session_domain.append_message(
                ChatMessage(
                    id=message.id,
                    session_id=message.session_id,
                    role=ChatMessageRole(message.role),
                    content=message.content,
                    created_at=message.created_at,
                    reasoning_content=message.reasoning_content,
                    reasoning_time=message.reasoning_time,
                    tool_calls = message.tool_calls,
                    tool_call_id=message.tool_call_id,
                    is_compressed=message.is_compressed
                )
            )
        return session_domain

    def find_by_id(self, id: ChatSessionId, max_turns: int = LLM_MAX_HISTORY_TURNS) -> ChatSession | None:
        """
        查询会话 id 对应会话
        Args:
            id (ChatSessionId): 会话 id
        Returns: ChatSession
            会话实体
        """
        logging.debug(
            '查询会话并加载部分消息',
            extra={
                'session_id': id,
                'max_turns': max_turns
            }
        )
        start_time = time.perf_counter()

        try:
            model = self.orm_session.get(ChatSessionModel, id)
            if model:
                logging.debug(
                    '查询会话成功',
                    extra={
                        'session_id': id,
                        'max_turns': max_turns,
                        'duration_ms': get_time_duration(start_time=start_time)
                    }
                )

                # 主查询查找 session model
                query = select(ChatMessageModel).where(ChatMessageModel.session_id == model.id)
                if max_turns > 0:
                    # 子查询查找第 max_turns 个未压缩的用户消息
                    subquery = (
                        select(ChatMessageModel.created_at)
                        .where(
                            ChatMessageModel.session_id == model.id,
                            ChatMessageModel.role == str(ChatMessageRole.USER)
                        )
                        .order_by(ChatMessageModel.created_at.desc())
                        .limit(1)
                        .offset(max_turns - 1)
                    )
                    boundary_time = self.orm_session.execute(subquery).scalar()

                    if boundary_time is not None:
                        # 加载从该时间点之后的所有消息，之前的未压缩消息不再加载
                        # 如果未压缩的 user 消息少于 max_turns，则 boundary_time 为 None，加载全部。
                        query = query.where(ChatMessageModel.created_at >= boundary_time)
                        
                query = query.order_by(ChatMessageModel.created_at.asc())
                messages = self.orm_session.execute(query).scalars().all()

                logging.debug(
                    '查询会话部分消息成功',
                    extra={
                        'session_id': id,
                        'max_turns': max_turns,
                        'messages_count': len(messages),
                        'duration_ms': get_time_duration(start_time=start_time)
                    }
                )

                return self._to_domain(session_model=model, message_models=messages)
            
        except Exception as e:
            logging.exception(
                '查询会话失败',
                extra={
                    'session_id': id,
                    'max_turns': max_turns,
                    'duration_ms': get_time_duration(start_time=start_time)
                }
            )

            raise PersistenceError(f'数据库查询异常: {e}') from e

    def delete_by_id(self, id: ChatSessionId) -> None:
        """
        删除会话
        Args:
            id (ChatSessionId): 会话 id
        """
        logging.debug(
            '提交删除会话事务',
            extra={
                'session_id': id
            }
        )
        start_time = time.perf_counter()

        try:
            model = self.orm_session.get(ChatSessionModel, id)
            if not model:
                logging.exception(
                    '提交删除会话事务失败，不存在该会话',
                    extra={
                        'session_id': id,
                        'duration_ms': get_time_duration(start_time=start_time)
                    }
                )

                raise SessionNotFoundError(f'会话 id {id} 不存在')
            
            self.orm_session.delete(model)
            self.orm_session.flush()

            logging.debug(
                '提交删除会话事务成功',
                extra={
                    'session_id': id,
                    'duration_ms': get_time_duration(start_time=start_time)
                }
            )

        except Exception as e:
            logging.exception(
                '提交删除会话事务失败',
                extra={
                    'session_id': id,
                    'duration_ms': get_time_duration(start_time=start_time)
                }
            )

            raise PersistenceError(f'数据库删除异常: {e}') from e

    def save(self, session: ChatSession) -> None:
        """
        保存会话及更新内容
        Args:
            session (ChatSession): 会话实体
        """
        logging.debug(
            '提交保存会话事务',
            extra={
                'session_id': session.id
            }
        )
        start_time = time.perf_counter()

        try:
            model = self._to_model(session_domain=session, message_domains=session.messages)
            self.orm_session.merge(model)
            self.orm_session.flush()

            logging.debug(
                '提交保存会话事务成功',
                extra={
                    'session_id': session.id,
                    'duration_ms': get_time_duration(start_time=start_time)
                }
            )
        
        except Exception as e:
            logging.exception(
                '提交保存会话事务失败',
                extra={
                    'session_id': session.id,
                    'duration_ms': get_time_duration(start_time=start_time)
                }
            )
            
            raise PersistenceError(f'数据库插入失败: {e}') from e
