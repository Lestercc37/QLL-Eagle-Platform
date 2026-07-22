from __future__ import annotations

from backend.domain.ports import IDataProvider, INotificationService, IStorage


async def process_flow(
    storage: IStorage, provider: IDataProvider, notifications: INotificationService, underlying: str
) -> None:
    """ProcessFlow scaffold.

    Flow classification and persistence are intentionally deferred until the Flow Engine is specified.
    """
    raise NotImplementedError
