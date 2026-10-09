from app.domain.tool.value_objects import ToolCallResult
from app.domain.tool.entities import Tool
from app.infra.external.tool import clients

def code_execution(code: str) -> ToolCallResult:
    """ 执行 python 代码 """
    execution = clients.SandBoxClient.run_code(code=code)

    # todo: 图片处理
    if execution.error is None:
        success = True
        data = {
            'results': {
                'type': 'array',
                'value': execution.results
            },
            'stdout': {
                'type': 'string',
                'value': ''.join(execution.logs.stdout)
            },
            'stderr': {
                'type': 'string',
                'value': ''.join(execution.logs.stderr)
            }
        }
        error_message = None
    else:
        success = False
        data = None
        error_message = str(execution.error)

    return ToolCallResult(
        success=success,
        data=data,
        error_message=error_message
    )

def web_search(query: str) -> ToolCallResult:
    """ 网络搜索 """
    response = clients.WebClient.search(query=query)
    if 'detail' in response:
        success = False
        data = None
        error_message = response['detail']['error']
    else:
        success = True
        data = {
            f'result {i}': {
                'url': {
                    'type': 'string',
                    'value': result['url']
                },
                'content': {
                    'type': 'string',
                    'value': result['content']
                }
            } for i, result in enumerate(response['results'], 1)
        }
        data['answer'] = {  # type: ignore
            'type': 'string',
            'value': response['answer']
        }
        error_message = None

    return ToolCallResult(
        success=success,
        data=data,
        error_message=error_message
    )

def web_extract(urls: list[str], query: str | None = None) -> ToolCallResult:
    """ 访问单个或多个资源地址获取详细信息 """
    response = clients.WebClient.extract(urls=urls, query=query)
    if 'detail' in response:
        success = False
        data = None
        error_message = response['detail']['error']
    else:
        success = True
        data = {
            f'url {i}': {
                'url': {
                    'type': 'string',
                    'value': result['url']
                },
                'content': {
                    'type': 'string',
                    'value': result['raw_content']
                }
            } for i, result in enumerate(response['results'], 1)
        }
        error_message = None

    return ToolCallResult(
        success=success,
        data=data,
        error_message=error_message
    )

def rag(query: str) -> ToolCallResult:
    """ 使用检索增强生成（RAG）获取与输入有关的详细信息 """
    try:
        chunks = clients.RagClient.retrieve(query=query)
        chunks = clients.RagClient.rerank(query=query, chunks=[chunk.content for chunk in chunks])

        success = True
        data = {
            f'chunk {i}': {
                'content': {
                    'type': 'string',
                    'value': chunk.content
                }
            }
            for i, chunk in enumerate(chunks, 1)
        }
        error_message = None

    except Exception as e:
        success = False
        data = None
        error_message = 'Unknown rag error.'

    return ToolCallResult(
        success=success,
        data=data,
        error_message=error_message
    )

web_tools = [
    Tool.create(web_search, '需要查询的关键字'),
    Tool.create(web_extract, '一个或多个需要提取的 url', '可选的查询关键字，用于提取结果的重排序'),
]

code_tools = [
    Tool.create(code_execution, '需要执行的代码')
]

rag_tools = [
    Tool.create(rag, '需要检索的内容')
]

# builtin_tools: list = code_tools + web_tools + rag_tools

builtin_tools: list = web_tools + rag_tools
