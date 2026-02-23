import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings
from app.dependencies import AppState
from app.errors import ClinCodeError, clincode_error_handler

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    settings = Settings()
    try:
        app.state.app_state = AppState.load(settings)
        logger.info("Models loaded successfully")
    except Exception:
        logger.exception("Failed to load models")
        app.state.app_state = None
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="ClinCode Copilot",
        description="ICD-9 clinical coding from discharge summaries",
        version="0.1.0",
        lifespan=lifespan,
    )

    settings = Settings()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_exception_handler(ClinCodeError, clincode_error_handler)

    from app.routers import health, codes, predict, neighbors

    app.include_router(health.router)
    app.include_router(predict.router, prefix="/api")
    app.include_router(neighbors.router, prefix="/api")
    app.include_router(codes.router, prefix="/api")

    return app


app = create_app()
