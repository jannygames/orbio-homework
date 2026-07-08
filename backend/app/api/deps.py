from functools import lru_cache
from typing import AsyncIterator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.base import AsyncSessionLocal
from app.repositories.conversation_repository import ConversationRepository
from app.services.llm.client import GeminiLLMClient, LLMClient


async def get_db() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        yield session


def get_conversation_repository(
    session: AsyncSession = Depends(get_db),
) -> ConversationRepository:
    return ConversationRepository(session)


@lru_cache
def _build_gemini_client() -> GeminiLLMClient:
    settings = get_settings()
    return GeminiLLMClient(api_key=settings.gemini_api_key, model=settings.gemini_model)


def get_llm_client() -> LLMClient:
    return _build_gemini_client()
