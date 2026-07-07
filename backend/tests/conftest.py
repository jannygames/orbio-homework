from typing import AsyncIterator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.api import deps
from app.db.base import Base
from app.main import create_app
from app.services.llm_service import LLMClient, StreamChunk


class FakeGeminiClient:
    def __init__(self, turns: list[list[StreamChunk]]):
        self._turns = turns
        self.calls = 0

    async def stream_turn(self, contents, system_instruction) -> AsyncIterator[StreamChunk]:
        assert self.calls < len(self._turns), "FakeGeminiClient received more turns than scripted"
        turn = self._turns[self.calls]
        self.calls += 1
        for chunk in turn:
            yield chunk


@pytest_asyncio.fixture
async def test_engine():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def session_factory(test_engine):
    return async_sessionmaker(test_engine, expire_on_commit=False)


@pytest_asyncio.fixture
async def app(session_factory):
    application = create_app()

    async def override_get_db():
        async with session_factory() as session:
            yield session

    application.dependency_overrides[deps.get_db] = override_get_db
    application.dependency_overrides[deps.get_llm_client] = lambda: FakeGeminiClient(turns=[])

    yield application

    application.dependency_overrides.clear()


def set_llm_client(app, llm_client: LLMClient) -> None:
    app.dependency_overrides[deps.get_llm_client] = lambda: llm_client


@pytest_asyncio.fixture
async def client(app) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
