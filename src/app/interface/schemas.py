from datetime import date, datetime, time, timedelta
from typing import Self

from pydantic import BaseModel, Field, field_validator, model_validator

from src.app.core.entities import BookingStatus


class BookingCreate(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    phone: str = Field(pattern=r"^\+7\d{10}$")
    booking_date: date
    booking_time: time
    guests: int = Field(ge=1, le=10)

    @field_validator("booking_date")
    @classmethod
    def validate_booking_date(cls, value: date) -> date:
        today = date.today()
        last_allowed_date = today + timedelta(days=30)

        if not today <= value <= last_allowed_date:
            raise ValueError(
                "Booking date must be between today and 30 days from today"
            )

        return value

    @field_validator("booking_time")
    @classmethod
    def validate_booking_time(cls, value: time) -> time:
        if value.tzinfo is not None:
            raise ValueError("Booking time must not contain a timezone offset")

        if value.minute != 0 or value.second != 0 or value.microsecond != 0:
            raise ValueError("Booking time must be a whole hour")

        if not time(12, 0) <= value <= time(22, 0):
            raise ValueError("Booking time must be between 12:00 and 22:00")

        return value

    @model_validator(mode="after")
    def validate_booking_datetime(self) -> Self:
        booking_datetime = datetime.combine(
            self.booking_date,
            self.booking_time,
        )
        now = datetime.now()

        if booking_datetime < now:
            raise ValueError("Booking date and time must not be in the past")

        return self


class BookingOut(BaseModel):
    id: int
    name: str
    phone: str
    booking_date: date
    booking_time: time
    guests: int
    status: BookingStatus
