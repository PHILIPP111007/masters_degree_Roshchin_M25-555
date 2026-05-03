from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import settings
from app.core.exceptions import BaseHTTPException
from app.db.base import Base
from app.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        lifespan=lifespan,
    )

    app.include_router(api_router, prefix="/auth")

    @app.exception_handler(BaseHTTPException)
    async def base_http_exception_handler(request, exc: BaseHTTPException):
        from fastapi.responses import JSONResponse

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error_code": exc.error_code,
                "message": exc.message,
                "meta": exc.meta,
            },
        )

    @app.get("/health")
    async def health_check():
        return {"status": "ok", "service": settings.app_name}

    return app


app = create_app()
