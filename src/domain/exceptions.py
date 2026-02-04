class DomainError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class InvalidTokenError(DomainError):
    pass


class ExpiredTokenError(DomainError):
    pass


class UserAlreadyExistsError(DomainError):
    pass


class UserDoesNotExistsError(DomainError):
    pass


class InvalidCredentialsError(DomainError):
    pass


class UserBlockedError(DomainError):
    pass
