class DomainError(Exception):
    pass

class InvalidTokenError(DomainError):
    pass

class ExpiredTokenError(DomainError):
    pass

class UserAlreadyExistsError(DomainError):
    pass