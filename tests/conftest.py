from dataclasses import asdict
from datetime import datetime, time, timedelta

import pytest

from src.app.core.entities import BookingCreateDTO


@pytest.fixture
def reference_time() -> datetime:
    return datetime(2026, 11, 22, 16, 30)


@pytest.fixture
def booking_data(reference_time: datetime) -> BookingCreateDTO:
    return BookingCreateDTO(
        name="Test Guest",
        phone="+70000000000",
        booking_date=reference_time.date() + timedelta(days=1),
        booking_time=time(15, 0),
        guests=2,
    )


@pytest.fixture
def booking_payload(booking_data: BookingCreateDTO) -> dict:
    payload = asdict(booking_data)
    payload["booking_date"] = booking_data.booking_date.isoformat()
    payload["booking_time"] = booking_data.booking_time.isoformat()
    return payload
