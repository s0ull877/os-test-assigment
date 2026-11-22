from datetime import date, time, timedelta

import pytest

from src.app.core.entities import BookingCreateDTO


@pytest.fixture
def booking_data() -> BookingCreateDTO:
    return BookingCreateDTO(
        name="Test Guest",
        phone="+70000000000",
        booking_date=date.today() + timedelta(days=1),
        booking_time=time(15, 0),
        guests=2,
    )