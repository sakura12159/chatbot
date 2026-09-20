from shared.exceptions import AppError

class DomainError(AppError):
    code: int = 1000
    message: str = 'Unknown domain error.'

# ========== 用户领域 ==========
class UserNotFoundError(DomainError):
    code: int = 1101
    message: str = 'User cannot be found.'

class UserAlreadyExistsError(DomainError):
    code: int = 1102
    message: str = 'User already exists.'

# ========== 会话领域 ==========
class SessionNotFoundError(DomainError):
    code: int = 1201
    message: str = 'Session cannot be found.'

# ========== 工具领域 ==========
class ToolNotFoundError(DomainError):
    code: int = 1301
    message: str = 'Tool cannot be found.'

class ToolAlreadyExistsError(DomainError):
    code: int = 1302
    message: str = 'Tool already exists.'

class TooManyToolCallsError(DomainError):
    code: int = 1303
    message: str = 'Too many tool calls.'

class ToolCallFailsError(DomainError):
    code: int = 1304
    message: str = 'Tool call fails.'

class ToolCreationFailsError(DomainError):
    code: int = 1305
    message: str = 'Tool creation fails.'
