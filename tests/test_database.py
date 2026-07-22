from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from backend.core.container import build_container
from backend.infrastructure.database.engine import create_engine
from backend.infrastructure.database.session import create_session_factory


@pytest.mark.asyncio
async def test_create_engine_returns_async_engine() -> None:
    engine = create_engine("sqlite+aiosqlite:///:memory:")

    try:
        assert isinstance(engine, AsyncEngine)
        assert str(engine.url) == "sqlite+aiosqlite:///:memory:"
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_session_factory_creates_async_session() -> None:
    engine = create_engine("sqlite+aiosqlite:///:memory:")
    session_factory = create_session_factory(engine)

    try:
        async with session_factory() as session:
            assert isinstance(session, AsyncSession)
            result = await session.execute(text("SELECT 1"))
            assert result.scalar_one() == 1
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_container_registers_postgresql_storage_adapter() -> None:
    container = build_container()

    try:
        assert container.storage.session_factory is container.session_factory
    finally:
        await container.database_engine.dispose()
