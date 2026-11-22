from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.ports import ITransaction


class SQLAlchemyTransaction(ITransaction):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @property
    def session(self) -> AsyncSession:
        return self._session

    async def __aenter__(self) -> Self:
        await self._session.begin()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if exc_type is not None:
            await self.rollback()
            return

        try:
            await self.commit()
        except BaseException:
            await self.rollback()
            raise

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()
