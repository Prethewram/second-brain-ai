class AppException(Exception):
    """
    Base exception for the application.
    """

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class NotFoundException(AppException):
    """
    Raised when a requested resource does not exist.
    """

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message)


class ValidationException(AppException):
    """
    Raised when validation fails.
    """

    def __init__(self, message: str = "Validation failed"):
        super().__init__(message)


class UnauthorizedException(AppException):
    """
    Raised when a user is not authorized.
    """

    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message)


class ConflictException(AppException):
    """
    Raised when a resource already exists or conflicts with existing data.
    """

    def __init__(self, message: str = "Conflict"):
        super().__init__(message)
