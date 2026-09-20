import time
import logging
from typing import overload, Iterator, Literal

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.infra.common.exceptions import HttpClientError
from shared.config import HTTP_TIMEOUT_SECONDS,  HTTP_MAX_RETRIES, HTTP_WAIT_EXPONENTIAL_MULTIPLIER, HTTP_WAIT_EXPONENTIAL_MIN, HTTP_WAIT_EXPONENTIAL_MAX
from shared.utils import get_time_duration

logger = logging.getLogger(__name__)

class HttpClient:
    """
    HTTP 客户端基类
    封装通用 HTTP 行为：重试、超时、日志、错误转换。
    """
    
    def __init__(
        self,
        base_url: str,
        timeout: float = HTTP_TIMEOUT_SECONDS,
        headers: dict[str, str] = {},
    ):
        self.base_url = base_url.rstrip('/')
        self.headers = headers
        
        # httpx 客户端
        self._client = httpx.Client(
            base_url=self.base_url,
            headers=self.headers,
            timeout=timeout,
            follow_redirects=True,
        )

    @retry(
        stop=stop_after_attempt(HTTP_MAX_RETRIES),
        wait=wait_exponential(multiplier=HTTP_WAIT_EXPONENTIAL_MULTIPLIER, min=HTTP_WAIT_EXPONENTIAL_MIN, max=HTTP_WAIT_EXPONENTIAL_MAX),
        retry=retry_if_exception_type(httpx.TimeoutException),
    )
    def _request(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        json: dict | None = None,
        headers: dict | None = None,
    ) -> dict:
        """
        底层非流式请求方法
        Args:
            method (str):           请求方法
            path (str):             url
            params (dict | None):   请求参数，适用于 GET
            json (dict | None):     请求体，适用于 POST
            headers (dict | None):  请求头
        Returns: dict
            json 字典
        """
        url = path.lstrip('/')
        full_headers = {**self.headers, **(headers or {})}

        logger.debug(
            '发起非流式 HTTP 连接', 
            extra={
                'method': method,
                'url': url
            }
        )
        start_time = time.perf_counter()

        try:
            response = self._client.request(
                method=method,
                url=url,
                params=params,
                json=json,
                headers=full_headers
            )
            response.raise_for_status()

            logger.debug(
                '非流式 HTTP 连接成功', 
                extra={
                    'method': method,
                    'url': url,
                    'duration_ms': get_time_duration(start_time=start_time),
                    'status_code': response.status_code
                }
            )

            return response.json()
        
        except httpx.TimeoutException as e:
            logger.exception(
                '非流式 HTTP 连接超时', 
                extra={
                    'method': method,
                    'url': url,
                    'duration_ms': get_time_duration(start_time=start_time)
                },
                exc_info=True
            )
            
            raise HttpClientError(message=f'非流式 HTTP 连接超时: {e}') from e
        
        except httpx.HTTPStatusError as e:
            logger.exception(
                '非流式 HTTP 连接状态错误', 
                extra={
                    'method': method,
                    'url': url,
                    'duration_ms': get_time_duration(start_time=start_time),
                    'status_code': e.response.status_code
                },
                exc_info=True
            )

            raise HttpClientError(
                status_code=e.response.status_code,
                message=f'非流式 HTTP 连接错误: {e}'
            ) from e
        
        except Exception as e:
            logger.exception(
                '非流式 HTTP 连接未知错误', 
                extra={
                    'method': method,
                    'url': url,
                    'duration_ms': get_time_duration(start_time=start_time)
                },
                exc_info=True
            )

            raise HttpClientError(message=f'非流式 HTTP 连接失败: {e}') from e

    def _stream(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        json: dict | None = None,
        headers: dict | None = None,
    ) -> Iterator[str]:
        """
        底层流式请求方法
        Args:
            method (str):           请求方法
            path (str):             url
            params (dict | None):   请求参数，适用于 GET
            json (dict | None):     请求体，适用于 POST
            headers (dict | None):  请求头
        Returns: Iterator[str]
            流式生成的字节流
        """
        url = path.lstrip('/')
        full_headers = {**self.headers, **(headers or {})}

        logger.debug(
            '发起流式 HTTP 连接', 
            extra={
                'method': method,
                'url': url
            }
        )
        start_time = time.perf_counter()

        try:
            with self._client.stream(
                method=method, 
                url=url,
                params=params,
                json=json,
                headers=full_headers
            ) as response:
                if response.status_code >= 400:
                    response.read()
                    logger.error(
                        '流式 HTTP 连接异常',
                        extra={
                            'method': method,
                            'url': url,
                            'duration_ms': get_time_duration(start_time=start_time),
                            'status_code': response.status_code,
                            'text': response.text
                        }
                    )
                response.raise_for_status()

                for chunk in response.iter_lines():
                    yield chunk

            logger.debug(
                '流式 HTTP 连接成功', 
                extra={
                    'method': method,
                    'url': url,
                    'duration_ms': get_time_duration(start_time=start_time),
                    'status_code': response.status_code
                }
            )
        
        except httpx.TimeoutException as e:
            logger.exception(
                '流式 HTTP 连接超时', 
                extra={
                    'method': method,
                    'url': url,
                    'duration_ms': get_time_duration(start_time=start_time)
                },
                exc_info=True
            )
            
            raise HttpClientError(message=f'流式 HTTP 连接超时: {e}') from e
        
        except httpx.HTTPStatusError as e:
            logger.exception(
                '流式 HTTP 连接状态错误', 
                extra={
                    'method': method,
                    'url': url,
                    'duration_ms': get_time_duration(start_time=start_time),
                    'status_code': e.response.status_code
                },
                exc_info=True
            )

            raise HttpClientError(
                status_code=e.response.status_code,
                message=f'流式 HTTP 连接错误: {e}'
            ) from e
        
        except Exception as e:
            logger.exception(
                '流式 HTTP 连接未知错误', 
                extra={
                    'method': method,
                    'url': url,
                    'duration_ms': get_time_duration(start_time=start_time)
                },
                exc_info=True
            )

            raise HttpClientError(message=f'流式 HTTP 连接失败: {e}') from e

    def get(
        self,
        path: str,
        params: dict | None = None,
        headers: dict | None = None,
    ) -> dict:
        """
        普通 get 方法
        Args:
            path (str):             url
            params (dict | None):   请求参数
            headers (dict | None):  请求头
        Returns: dict
            响应字典
        """
        return self._request(method='GET', path=path, params=params, headers=headers)

    def post(
        self,
        path: str,
        json: dict | None = None,
        headers: dict | None = None,
    ) -> dict:
        """
        普通 post 方法
        Args:
            path (str):             url
            json (dict | None):     请求体
            headers (dict | None):  请求头
        Returns: dict
            响应字典
        """
        return self._request(method='POST', path=path, json=json, headers=headers)
        
    def stream(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        json: dict | None = None,
        headers: dict | None = None,
    ) -> Iterator[str]:
        """
        流式响应
        Args:
            method (str):           请求方法
            path (str):             url
            params (dict | None):   请求参数，适用于 GET
            json (dict | None):     请求体，适用于 POST
            headers (dict | None):  请求头
        Returns: Iterator[str]
            响应字节流
        """
        return self._stream(method=method, path=path, params=params, json=json, headers=headers)

    def close(self) -> None:
        """ 关闭 HTTP 连接池 """
        self._client.close()
