class AppError(Exception):
    """Base application error."""

    def __init__(self, message: str = "Application error"):
        self.message = message
        super().__init__(message)


class ConflictError(AppError):
    """Resource already exists (e.g., duplicate email)."""

    def __init__(self, message: str = "Resource already exists"):
        super().__init__(message)


class UnauthorizedError(AppError):
    """Invalid credentials."""

    def __init__(self, message: str = "Invalid credentials"):
        super().__init__(message)


class ForbiddenError(AppError):
    """Insufficient permissions."""

    def __init__(self, message: str = "Forbidden"):
        super().__init__(message)


class NotFoundError(AppError):
    """Resource not found."""

    def __init__(self, message: str = "Not found"):
        super().__init__(message)


class ExternalServiceError(AppError):
    """External service (e.g., OpenRouter) returned an error."""

    def __init__(self, message: str = "External service error"):
        super().__init__(message)
