from dataclasses import dataclass
from datetime import date

from .entities import BookingCreateDTO, BookingResponseDTO
from .interfaces import (
    AlreadyBookedRepositoryError,
    IBookingRepository,
    NotFoundRepositoryError,
)
from .ports import ITransaction


class ServiceError(Exception):
    status_code: int = 500
    message: str = "Internal service error"

    def __init__(self, message: str | None = None):
        self.message = message or self.message
        super().__init__(self.message)


class SlotAlreadyBookedError(ServiceError):
    status_code = 409
    message = "Slot is already booked"


class BookingNotFoundError(ServiceError):
    status_code = 404
    message = "Booking not found"


@dataclass
class BookingService:
    repository: IBookingRepository
    transaction: ITransaction

    async def create_booking(
        self, booking_data: BookingCreateDTO
    ) -> BookingResponseDTO:

        try:
            async with self.transaction:
                return await self.repository.create_booking(booking_data)

        except AlreadyBookedRepositoryError as ex:
            raise SlotAlreadyBookedError() from ex

    async def get_bookings(
        self, booking_date: date | None = None
    ) -> list[BookingResponseDTO]:

        async with self.transaction:
            books = await self.repository.get_all_bookings(booking_date=booking_date)

        return books

    async def get_booking(self, booking_id: int) -> BookingResponseDTO:

        try:
            async with self.transaction:
                booking = await self.repository.get_booking_by_id(booking_id=booking_id)

            return booking

        except NotFoundRepositoryError as ex:
            raise BookingNotFoundError() from ex

    async def cancel_booking(self, booking_id: int) -> BookingResponseDTO:
        try:
            async with self.transaction:
                booking = await self.repository.cancel_booking(booking_id=booking_id)

            return booking

        except NotFoundRepositoryError as ex:
            raise BookingNotFoundError() from ex
