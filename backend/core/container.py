from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from backend.adapters.storage.postgresql import PostgreSQLStorage
from backend.core.settings import Settings, get_settings


@dataclass(frozen=True)
class Container:
    """Application dependency container.

    The container is intentionally minimal in this stage and only exposes
    infrastructure-level dependencies required to boot the API.
    """

    settings: Settings
    database_engine: AsyncEngine
    session_factory: async_sessionmaker[AsyncSession]
    storage: PostgreSQLStorage


def build_container() -> Container:
    settings = get_settings()
    from backend.infrastructure.database.engine import create_engine
    from backend.infrastructure.database.session import create_session_factory

    database_engine = create_engine(settings.database_url, echo=settings.database_echo)
    session_factory = create_session_factory(database_engine)
    storage = PostgreSQLStorage(session_factory)
    return Container(
        settings=settings,
        database_engine=database_engine,
        session_factory=session_factory,
        storage=storage,
    )
