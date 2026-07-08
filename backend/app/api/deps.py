from typing import AsyncIterator

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import AsyncSessionLocal
from app.repositories.conversation_repository import ConversationRepository
from app.services.llm.client import LLMClient


async def get_db() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        yield session


def get_conversation_repository(
    session: AsyncSession = Depends(get_db),
) -> ConversationRepository:
    return ConversationRepository(session)


def get_llm_client(request: Request) -> LLMClient:
    return request.app.state.llm_client
