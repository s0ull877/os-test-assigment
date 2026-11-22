from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.services import BookingService
from src.app.infrastructure.database.repository import BookingRepository
from src.app.infrastructure.database.session import database
from src.app.infrastructure.database.transaction import SQLAlchemyTransaction

SessionDep = Annotated[
    AsyncSession,
    Depends(database.get_db_session),
]

async def get_booking_service(
    session: SessionDep,
):
    repository = BookingRepository(session=session)

    yield BookingService(
        repository=repository,
        transaction=SQLAlchemyTransaction(session=session)
    )

BookingServiceDep = Annotated[
    BookingService,
    Depends(get_booking_service)
]