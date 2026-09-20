from shared.exceptions import AppError

class ApplicationError(AppError):
    code: int = 2000
    message: str = 'Unknown application error.'

# ========== LLM 相关 ==========
class LLMError(ApplicationError):
    code: int = 2100
    message: str = 'Unknown llm error.'

class PromptLoadingFailsError(LLMError):
    code: int = 2101
    message: str = 'Prompt loading fails.'

class UnexpectedFinishReasonError(LLMError):
    code: int = 2102
    message: str = 'Unexpected finish reason for llm generation.'
