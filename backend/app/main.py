from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import chat, health
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.middleware import RequestIdMiddleware
from app.exceptions import register_exception_handlers

configure_logging()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Mini AI Product Assistant",
        description=(
            "A small AI chat assistant that answers questions about products and "
            "knows how to use tools (tool calling) to look them up in the catalog."
        ),
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestIdMiddleware)

    register_exception_handlers(app)

    app.include_router(health.router)
    app.include_router(chat.router)

    return app


app = create_app()
