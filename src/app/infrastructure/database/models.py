from datetime import date, time

from sqlalchemy import (
    CheckConstraint,
    Date, 
    Index,
    Integer,
    String,
    Time
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from src.app.core.entities import BookingStatus

class Base(DeclarativeBase):
    pass


class BookingModel(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    phone: Mapped[str] = mapped_column(String(12), nullable=False)
    booking_date: Mapped[date] = mapped_column(Date, nullable=False)
    booking_time: Mapped[time] = mapped_column(Time, nullable=False)
    guests: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(12), nullable=False, default=BookingStatus.ACTIVE)

    __table_args__ = (
        Index("unique_bookings_active_slot", booking_date, booking_time, unique=True, sqlite_where=(status == 'active')),
        CheckConstraint("length(name) >= 2", name="check_name_min_length"),
        CheckConstraint("length(phone) = 12", name="check_phone_exact_length"),
        CheckConstraint("status IN ('active', 'cancelled')", name="check_booking_status"),
        CheckConstraint("guests BETWEEN 1 AND 10", name="check_booking_guests")
    )