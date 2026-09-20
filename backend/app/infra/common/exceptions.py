from shared.exceptions import AppError

class InfrastructureError(AppError):
    code: int = 3000
    message: str = 'Unknown infrastructure error.'

class PersistenceError(InfrastructureError):
    code: int = 3101
    message: str = 'Unknown persistence error.'

class ExternalError(InfrastructureError):
    code: int = 3900
    message: str = 'Unknown external error.'

class HttpClientError(ExternalError):
    code: int = 3901
    message: str = 'Unknown http error.'

    def __init__(self, status_code: int | None = None, *args, **kwargs) -> None:
        self.status_code = status_code
        super().__init__(*args, **kwargs)
