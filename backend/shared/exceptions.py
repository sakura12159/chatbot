class AppError(Exception):
    code: int = 0000
    message: str = 'Unknown app error.'

    def __init__(self, message: str | None = None) -> None:
        if message is not None:
            self.message = message
        super().__init__(self.message)
