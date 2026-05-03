from fastapi import FastAPI

from app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)

    @app.get("/health")
    async def health_check():
        return {"status": "ok", "service": settings.app_name}

    return app


app = create_app()
