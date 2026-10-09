import json
import time
import logging
from typing import Any, Literal, Generator
from contextlib import contextmanager
from functools import lru_cache

from dotenv import load_dotenv
load_dotenv()

import httpx

from sqlalchemy import text, insert, select

from langchain_text_splitters import RecursiveCharacterTextSplitter

from e2b import default_build_logger
from e2b_code_interpreter import Template, Sandbox
from e2b_code_interpreter.models import Execution

from tavily import TavilyClient

from cohere import ClientV2

from app.infra.external.http.proxy_client import create_proxy_client
from app.infra.common.exceptions import ExternalError, PersistenceError
from app.infra.tool.rag.vector_database import session_maker
from app.infra.tool.rag.types import RetrievedChunk, RerankedChunk
from app.infra.tool.rag.models.source_document_model import SourceDocument
from app.infra.tool.rag.models.document_chunk_model import DocumentChunk
from shared.config import SANDBOX_API_KEY, SANDBOX_TEMPLATE_NAME, SANDBOX_TEMPLATE_REQUIREMENTS, \
    SANDBOX_TIMEOUT_SECONDS, SANDBOX_TEMPLATE_MEMORY_MB, SANDBOX_TEMPLATE_CPU_COUNT, WEB_API_KEY, \
    WEB_TIMEOUT_SECONDS, WEB_SEARCH_MAX_RESULTS, RAG_SPLIT_CHUNK_SIZE, RAG_SPLIT_CHUNK_OVERLAP, RAG_SPLIT_SEPERATORS, \
    RAG_EMBEDDING_MODEL, RAG_RERANK_MODEL, RAG_API_KEY, RAG_RETRIVE_HNSW_EF_SEARCH, RAG_RERANK_TOPK, \
    RAG_RETRIEVE_TOPK, RAG_RETRIEVE_MIN_SIMILARITY, RAG_EMBEDDING_TEXT_PER_CALL, \
    RAG_EMBEDDING_DIM, HTTP_PROXY_URL, HTTP_TIMEOUT_SECONDS
from shared.utils import get_time_duration

logger = logging.getLogger(__name__)

class SandBoxClient:
    """
    沙盒客户端
    负责沙盒的模板创建、沙盒创建与运行
    """

    @staticmethod
    def _check_api_key(api_key: str | None) -> None:
        """ 检查 api key """
        if api_key is None:
            logger.exception(
                'E2B 沙盒 api 不存在'
            )

            raise ExternalError('E2B 沙盒 api key 不存在')

    @staticmethod
    def build_template(
        api_key: str | None = SANDBOX_API_KEY,
        name: str = SANDBOX_TEMPLATE_NAME,
        cpu_count: int = SANDBOX_TEMPLATE_CPU_COUNT,
        memory_mb: int = SANDBOX_TEMPLATE_MEMORY_MB,
        requirements: list[str] = SANDBOX_TEMPLATE_REQUIREMENTS
    ) -> None:
        """
        创建 sandbox template
        Args:
            api_key (str | None):      e2b api key
            name (str):                模板名字
            cpu_count (int):           模板分配的 cpu 核数
            memory_mb (int):           模板分配的内存大小，单位为 MB
            requirements (list[str]):  模板安装库列表
        """
        SandBoxClient._check_api_key(api_key=api_key)

        logger.info(
            '创建沙盒模板',
            extra={
                'template_name': SANDBOX_TEMPLATE_NAME,
                'cpu_count': SANDBOX_TEMPLATE_CPU_COUNT,
                'memory_mb': SANDBOX_TEMPLATE_MEMORY_MB,
                'requirements': ' | '.join(SANDBOX_TEMPLATE_REQUIREMENTS)
            }
        )
        start_time = time.perf_counter()

        try:
            template = (
                Template()
                .from_template('code-interpreter-v1')
                .run_cmd([f'pip install {module}' for module in requirements])
            )

            Template.build(
                template=template,
                name=name,
                cpu_count=cpu_count,
                memory_mb=memory_mb,
                on_build_logs=default_build_logger(),
                api_key=api_key
            )

            logger.info(
                '创建沙盒模板成功',
                extra={
                    'template_name': SANDBOX_TEMPLATE_NAME,
                    'cpu_count': SANDBOX_TEMPLATE_CPU_COUNT,
                    'memory_mb': SANDBOX_TEMPLATE_MEMORY_MB,
                    'requirements': ' | '.join(SANDBOX_TEMPLATE_REQUIREMENTS),
                    'duration_ms': get_time_duration(start_time=start_time)
                }
            )
            
        except Exception as e:
            logger.exception(
                '创建沙盒模板失败',
                extra={
                    'template_name': SANDBOX_TEMPLATE_NAME,
                    'cpu_count': SANDBOX_TEMPLATE_CPU_COUNT,
                    'memory_mb': SANDBOX_TEMPLATE_MEMORY_MB,
                    'requirements': ' | '.join(SANDBOX_TEMPLATE_REQUIREMENTS),
                    'duration_ms': get_time_duration(start_time=start_time)
                }
            )

            raise ExternalError(f'沙箱模板 {name} 创建失败') from e

    @staticmethod
    def run_code(
        code: str,
        api_key: str | None = SANDBOX_API_KEY,
        template_name: str = SANDBOX_TEMPLATE_NAME,
        sandbox_timeout: int = SANDBOX_TIMEOUT_SECONDS
    ) -> Execution:
        """
        运行代码
        Args:
            api_key (str | None):   e2b api key
            code (str):             要运行的代码
            template_name (str):    模板名字
            sandbox_timeout (int):  沙盒运行超时时间
        Returns: Execution
            代码运行结果
        """
        SandBoxClient._check_api_key(api_key=api_key)

        logger.info(
            '沙盒执行代码',
            extra={
                'code': code,
                'template_name': SANDBOX_TEMPLATE_NAME,
                'sandbox_timeout': sandbox_timeout
            }
        )
        start_time = time.perf_counter()

        try:
            sandbox = Sandbox.create(
                template=template_name,
                timeout=sandbox_timeout,
                api_key=api_key
            )
            execution = sandbox.run_code(code)
            sandbox.kill()

            logger.info(
                '沙盒执行代码成功',
                extra={
                    'code': code,
                    'template_name': SANDBOX_TEMPLATE_NAME,
                    'sandbox_timeout': sandbox_timeout,
                    'duration_ms': get_time_duration(start_time=start_time)
                }
            )

            return execution
            
        except Exception as e:
            logger.info(
                '沙盒执行代码失败',
                extra={
                    'code': code,
                    'template_name': SANDBOX_TEMPLATE_NAME,
                    'sandbox_timeout': sandbox_timeout,
                    'duration_ms': get_time_duration(start_time=start_time)
                }
            )

            raise ExternalError(f'沙箱代码执行失败') from e

class WebClient:
    """
    网络检索客户端
    负责网络关键词搜索与提取具体页面信息
    """
    @staticmethod
    def _check_api_key(api_key: str | None) -> None:
        """ 检查 api key """
        if api_key is None:
            logger.exception(
                'Tavily api 不存在'
            )
            raise ExternalError('Tavily api key 不存在')

    @staticmethod
    def search(
        query: str,
        *,
        api_key: str | None = WEB_API_KEY,
        max_results: int | None = WEB_SEARCH_MAX_RESULTS,
        search_depth: Literal['basic', 'advanced', 'fast', 'ultra-fast'] | None = 'basic',
        chunks_per_source: int | None = 3,
        topic: Literal['general', 'news', 'finance'] | None = 'general',
        time_range: Literal['day', 'week', 'month', 'year', 'd', 'w', 'm', 'y'] | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        include_answer: bool | Literal['basic', 'advanced'] | None = 'basic',
        include_raw_content: bool | Literal['markdown', 'text'] | None = False,
        include_images: bool | None = False,
        include_image_descriptions: bool | None = False,
        include_favicon: bool | None = False,
        include_domains: list[str] | None = None,
        exclude_domains: list[str] | None = None,
        country: str | None = None,
        auto_parameters: bool | None = False,
        exact_match: bool | None = False,
        include_usage: bool | None = False,
        safe_search: bool | None = False,
        timeout: float | None = WEB_TIMEOUT_SECONDS
    ) -> dict[str, Any]:
        """
        使用 tavily api 进行网络搜索
        Args:
            query (str):                                                                        搜索关键字
            api_key (str | None):                                                               tavily api key
            max_results (int | None):                                                           搜索的结果数量
            search_depth (Literal['basic', 'advanced', 'fast', 'ultra-fast'] | None):           搜索深度
            chunks_per_source (int | None):                                                     相关分块数量
            topic (Literal['general', 'news', 'finance'] | None):                               搜索话题
            time_range (Literal['day', 'week', 'month', 'year', 'd', 'w', 'm', 'y'] | None):    过滤过去一段时间内的内容
            start_date (str | None):                                                            过滤开始时间
            end_date (str | None):                                                              过滤结束时间
            include_answer (bool | Literal['basic', 'advanced'] | None):                        是否包含总结部分
            include_raw_content (bool | Literal['markdown', 'text'] | None):                    结果中是否包含原始内容
            include_images (bool | None):                                                       结果中是否包含图片
            include_image_descriptions (bool | None):                                           结果中是否包含图片介绍
            include_favicon (bool | None):                                                      结果中是否包含 url 图标
            include_domains (list[str] | None):                                                 包含的搜索领域
            exclude_domains (list[str] | None):                                                 排除的搜索领域
            country (str | None):                                                               过滤搜索的国家
            auto_parameters (bool | None):                                                      自动设置搜索参数
            exact_match (bool | None):                                                          精确搜索
            include_usage (bool | None):                                                        结果中是否包含搜索使用信息
            safe_search (bool | None):                                                          安全搜索，需要专业版
            timeout (float | None):                                                             超时时间
        Returns: dict[str, Any]
            搜索结果，结构见 https://docs.tavily.com/documentation/api-reference/endpoint/search
        """
        WebClient._check_api_key(api_key=WEB_API_KEY)

        logger.info(
            '执行网络搜索',
            extra={
                'query': query,
                'max_results': max_results,
                'search_depth': search_depth,
                'include_answer': include_answer,
                'timeout': timeout
            }
        )
        start_time = time.perf_counter()

        client = TavilyClient(api_key=api_key)
        try:
            result = client.search(
                query=query,
                search_depth=search_depth,                              # type: ignore
                chunks_per_source=chunks_per_source,
                topic=topic,                                            # type: ignore
                time_range=time_range,                                  # type: ignore
                start_date=start_date,                                  # type: ignore
                end_date=end_date,                                      # type: ignore
                max_results=max_results,                                # type: ignore
                include_domains=include_domains,                        # type: ignore
                exclude_domains=exclude_domains,                        # type: ignore
                include_answer=include_answer,                          # type: ignore
                include_raw_content=include_raw_content,                # type: ignore
                include_images=include_images,                          # type: ignore
                include_image_descriptions=include_image_descriptions,
                timeout=timeout,                                        # type: ignore
                country=country,                                        # type: ignore
                auto_parameters=auto_parameters,                        # type: ignore
                include_favicon=include_favicon,                        # type: ignore
                include_usage=include_usage,                            # type: ignore
                exact_match=exact_match,                                # type: ignore
                safe_search=safe_search
            )

            logger.info(
                '执行网络搜索成功',
                extra={
                    'query': query,
                    'max_results': max_results,
                    'search_depth': search_depth,
                    'include_answer': include_answer,
                    'timeout': timeout,
                    'duration_ms': get_time_duration(start_time=start_time)
                }
            )
        
            return result

        except Exception as e:
            logger.exception(
                '执行网络搜索失败',
                extra={
                    'query': query,
                    'max_results': max_results,
                    'search_depth': search_depth,
                    'include_answer': include_answer,
                    'timeout': timeout,
                    'duration_ms': get_time_duration(start_time=start_time)
                }
            )

            raise ExternalError(f'检索关键字 {query} 失败') from e

    @staticmethod
    def extract(
        urls: list[str],
        *,
        api_key: str | None = WEB_API_KEY,
        query: str | None = None,
        chunks_per_source: int | None = 3,
        extract_depth: Literal['basic', 'advanced'] | None = 'basic',
        include_images: bool | None = False,
        include_favicon: bool | None = False,
        format: Literal['markdown', 'text'] | None = 'markdown',
        timeout: float | None = WEB_TIMEOUT_SECONDS,
        include_usage: bool | None = False
    ) -> dict[str, Any]:
        """
        提取具体 url 的内容
        Args:
            urls (list[str]):                                   url 列表
            api_key (str | None):                               tavily api key
            query (str | None):                                 查询关键字
            chunks_per_source (int | None):                     相关分块数量
            extract_depth (Literal['basic', 'advanced' | None): 提取深度
            include_images (bool | None):                       结果中是否包含图片
            include_favicon (bool | None):                      结果中是否包含图标
            format (Literal['markdown', 'text'] | None):        结果格式
            timeout (float | None):                             超时时间，单位为秒
            include_usage (bool | None):                        结果中是否包含使用信息
        Returns: dict[str, Any]
            访问结果 https://docs.tavily.com/documentation/api-reference/endpoint/extract
        """
        WebClient._check_api_key(api_key=WEB_API_KEY)

        logger.info(
            '执行网络信息提取',
            extra={
                'urls': urls if isinstance(urls, str) else ' | '.join(urls),
                'query': query,
                'extract_depth': extract_depth,
                'format': format,
                'timeout': timeout
            }
        )
        start_time = time.perf_counter()
        
        client = TavilyClient(api_key=api_key)
        try:
            result = client.extract(
                urls=urls,
                query=query,                            # type: ignore
                include_images=include_images,          # type: ignore
                extract_depth=extract_depth,            # type: ignore
                format=format,                          # type: ignore
                timeout=timeout,                        # type: ignore
                include_favicon=include_favicon,        # type: ignore
                include_usage=include_usage,            # type: ignore
                chunks_per_source=chunks_per_source     # type: ignore
            )

            logger.info(
                '执行网络信息提取成功',
                extra={
                    'urls': urls if isinstance(urls, str) else ' | '.join(urls),
                    'query': query,
                    'extract_depth': extract_depth,
                    'format': format,
                    'timeout': timeout,
                    'duration_ms': get_time_duration(start_time=start_time)
                }
            )

            return result

        except Exception as e:
            logger.exception(
                '执行网络信息提取失败',
                extra={
                    'urls': urls if isinstance(urls, str) else ' | '.join(urls),
                    'query': query,
                    'extract_depth': extract_depth,
                    'format': format,
                    'timeout': timeout,
                    'duration_ms': get_time_duration(start_time=start_time)
                }
            )
            
            raise ExternalError(f'提取 url {urls} 失败') from e

@contextmanager
def get_vector_orm_session() -> Generator:
    """ 生成向量数据库会话，用于依赖注入。每次请求结束后自动关闭会话 """
    orm_session = session_maker()
    orm_session.execute(text(f'SET hnsw.ef_search = {RAG_RETRIVE_HNSW_EF_SEARCH}'))  # 设置检索参数，提高召回率

    try:
        yield orm_session
    finally:
        orm_session.close()

@lru_cache(maxsize=1)
def get_proxy_client(proxy: str = HTTP_PROXY_URL, timeout: float = HTTP_TIMEOUT_SECONDS) -> httpx.Client:
    """ 获取 httpx 代理客户端，Cohere api 需要 """
    return create_proxy_client(proxy=proxy, timeout=timeout)

class RagClient:
    """
    基于 Cohere API 的 rag 客户端
    负责从向量数据库中检索相关信息
    """

    @staticmethod
    def _check_api_key(api_key: str | None) -> None:
        """ 检查 api key """
        if api_key is None:
            logger.exception(
                'Cohere api 不存在'
            )
            raise ExternalError('Cohere api key 不存在')

    @staticmethod
    def encode_text(
        texts: list[str],
        *,
        api_key: str | None = RAG_API_KEY,
        model: str = RAG_EMBEDDING_MODEL,
        text_per_call: int = RAG_EMBEDDING_TEXT_PER_CALL,
        output_dimension: int = RAG_EMBEDDING_DIM,
        embedding_type: Literal['float', 'int8', 'uint8', 'binary', 'ubinary', 'base64'] = 'float'
    ) -> list[list[float]]:
        """
        使用嵌入模型编码字符串
        Args:
            texts (list[str]):                                                                  要编码的字符串列表
            api_key (str | None):                                                               api key
            model (str):                                                                        嵌入模型名称
            text_per_call (int):                                                                每次 embed 的字符串数量
            output_dimension(int):                                                              嵌入维度
            embedding_type (Literal['float', 'int8', 'uint8', 'binary', 'ubinary', 'base64']):  嵌入编码的数据类型
        Returns: list[list[float]]
            编码列表
        """
        RagClient._check_api_key(api_key=api_key)

        logger.debug(
            '使用嵌入模型进行编码',
            extra={
                'text_count': len(texts)
            }
        )
        start_time = time.perf_counter()

        client = ClientV2(
            api_key=api_key,
            httpx_client=get_proxy_client()  # 注入自定义客户端
        )
        try:
            res = []
            for i in range(0, len(texts), text_per_call):
                response = client.embed(
                    texts=texts[i:i + text_per_call],
                    model=model,
                    input_type='search_document',
                    output_dimension=output_dimension,
                    embedding_types=[embedding_type]
                )
                res.extend(json.loads(response.json())['embeddings'][embedding_type])

            logger.debug(
                '嵌入模型编码成功',
                extra={
                    'text_count': len(texts),
                    'embedding_count': len(res),
                    'duration_ms': get_time_duration(start_time=start_time)
                }
            )

            return res

        except Exception as e:
            logger.exception(
                '嵌入模型编码失败',
                extra={
                    'text_count': len(texts),
                    'duration_ms': get_time_duration(start_time=start_time)
                }
            )
            
            raise ExternalError(f'嵌入模型编码失败: {e}') from e

    @staticmethod
    def ingest(
        name: str,
        content: str,
        source_url: str | None
    ) -> None:
        """
        文档内容切分
        Args:
            name (str):                 文档名
            content (str):              文档内容
            source_url (str | None):    文档链接
        """
        logger.info(
            '开始文档切分编码与入库',
            extra={
                'document_name': name,
                'source_url': source_url,
                'content_count': len(content)
            }
        )

        start_time = time.perf_counter()

        try:
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=RAG_SPLIT_CHUNK_SIZE,
                chunk_overlap=RAG_SPLIT_CHUNK_OVERLAP,
                separators=RAG_SPLIT_SEPERATORS
            )
            # 切分字符串并编码
            splitted_texts = splitter.split_text(text=content)
            if not splitted_texts:
                logger.info(
                    '文档切分结果为空，跳过入库',
                    extra={
                        'document_name': name,
                        'source_url': source_url,
                        'content_count': len(content),
                        'duration_ms': get_time_duration(start_time=start_time)
                    }
                )
                return
            
            embeddings = RagClient.encode_text(texts=splitted_texts)

        except Exception as e:
            logger.exception(
                '文档切分或编码失败',
                extra={
                    'document_name': name,
                    'source_url': source_url,
                    'content_count': len(content),
                    'duration_ms': get_time_duration(start_time=start_time)
                }
            )

            raise PersistenceError(f'文档切分或编码异常: {e}') from e

        if len(splitted_texts) != len(embeddings):
            logger.exception(
                '文档切分与编码结果长度不一致',
                extra={
                    'document_name': name,
                    'source_url': source_url,
                    'content_count': len(content),
                    'chunk_count': len(splitted_texts),
                    'embedding_count': len(embeddings),
                    'duration_ms': get_time_duration(start_time=start_time)
                }
            )

            raise PersistenceError(f'文档文档切分或编码异常')
        
        with get_vector_orm_session() as orm_session:
            try:
                # 存入数据库
                source_document_model = SourceDocument(
                    name=name,
                    source_url=source_url
                )
                orm_session.add(source_document_model)
                orm_session.flush()

                document_chunks = [
                    {
                        'document_id': source_document_model.id,
                        'chunk_index': i,
                        'content': splitted_text,
                        'embedding': embedding
                    } 
                    for i, (splitted_text, embedding) in enumerate(zip(splitted_texts, embeddings))
                ]

                orm_session.execute(insert(DocumentChunk), document_chunks)
                orm_session.commit()

                logger.info(
                    '文档切分入库成功',
                    extra={
                        'document_name': name,
                        'source_url': source_url,
                        'content_count': len(content),
                        'chunk_count': len(splitted_texts),
                        'duration_ms': get_time_duration(start_time=start_time)
                    }
                )

            except Exception as e:
                orm_session.rollback()

                logger.exception(
                    '文档切分入库失败',
                    extra={
                        'document_name': name,
                        'source_url': source_url,
                        'content_count': len(content),
                        'duration_ms': get_time_duration(start_time=start_time)
                    }
                )

                raise PersistenceError(f'文档切分入库异常: {e}') from e

    @staticmethod
    def retrieve(
        query: str, 
        topk: int = RAG_RETRIEVE_TOPK,
        min_similarity: float | None = RAG_RETRIEVE_MIN_SIMILARITY
    ) -> list[RetrievedChunk]:
        """
        向量检索
        Args:
            query (str):                    要检索的输入
            topk (int):                     检索前 n 条最相关的向量
            min_similarity (float | None):  相似度阈值
        Returns: list[RetrievedChunk]
            检索结果列表
        """
        logger.debug(
            '开始进行向量检索',
            extra={
                'query': query,
                'topk': topk,
                'min_similarity': min_similarity
            }
        )

        start_time = time.perf_counter()

        
        try:
            with get_vector_orm_session() as orm_session:
                embedding = RagClient.encode_text(texts=[query])[0]
                distance = DocumentChunk.embedding.cosine_distance(embedding)

                stmt = (
                    select(
                        DocumentChunk.id, 
                        DocumentChunk.document_id,
                        DocumentChunk.content,
                    )
                    .order_by(distance)
                    .limit(topk)
                )

                if min_similarity is not None:
                    stmt = stmt.where((1 - distance) >= min_similarity)

                document_chunk_models = orm_session.execute(stmt).all()

                res = [
                    RetrievedChunk(
                        id=model.id,
                        document_id=model.document_id,
                        content=model.content
                    )
                    for model in document_chunk_models
                ]

                logger.debug(
                    '向量检索成功',
                    extra={
                        'query': query,
                        'topk': topk,
                        'min_similarity': min_similarity,
                        'retrieved_count': len(res),
                        'duration_ms': get_time_duration(start_time=start_time)
                    }
                )

                return res

        except Exception as e:
            logger.exception(
                '向量检索失败',
                extra={
                    'query': query,
                    'topk': topk,
                    'min_similarity': min_similarity,
                    'duration_ms': get_time_duration(start_time=start_time)
                }
            )

            raise PersistenceError(f'向量检索失败: {e}') from e

    @staticmethod
    def rerank(
        query: str,
        chunks: list[str],
        *,
        api_key: str | None = RAG_API_KEY,
        model: str = RAG_RERANK_MODEL,
        topk: int = RAG_RERANK_TOPK
    ) -> list[RerankedChunk]:
        """
        检索结果重排序
        Args:
            query (str):        要匹配的字符串
            chunks (list[str]): 检索结果字符串列表
            topk (int):         返回前 n 条最相关的向量
        Returns: list[RerankedChunk]
            重排序结果类列表
        """
        RagClient._check_api_key(api_key=api_key)

        logger.debug(
            '开始对检索结果进行重排序',
            extra={
                'query': query,
                'chunk_count': len(chunks),
            }
        )
        start_time = time.perf_counter()

        client = ClientV2(
            api_key=api_key
        )
        try:        
            response = client.rerank(
                model=model,
                query=query,
                documents=chunks,
                top_n=topk
            )
            res = json.loads(response.json())
            res = [
                RerankedChunk(
                    content=chunks[result['index']],
                    score=result['relevance_score']
                )
                for result in res['results']
            ]

            logger.debug(
                '检索结果重排序成功',
                extra={
                    'query': query,
                    'chunk_count': len(chunks),
                    'reranked_chunk_count': len(res),
                    'duration_ms': get_time_duration(start_time=start_time)
                }
            )

            return res

        except Exception as e:
            logger.exception(
                '检索结果重排序失败',
                extra={
                    'query': query,
                    'chunk_count': len(chunks),
                    'duration_ms': get_time_duration(start_time=start_time)
                }
            )
            
            raise ExternalError(f'检索结果重排序失败: {e}') from e
