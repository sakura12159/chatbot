import json
import uuid
import logging.config

from datetime import datetime

from shared.config import LOG_DIRECTORY, LOG_FILENAME, LOG_CONFIG
from shared.utils import get_backend_directory

def init_logging() -> None:
    """ 初始化 log 配置 """
    p = get_backend_directory() / LOG_DIRECTORY
    p.mkdir(parents=True, exist_ok=True)
    open(p / LOG_FILENAME, 'a', encoding='utf-8').close()

    logging.config.dictConfig(LOG_CONFIG)

class JsonFormatter(logging.Formatter):

    STANDARD_ATTRS = {
        'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename',
        'module', 'exc_info', 'exc_text', 'stack_info', 'lineno', 'funcName',
        'created', 'msecs', 'relativeCreated', 'thread', 'threadName',
        'processName', 'process', 'message', 'asctime', 'taskName',
    }

    def format(self, record):

        def default_handler(obj):
            """ 处理 json 不兼容类型 """
            if isinstance(obj, uuid.UUID):
                return str(obj)
            if isinstance(obj, datetime):
                return obj.isoformat()
            return str(obj)
        
        log_data = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        # 附加 extra 中的自定义字段
        extra = {}
        for key, value in record.__dict__.items():
            if key not in self.STANDARD_ATTRS and not key.startswith("_"):
                extra[key] = value

        if extra:
            log_data['extra'] = extra
        # 附加异常堆栈
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_data, default=default_handler, ensure_ascii=False)
