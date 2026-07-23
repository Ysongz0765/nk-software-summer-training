from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.schemas.common import ApiResponse


class AppError(Exception):
    code = 40000
    status_code = status.HTTP_400_BAD_REQUEST
    message = "request failed"

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.message
        super().__init__(self.message)


class ResourceNotFoundError(AppError):
    code = 40400
    status_code = status.HTTP_404_NOT_FOUND
    message = "resource not found"


class PermissionDeniedError(AppError):
    code = 40300
    status_code = status.HTTP_403_FORBIDDEN
    message = "permission denied"


class UnsupportedFileTypeError(AppError):
    code = 41500
    status_code = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    message = "unsupported file type"


class AIServiceUnavailableError(AppError):
    code = 50301
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    message = "ai service unavailable"


class OCRServiceUnavailableError(AppError):
    code = 50302
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    message = "ocr service unavailable"


class ExportFailedError(AppError):
    code = 50002
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    message = "export failed"


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ApiResponse(
                code=42200,
                message="validation error",
                data=exc.errors(),
            ).model_dump(),
        )

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=ApiResponse(code=exc.code, message=exc.message, data=None).model_dump(),
        )

    @app.exception_handler(Exception)
    async def internal_error_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ApiResponse(
                code=50000,
                message="internal server error",
                data=None,
            ).model_dump(),
        )
