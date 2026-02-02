from fastapi import FastAPI
from infrastructure.config import settings
from presentation.api.v1.endpoints import auth


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
    )

    @app.get("/healthcheck", tags=["service"])
    async def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    # Подключение роутеров
    app.include_router(auth.router, prefix="/api/v1")

    return app

app = create_app()
