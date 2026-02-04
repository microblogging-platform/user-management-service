from fastapi import FastAPI
from infrastructure.config import settings
from presentation.api.v1.endpoints import auth, user


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
    )

    @app.get("/healthcheck", tags=["service"])
    async def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(user.router, prefix="/api/v1")

    return app


app = create_app()
