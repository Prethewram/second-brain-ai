from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.common.exceptions import (
    AIProviderException,
    ConflictException,
    NotFoundException,
    UnauthorizedException,
    ValidationException,
)


def register_exception_handlers(app: FastAPI):

    @app.exception_handler(AIProviderException)
    async def ai_provider_exception_handler(request: Request, exc: AIProviderException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "message": exc.message,
                "data": {
                    "conversation_id": exc.conversation_id,
                    "message_saved": exc.conversation_id is not None,
                    "actions_may_be_saved": exc.actions_may_be_saved,
                },
            },
        )

    @app.exception_handler(ValidationException)
    async def validation_exception_handler(
        request: Request,
        exc: ValidationException,
    ):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "message": exc.message,
                "data": None,
            },
        )

    @app.exception_handler(NotFoundException)
    async def not_found_exception_handler(
        request: Request,
        exc: NotFoundException,
    ):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "success": False,
                "message": exc.message,
                "data": None,
            },
        )

    @app.exception_handler(UnauthorizedException)
    async def unauthorized_exception_handler(
        request: Request,
        exc: UnauthorizedException,
    ):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "success": False,
                "message": exc.message,
                "data": None,
            },
        )

    @app.exception_handler(ConflictException)
    async def conflict_exception_handler(
        request: Request,
        exc: ConflictException,
    ):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "success": False,
                "message": exc.message,
                "data": None,
            },
        )

    @app.exception_handler(Exception)
    async def internal_exception_handler(
        request: Request,
        exc: Exception,
    ):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "Internal Server Error",
                "data": None,
            },
        )
