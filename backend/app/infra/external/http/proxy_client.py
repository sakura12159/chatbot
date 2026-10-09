import httpx

def create_proxy_client(proxy: str, **kwargs) -> httpx.Client:
    """ 创建代理 http 客户端 """
    return httpx.Client(
        proxy=proxy,
        **kwargs
    )
