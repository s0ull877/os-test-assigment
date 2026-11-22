from datetime import date
from typing import Annotated

from fastapi import APIRouter, Query, status

from src.app.core.entities import BookingCreateDTO

from .dependencies import BookingServiceDep
from .schemas import BookingCreate, BookingOut

router = APIRouter(prefix="/bookings", tags=["booking"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_booking(
    booking_data: BookingCreate,
    booking_service: BookingServiceDep,
) -> BookingOut:
    """Создать бронь."""
    booking = await booking_service.create_booking(
        BookingCreateDTO(**booking_data.model_dump())
    )
    return BookingOut.model_validate(booking, from_attributes=True)


@router.get("", status_code=status.HTTP_200_OK)
async def get_bookings(
    booking_service: BookingServiceDep,
    booking_date: Annotated[date | None, Query(alias="date")] = None,
) -> list[BookingOut]:
    """Получить список броней с необязательным фильтром по дате."""
    bookings = await booking_service.get_bookings(booking_date=booking_date)
    return [
        BookingOut.model_validate(booking, from_attributes=True)
        for booking in bookings
    ]


@router.get("/{booking_id}", status_code=status.HTTP_200_OK)
async def get_booking_by_id(
    booking_id: int,
    booking_service: BookingServiceDep,
) -> BookingOut:
    """Получить бронь по id."""
    booking = await booking_service.get_booking(booking_id=booking_id)
    return BookingOut.model_validate(booking, from_attributes=True)


@router.delete("/{booking_id}", status_code=status.HTTP_200_OK)
async def cancel_booking_by_id(
    booking_id: int,
    booking_service: BookingServiceDep,
) -> BookingOut:
    """Отменить бронь, сохранив запись."""
    booking = await booking_service.cancel_booking(booking_id=booking_id)
    return BookingOut.model_validate(booking, from_attributes=True)
