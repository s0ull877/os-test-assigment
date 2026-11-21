from abc import ABC, abstractmethod
from datetime import date

from .entities import BookingCreateDTO, BookingResponseDTO

class NotFoundRepositoryError(Exception):
    pass

class AlreadyBookedRepositoryError(Exception):
    pass

class IBookingRepository(ABC):
    
    @abstractmethod
    async def create_booking(self, booking: BookingCreateDTO) -> BookingResponseDTO:
        raise NotImplementedError

    @abstractmethod
    async def get_booking_by_id(self, booking_id: int) -> BookingResponseDTO:
        raise NotImplementedError

    @abstractmethod
    async def cancel_booking(self, booking_id: int) -> BookingResponseDTO:
        raise NotImplementedError

    @abstractmethod
    async def get_all_bookings(self, date: date | None = None) -> list[BookingResponseDTO]:
        raise NotImplementedError
    
    @abstractmethod
    async def get_for_update(self, booking_id: int) -> BookingResponseDTO:
        '''SQLite не обеспечивает FOR UPDATE'''
        raise NotImplementedError
