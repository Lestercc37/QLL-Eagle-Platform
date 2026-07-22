from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from backend.adapters.greeks.fake import FakeGreeksCalculator
from backend.adapters.providers.fake import FakeMarketDataProvider
from backend.adapters.storage.postgresql import PostgreSQLStorage
from backend.application.use_cases import (
    CalculateGreeksUseCase,
    GetMarketSnapshotUseCase,
    LoadOptionChainUseCase,
)
from backend.domain.ports import IDataProvider, IGreeksCalculator
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
    market_data_provider: IDataProvider
    greeks_calculator: IGreeksCalculator
    get_market_snapshot_use_case: GetMarketSnapshotUseCase
    load_option_chain_use_case: LoadOptionChainUseCase
    calculate_greeks_use_case: CalculateGreeksUseCase


def build_container() -> Container:
    settings = get_settings()
    from backend.infrastructure.database.engine import create_engine
    from backend.infrastructure.database.session import create_session_factory

    database_engine = create_engine(settings.database_url, echo=settings.database_echo)
    session_factory = create_session_factory(database_engine)
    storage = PostgreSQLStorage(session_factory)
    market_data_provider = FakeMarketDataProvider()
    greeks_calculator = FakeGreeksCalculator()
    get_market_snapshot_use_case = GetMarketSnapshotUseCase(market_data_provider)
    load_option_chain_use_case = LoadOptionChainUseCase(market_data_provider)
    calculate_greeks_use_case = CalculateGreeksUseCase(greeks_calculator)
    return Container(
        settings=settings,
        database_engine=database_engine,
        session_factory=session_factory,
        storage=storage,
        market_data_provider=market_data_provider,
        greeks_calculator=greeks_calculator,
        get_market_snapshot_use_case=get_market_snapshot_use_case,
        load_option_chain_use_case=load_option_chain_use_case,
        calculate_greeks_use_case=calculate_greeks_use_case,
    )
