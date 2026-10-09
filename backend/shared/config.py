import os
import logging
from typing import Literal

from dotenv import load_dotenv

load_dotenv()

# LLM
LLM_BASE_URL = 'https://api.deepseek.com'
LLM_CHAT_COMPLETIONS_PATH = '/chat/completions'
LLM_BALANCE_INQUERY_PATH = '/user/balance'
LLM_TIMEOUT_SECONDS = 60.0
LLM_API_KEY = os.getenv('DEEPSEEK_API_KEY')
LLM_CHAT_MODEL = 'deepseek-flash'
LLM_SUMMARIZATION_MODEL = 'deepseek-flash'
LLM_MAX_TOKENS = 1_000_000
LLM_MAX_TOKENS_PER_GENERATION = 8192
LLM_TEMPERATURE = 0.7
LLM_TOP_P = 0.9
LLM_MAX_REACT_ITERATIONS = 10
LLM_MAX_HISTORY_TURNS = 50
LLM_COMPRESSION_TRIGGER_HISTORY_TURNS = 20
LLM_COMPRESSION_TRIGGER_TOKENS = int(0.8 * LLM_MAX_TOKENS)
LLM_COMPRESSION_TURNS_PER_LOOP = 5

# prompt
CHAT_PROMPT_PATH = 'backend/app/infra/prompt/chat.yaml'
SESSION_TITLE_SUMMARIZATION_PROMPT_PATH = 'backend/app/infra/prompt/session_title_summarization.yaml'
SESSION_HISTORY_COMPRESSION_PROMPT_PATH = 'backend/app/infra/prompt/session_history_compression.yaml'

# log
LOG_DIRECTORY = 'logs'
LOG_FILENAME = 'app.log'
LOG_FORMATTER = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)s - %(message)s')
LOG_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'console': {
            'format': '%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s',
            'datefmt': '%H:%M:%S',
        },
        'json': {'()': 'shared.logging.JsonFormatter'},
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
            'level': 'INFO',
        },
        'file': {
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'formatter': 'json',
            'filename': f'{LOG_DIRECTORY}/{LOG_FILENAME}',
            'when': 'midnight',
            'backupCount': 30,
            'encoding': 'utf-8',
            'level': 'INFO',
        },
    },
    'loggers': {
        'app': {'level': 'DEBUG', 'handlers': ['console', 'file'], 'propagate': False},
        'sqlalchemy.engine': {'level': 'WARNING', 'handlers': ['console'], 'propagate': False},
        'httpx': {'level': 'WARNING', 'handlers': ['console'], 'propagate': False},
        'uvicorn.access': {'level': 'WARNING', 'handlers': ['console'], 'propagate': False},
    },
    'root': {'level': 'WARNING', 'handlers': ['console']},
}

# persistence
DB_HOST = '127.0.0.1'
DB_PORT = 5432
DB_USER = 'postgres'
DB_PASSWORD = '12159'
DB_NAME = 'chatbot'
DB_DEFAULT_DBNAME = 'postgres'
DB_ECHO = False
DB_POOL_SIZE = 10
DB_MAX_OVERFLOW = 20

# http
HTTP_PROXY_URL = 'http://127.0.0.1:7890'
HTTP_TIMEOUT_SECONDS = 10.0
HTTP_MAX_RETRIES = 3
HTTP_WAIT_EXPONENTIAL_MULTIPLIER = 1
HTTP_WAIT_EXPONENTIAL_MIN = 1
HTTP_WAIT_EXPONENTIAL_MAX = 10

# tools
# web
WEB_API_KEY = os.getenv('TAVILY_API_KEY')
WEB_TIMEOUT_SECONDS = 30.0
WEB_SEARCH_MAX_RESULTS = 10

# sandbox
SANDBOX_API_KEY = os.getenv('E2B_API_KEY')
SANDBOX_TEMPLATE_NAME = 'ai_code_execution'
SANDBOX_TEMPLATE_REQUIREMENTS = ['numpy', 'scipy', 'matplotlib', 'pandas']
SANDBOX_TEMPLATE_CPU_COUNT = 1
SANDBOX_TEMPLATE_MEMORY_MB = 512
SANDBOX_TIMEOUT_SECONDS = 30

# rag
RAG_API_KEY = os.getenv('COHERE_API_KEY')
RAG_DOCUMENT_PATH = 'backend/app/infra/tool/rag/documents'
RAG_DB_NAME = 'vector_db'
RAG_DB_ECHO = False
RAG_DB_POOL_SIZE = 10
RAG_DB_MAX_OVERFLOW = 20
RAG_SPLIT_CHUNK_SIZE = 200
RAG_SPLIT_CHUNK_OVERLAP = 20
RAG_SPLIT_SEPERATORS = ['\n\n', '\n', '。', '！', '？', '.', ' ', '']
RAG_EMBEDDING_MODEL = 'embed-v5.0-fast'
RAG_EMBEDDING_DIM = 1024
RAG_EMBEDDING_TEXT_PER_CALL = 96
RAG_RETRIEVE_MIN_SIMILARITY = 0.5
RAG_RETRIEVE_TOPK = 20
RAG_RETRIVE_HNSW_M = 16
RAG_RETRIVE_HNSW_EF_CONSTRUCTION = 200
RAG_RETRIVE_HNSW_EF_SEARCH = 100
RAG_RERANK_MODEL = 'rerank-v4.0-fast'
RAG_RERANK_TOPK = 5
RAG_RERANK_CHUNK_PER_CALL = 10
