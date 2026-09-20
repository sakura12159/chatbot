import time
import logging
from typing import Generator

import psycopg
from psycopg import sql
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.infra.common.exceptions import PersistenceError
from shared.config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER, DB_DEFAULT_DBNAME, DB_ECHO, DB_POOL_SIZE, DB_MAX_OVERFLOW
from shared.utils import get_time_duration

logger = logging.getLogger(__name__)

Base = declarative_base()
engine = create_engine(
    url=f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}',
    echo=DB_ECHO,                   # 打印 SQL 日志
    pool_size=DB_POOL_SIZE,         # 连接池大小
    max_overflow=DB_MAX_OVERFLOW,   # 连接池溢出上限
)
session_maker = sessionmaker(
    bind=engine,
    autocommit=False,   # 禁止自动提交，手动控制事务
    autoflush=False,    # 禁止自动刷新，手动 flush
)

def get_orm_session() -> Generator:
    """ 生成数据库会话，用于 FastAPI 依赖注入。每次请求结束后自动关闭会话 """
    orm_session = session_maker()
    try:
        yield orm_session
    finally:
        orm_session.close()

def init_database(by_force: bool = False) -> None:
    """
    创建数据库与所有表
    Args:
        by_force (bool): 删除数据库后再重建
    """
    logger.info(
        '创建数据库',
        extra={
            'by_force': by_force
        }
    )
    start_time = time.perf_counter()

    try:
        conn = psycopg.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_DEFAULT_DBNAME,
            user=DB_USER,
            password=DB_PASSWORD,
            autocommit=True
        )
        with conn.cursor() as cur:
            if by_force:
                cur.execute(
                    """
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = %s
                    """, 
                    (DB_NAME,)
                )
                cur.execute(
                    sql.SQL('DROP DATABASE IF EXISTS {}')
                    .format(sql.Identifier(DB_NAME))
                )
            cur.execute(
                sql.SQL('CREATE DATABASE {}')
                .format(sql.Identifier(DB_NAME))
            )
        conn.close()

        logger.info(
            '创建数据库成功',
            extra={
                'by_force': by_force,
                'duration_ms': get_time_duration(start_time=start_time)
            }
        )

    except Exception as e:
        logger.exception(
            '创建数据库失败',
            extra={
                'by_force': by_force,
                'duration_ms': get_time_duration(start_time=start_time)
            }
        )

        raise PersistenceError(message=f'数据库创建异常: {e}') from e
    
    logger.info(
        '创建数据库中各表'
    )
    start_time = time.perf_counter()

    try:
        Base.metadata.create_all(bind=engine)
        logger.info(
            '各数据表创建成功',
            extra={
                'duration_ms': get_time_duration(start_time=start_time)
            }
        )

    except Exception as e:
        logger.exception(
            '数据表创建失败',
            extra={
                'duration_ms': get_time_duration(start_time=start_time)
            }
        )

        raise PersistenceError(message=f'数据表创建异常: {e}') from e
