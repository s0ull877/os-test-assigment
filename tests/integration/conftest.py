from collections.abc import AsyncIterator, Callable
from datetime import date, datetime
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.app.core.services import BookingService
from src.app.infrastructure.database import repository as repository_module
from src.app.infrastructure.database.models import Base
from src.app.infrastructure.database.repository import BookingRepository
from src.app.infrastructure.database.session import database
from src.app.infrastructure.database.transaction import SQLAlchemyTransaction
from src.app.interface import schemas
from src.app.interface.main import app


@pytest_asyncio.fixture
async def session_factory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    monkeypatch.setattr(
        repository_module.setting, "db_engine", "sqlite+aiosqlite"
    )

    db_path = tmp_path / "test.sqlite3"
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{db_path.as_posix()}"
    )

    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        yield async_sessionmaker(
            engine,
            autoflush=False,
            expire_on_commit=False,
        )
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def session(session_factory) -> AsyncIterator[AsyncSession]:
    async with session_factory() as db_session:
        yield db_session


@pytest.fixture
def service_factory() -> Callable[[AsyncSession], BookingService]:
    def build(session: AsyncSession) -> BookingService:
        return BookingService(
            repository=BookingRepository(session),
            transaction=SQLAlchemyTransaction(session),
        )

    return build


@pytest.fixture
def service(session: AsyncSession, service_factory) -> BookingService:
    return service_factory(session)


@pytest.fixture
def fixed_clock(
    reference_time: datetime,
    monkeypatch: pytest.MonkeyPatch,
) -> None:

    class FixedDate(date):
        @classmethod
        def today(cls):
            return reference_time.date()

    class FixedDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return (
                reference_time
                if tz is None
                else reference_time.astimezone(tz)
            )

    monkeypatch.setattr(schemas, "date", FixedDate)
    monkeypatch.setattr(schemas, "datetime", FixedDatetime)


@pytest_asyncio.fixture
async def client(
    session_factory,
    monkeypatch: pytest.MonkeyPatch,
) -> AsyncIterator[AsyncClient]:

    async def override_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    monkeypatch.setitem(
        app.dependency_overrides,
        database.get_db_session,
        override_session,
    )

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as http_client:
        yield http_client
