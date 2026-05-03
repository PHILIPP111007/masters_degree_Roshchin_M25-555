from fastapi import HTTPException


class BaseHTTPException(HTTPException):
    error_code: str = "APP_ERROR"
    message: str = "Application error"
    meta: dict = {}

    def __init__(self, meta: dict | None = None):
        self.meta = meta or {}
        super().__init__(
            status_code=self.status_code,
            detail={
                "error_code": self.error_code,
                "message": self.message,
                "meta": self.meta,
            },
        )


class UserAlreadyExistsError(BaseHTTPException):
    error_code = "USER_ALREADY_EXISTS"
    message = "User with this email already exists"
    status_code = 409


class InvalidCredentialsError(BaseHTTPException):
    error_code = "INVALID_CREDENTIALS"
    message = "Invalid email or password"
    status_code = 401


class InvalidTokenError(BaseHTTPException):
    error_code = "INVALID_TOKEN"
    message = "Invalid token"
    status_code = 401


class TokenExpiredError(BaseHTTPException):
    error_code = "TOKEN_EXPIRED"
    message = "Token has expired"
    status_code = 401


class UserNotFoundError(BaseHTTPException):
    error_code = "USER_NOT_FOUND"
    message = "User not found"
    status_code = 404


class PermissionDeniedError(BaseHTTPException):
    error_code = "PERMISSION_DENIED"
    message = "Permission denied"
    status_code = 403
