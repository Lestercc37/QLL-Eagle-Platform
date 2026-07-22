from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine


def create_engine(database_url: str, *, echo: bool = False) -> AsyncEngine:
    """Create the application AsyncEngine."""
    return create_async_engine(database_url, echo=echo, future=True)
