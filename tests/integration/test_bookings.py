import asyncio
from dataclasses import replace
from datetime import timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from src.app.core.entities import BookingStatus
from src.app.core.services import BookingNotFoundError, SlotAlreadyBookedError
from src.app.infrastructure.database.models import BookingModel

pytestmark = pytest.mark.asyncio


async def test_create_persists_booking(
    service, session_factory, booking_data
):
    created = await service.create_booking(booking_data)

    assert created.id > 0
    assert created.status is BookingStatus.ACTIVE

    # Другая сессия подтверждает, что изменения действительно сохранены.
    async with session_factory() as other_session:
        stored = await other_session.get(BookingModel, created.id)

        assert stored is not None
        assert stored.name == booking_data.name
        assert stored.phone == booking_data.phone
        assert stored.booking_date == booking_data.booking_date
        assert stored.booking_time == booking_data.booking_time
        assert stored.guests == booking_data.guests
        assert stored.status == "active"


async def test_duplicate_active_slot_is_rejected(service, booking_data):
    created = await service.create_booking(booking_data)

    with pytest.raises(SlotAlreadyBookedError) as caught:
        await service.create_booking(booking_data)

    assert caught.value.status_code == 409
    assert str(caught.value) == "Slot is already booked"

    bookings = await service.get_bookings()
    assert [booking.id for booking in bookings] == [created.id]


async def test_cancel_is_idempotent_and_releases_slot(
    service, booking_data
):
    first = await service.create_booking(booking_data)

    # Проверяем также чтение перед следующей операцией записи.
    loaded = await service.get_booking(first.id)
    assert loaded.status is BookingStatus.ACTIVE

    cancelled = await service.cancel_booking(first.id)
    repeated = await service.cancel_booking(first.id)

    assert cancelled.status is BookingStatus.CANCELLED
    assert repeated == cancelled

    replacement = await service.create_booking(booking_data)
    assert replacement.id != first.id

    await service.cancel_booking(first.id)

    old = await service.get_booking(first.id)
    current = await service.get_booking(replacement.id)

    assert old.status is BookingStatus.CANCELLED
    assert current.status is BookingStatus.ACTIVE


@pytest.mark.parametrize("method_name", ["get_booking", "cancel_booking"])
async def test_missing_booking_returns_not_found(service, method_name):
    method = getattr(service, method_name)

    with pytest.raises(BookingNotFoundError) as caught:
        await method(999)

    assert caught.value.status_code == 404
    assert str(caught.value) == "Booking not found"


async def test_list_filters_by_date(service, booking_data):
    assert await service.get_bookings() == []

    first = await service.create_booking(booking_data)
    other_data = replace(
        booking_data,
        booking_date=booking_data.booking_date + timedelta(days=1),
    )
    second = await service.create_booking(other_data)

    filtered = await service.get_bookings(
        booking_date=booking_data.booking_date
    )

    assert [booking.id for booking in filtered] == [first.id]
    assert {booking.id for booking in await service.get_bookings()} == {
        first.id,
        second.id,
    }


@pytest.mark.parametrize("guests", [0, 11])
async def test_check_violation_is_not_slot_conflict(
    service, booking_data, guests
):
    invalid = replace(booking_data, guests=guests)

    with pytest.raises(IntegrityError):
        await service.create_booking(invalid)

    assert await service.get_bookings() == []


async def test_two_concurrent_cancellations_succeed(
    service, service_factory, session_factory, booking_data
):
    created = await service.create_booking(booking_data)

    # Для параллельных задач нужны разные сессии. 
    async with session_factory() as first, session_factory() as second:
        results = await asyncio.gather(
            service_factory(first).cancel_booking(created.id),
            service_factory(second).cancel_booking(created.id),
        )

    assert all(booking.id == created.id for booking in results)
    assert all(
        booking.status is BookingStatus.CANCELLED
        for booking in results
    )