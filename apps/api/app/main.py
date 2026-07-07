from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.constants import API_V1_PREFIX
from app.core.exceptions import (
    AppException,
    app_exception_handler,
    http_exception_handler,
    success_response,
    validation_exception_handler,
)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.API_VERSION,
        debug=settings.APP_DEBUG,
    )

    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.include_router(api_v1_router, prefix=API_V1_PREFIX)

    @app.get("/health", tags=["health"])
    def health_check() -> dict:
        return success_response(
            data={
                "status": "ok",
                "service": settings.PROJECT_NAME,
                "version": settings.API_VERSION,
            },
        )

    return app


app = create_app()
