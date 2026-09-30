"""Application exception classes and handlers."""

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import get_logger

logger = get_logger(__name__)


class AppException(Exception):
    """Base application exception."""

    def __init__(
        self,
        detail: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        errors: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(detail)
        self.detail = detail
        self.code = code
        self.status_code = status_code
        self.errors = errors or []


class NotFoundError(AppException):
    """Resource not found."""

    def __init__(self, detail: str = "Resource not found", code: str = "NOT_FOUND") -> None:
        super().__init__(detail=detail, code=code, status_code=status.HTTP_404_NOT_FOUND)


class ConflictError(AppException):
    """Resource conflict (e.g. duplicate client_uuid)."""

    def __init__(self, detail: str = "Resource conflict", code: str = "CONFLICT") -> None:
        super().__init__(detail=detail, code=code, status_code=status.HTTP_409_CONFLICT)


class PermissionDeniedError(AppException):
    """User lacks required permissions or scope."""

    def __init__(
        self,
        detail: str = "Permission denied",
        code: str = "PERMISSION_DENIED",
    ) -> None:
        super().__init__(detail=detail, code=code, status_code=status.HTTP_403_FORBIDDEN)


class AuthenticationError(AppException):
    """Authentication required or token invalid."""

    def __init__(
        self,
        detail: str = "Authentication failed",
        code: str = "UNAUTHORIZED",
    ) -> None:
        super().__init__(detail=detail, code=code, status_code=status.HTTP_401_UNAUTHORIZED)


class BadRequestError(AppException):
    """Invalid client request."""

    def __init__(self, detail: str = "Bad request", code: str = "BAD_REQUEST") -> None:
        super().__init__(detail=detail, code=code, status_code=status.HTTP_400_BAD_REQUEST)


def register_error_handlers(app: FastAPI) -> None:
    """Register custom exception handlers on the FastAPI application."""

    @app.exception_handler(AppException)
    async def app_exception_handler(_: Request, exc: AppException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.detail,
                "code": exc.code,
                "errors": exc.errors,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        errors = [
            {
                "field": ".".join(str(loc) for loc in err["loc"]),
                "message": err["msg"],
                "type": err["type"],
            }
            for err in exc.errors()
        ]
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": "Request validation failed",
                "code": "VALIDATION_ERROR",
                "errors": errors,
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code_map = {
            status.HTTP_401_UNAUTHORIZED: "UNAUTHORIZED",
            status.HTTP_403_FORBIDDEN: "FORBIDDEN",
            status.HTTP_404_NOT_FOUND: "NOT_FOUND",
            status.HTTP_405_METHOD_NOT_ALLOWED: "METHOD_NOT_ALLOWED",
            status.HTTP_409_CONFLICT: "CONFLICT",
        }
        code = code_map.get(exc.status_code, "HTTP_ERROR")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.detail,
                "code": code,
                "errors": [],
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled server exception: %s", str(exc))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Internal server error occurred",
                "code": "INTERNAL_SERVER_ERROR",
                "errors": [],
            },
        )
