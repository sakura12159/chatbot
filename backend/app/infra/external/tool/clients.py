import time
import logging
from typing import Any, Literal

from e2b import default_build_logger
from e2b_code_interpreter import Template, Sandbox
from e2b_code_interpreter.models import Execution

from tavily import TavilyClient

from app.infra.common.exceptions import ExternalError
from shared.config import SANDBOX_API_KEY, SANDBOX_TEMPLATE_NAME, SANDBOX_TEMPLATE_REQUIREMENTS, \
    SANDBOX_TIMEOUT_SECONDS, SANDBOX_TEMPLATE_MEMORY_MB, SANDBOX_TEMPLATE_CPU_COUNT, WEB_API_KEY, \
    WEB_TIMEOUT_SECONDS, WEB_SEARCH_DEPTH, WEB_SEARCH_INCLUDE_ANSWER, WEB_SEARCH_MAX_RESULTS, \
    WEB_EXTRACT_DEPTH, WEB_EXTRACT_FORMAT
from shared.utils import get_time_duration

logger = logging.getLogger(__name__)

class SandBoxClient:
    """
    沙盒客户端
    负责沙盒的模板创建、沙盒创建与运行
    """

    @staticmethod
    def _check_api_key(api_key: str | None):
        """ 检查 api key """
        if api_key is None:
            logger.exception(
                'E2B 沙盒 api 不存在'
            )

            raise ExternalError('E2B 沙盒 api 不存在')

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
    def _check_api_key(api_key: str | None):
        """ 检查 api key """
        if api_key is None:
            logger.exception(
                'Tavily api 不存在'
            )
            raise ExternalError('Tavily api 不存在')

    @staticmethod
    def search(
        query: str,
        *,
        api_key: str | None = WEB_API_KEY,
        max_results: int | None = WEB_SEARCH_MAX_RESULTS,
        search_depth: Literal['basic', 'advanced', 'fast', 'ultra-fast'] | None = WEB_SEARCH_DEPTH,
        chunks_per_source: int | None = 3,
        topic: Literal['general', 'news', 'finance'] | None = 'general',
        time_range: Literal['day', 'week', 'month', 'year', 'd', 'w', 'm', 'y'] | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        include_answer: bool | Literal['basic', 'advanced'] | None = WEB_SEARCH_INCLUDE_ANSWER,
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
        urls: str | list[str],
        *,
        api_key: str | None = WEB_API_KEY,
        query: str | None = None,
        chunks_per_source: int | None = 3,
        extract_depth: Literal['basic', 'advanced'] | None = WEB_EXTRACT_DEPTH,
        include_images: bool | None = False,
        include_favicon: bool | None = False,
        format: Literal['markdown', 'text'] | None = WEB_EXTRACT_FORMAT,
        timeout: float | None = WEB_TIMEOUT_SECONDS,
        include_usage: bool | None = False
    ) -> dict[str, Any]:
        """
        提取具体 url 的内容
        Args:
            urls (str | list[str]):                             url
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
