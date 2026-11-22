from dataclasses import dataclass
from datetime import date, time
from enum import StrEnum

class BookingStatus(StrEnum):
    ACTIVE = "active"
    CANCELLED = "cancelled"

@dataclass(slots=True)
class BookingCreateDTO:
    
    name: str
    phone: str
    booking_date: date
    booking_time: time
    guests: int

@dataclass(slots=True, kw_only=True)
class BookingResponseDTO(BookingCreateDTO):
    
    id: int
    status: BookingStatus