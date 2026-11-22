import sqlite3
from datetime import date

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.entities import BookingCreateDTO, BookingResponseDTO, BookingStatus
from src.app.core.interfaces import (
    AlreadyBookedRepositoryError,
    IBookingRepository,
    NotFoundRepositoryError,
)
from src.app.infrastructure.config import get_settings

from .models import BookingModel

setting = get_settings()


class BookingRepository(IBookingRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    @staticmethod
    def _to_dto(booking_model: BookingModel) -> BookingResponseDTO:
        """Convert a BookingModel instance to BookingResponseDTO.
        """
        return BookingResponseDTO(
            id=booking_model.id,
            name=booking_model.name,
            phone=booking_model.phone,
            booking_date=booking_model.booking_date,
            booking_time=booking_model.booking_time,
            guests=booking_model.guests,
            status=BookingStatus(booking_model.status),
        )

    @staticmethod
    def _is_slot_conflict(ex: IntegrityError) -> bool:

        if setting.db_engine == "sqlite+aiosqlite":
            # работает только для SQLite
            return getattr(
                ex.orig, "sqlite_errorcode", None
            ) == sqlite3.SQLITE_CONSTRAINT_UNIQUE and str(ex.orig) == (
                "UNIQUE constraint failed: bookings.booking_date, bookings.booking_time"
            )

        return True

    async def create_booking(
        self, booking_data: BookingCreateDTO
    ) -> BookingResponseDTO:

        try:
            booking_model = BookingModel(
                name=booking_data.name,
                phone=booking_data.phone,
                booking_date=booking_data.booking_date,
                booking_time=booking_data.booking_time,
                guests=booking_data.guests,
                status=BookingStatus.ACTIVE.value,
            )

            self.session.add(booking_model)

            await self.session.flush()

            return self._to_dto(booking_model)

        except IntegrityError as ex:
            if self._is_slot_conflict(ex):
                raise AlreadyBookedRepositoryError()

            raise

    async def get_booking_by_id(self, booking_id: int) -> BookingResponseDTO:

        stmt = select(BookingModel).where(BookingModel.id == booking_id)
        result = await self.session.execute(stmt)
        booking_model = result.scalar_one_or_none()

        if booking_model is None:
            raise NotFoundRepositoryError()

        return self._to_dto(booking_model)

    async def get_all_bookings(
        self, booking_date: date | None = None
    ) -> list[BookingResponseDTO]:

        stmt = select(BookingModel).order_by(
            BookingModel.booking_date, BookingModel.booking_time
        )

        if booking_date is not None:
            stmt = stmt.where(BookingModel.booking_date == booking_date)

        result = await self.session.execute(stmt)
        booking_models = result.scalars().all()

        return [self._to_dto(model) for model in booking_models]

    async def cancel_booking(self, booking_id: int) -> BookingResponseDTO:

        stmt = (
            update(BookingModel)
            .where(BookingModel.id == booking_id)
            .values(status=BookingStatus.CANCELLED.value)
            .returning(BookingModel)
        )

        result = await self.session.execute(stmt)
        booking_model = result.scalar_one_or_none()

        if booking_model is None:
            raise NotFoundRepositoryError()

        return self._to_dto(booking_model)
