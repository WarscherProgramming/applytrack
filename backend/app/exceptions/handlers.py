import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError

from app.exceptions.http import AppError

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register all global exception handlers on the FastAPI app.

    Handler priority follows Starlette's MRO-based dispatch: when an exception
    is raised, Starlette checks for an exact-type handler first, then walks the
    MRO.  Registering AppError here catches every subclass (NotFoundError,
    ConflictError, etc.) that doesn't have its own explicit handler.
    """

    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    @app.exception_handler(PydanticValidationError)
    async def handle_pydantic_error(
        request: Request, exc: PydanticValidationError
    ) -> JSONResponse:
        # Catches pydantic.ValidationError raised by manual model_validate()
        # calls inside service code — distinct from FastAPI's built-in handler
        # for RequestValidationError (which covers request body parsing).
        return JSONResponse(
            status_code=422,
            content={"detail": exc.errors(include_url=False)},
        )

    @app.exception_handler(Exception)
    async def handle_unhandled_exception(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.error(
            "Unhandled exception on %s %s",
            request.method,
            request.url.path,
            exc_info=exc,
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "An unexpected error occurred."},
        )
