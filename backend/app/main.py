import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import chat, health
from app.core.config import get_settings
from app.db.base import Base, engine
from app.exceptions import register_exception_handlers
from app.services.llm_service import GeminiLLMClient

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    app.state.llm_client = GeminiLLMClient(
        api_key=settings.gemini_api_key,
        model=settings.gemini_model,
    )

    yield


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Mini AI Product Assistant",
        description=(
            "A small AI chat assistant that answers questions about products and "
            "knows how to use tools (tool calling) to look them up in the catalog."
        ),
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    app.include_router(health.router)
    app.include_router(chat.router)

    return app


app = create_app()
