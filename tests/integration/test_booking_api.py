import asyncio

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def create_booking(client: AsyncClient, payload: dict) -> dict:

    response = await client.post("/bookings", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


async def test_success_status_codes_and_response_bodies(client, booking_payload):

    empty = await client.get("/bookings")
    assert empty.status_code == 200
    assert empty.json() == []

    booking = await create_booking(client, booking_payload)

    assert booking["status"] == "active"
    assert booking["booking_time"] == "15:00:00"

    found = await client.get(f"/bookings/{booking['id']}")
    assert found.status_code == 200
    assert found.json() == booking

    bookings = await client.get("/bookings")
    assert bookings.status_code == 200
    assert bookings.json() == [booking]

    cancelled = await client.delete(f"/bookings/{booking['id']}")
    assert cancelled.status_code == 200
    assert cancelled.json()['status'] == "cancelled"

    repeated = await client.delete(f"/bookings/{booking['id']}")
    assert repeated.status_code == 200
    assert repeated.json() == cancelled.json()

    preserved = await client.get(f"/bookings/{booking['id']}")
    assert preserved.status_code == 200
    assert preserved.json() == cancelled.json()


async def test_duplicate_active_slot(client, booking_payload):
    booking = await create_booking(client, booking_payload)

    response = await client.post("/bookings", json=booking_payload)
    assert response.status_code == 409
    assert response.json() == {"detail": "Slot is already booked"}

    listed = await client.get("/bookings")
    assert listed.status_code == 200
    assert listed.json() == [booking]


async def test_concurrent_creations_cannot_book_slot_twice(client, booking_payload):
    responses = await asyncio.gather(
        client.post("/bookings", json=booking_payload),
        client.post("/bookings", json=booking_payload),
    )

    assert sorted(response.status_code for response in responses) == [201, 409]
    conflict = next(response for response in responses if response.status_code == 409)
    assert conflict.json() == {"detail": "Slot is already booked"}

    listed = await client.get("/bookings")
    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert listed.json()[0]["status"] == "active"


async def test_cancelled_slot_can_be_booked_again(client, booking_payload):
    first = await create_booking(client, booking_payload)
    cancelled = await client.delete(f"/bookings/{first['id']}")
    assert cancelled.status_code == 200

    second = await create_booking(client, booking_payload)
    assert second["id"] != first["id"]

    repeated = await client.delete(f"/bookings/{first['id']}")
    assert repeated.status_code == 200
    assert repeated.json()["status"] == "cancelled"

    current = await client.get(f"/bookings/{second['id']}")
    assert current.status_code == 200
    assert current.json()["status"] == "active"


@pytest.mark.parametrize("method", ["GET", "DELETE"])
async def test_missing_booking_returns_404(client, method):
    response = await client.request(method, "/bookings/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Booking not found"}


@pytest.mark.parametrize(
    ("field", "value"),
    [
        pytest.param("name", "", id="empty-name"),
        pytest.param("name", "A", id="short-name"),
        pytest.param("name", "A" * 51, id="long-name"),
        pytest.param("phone", "871234567890", id="phone-prefix"),
        pytest.param("phone", "+7123456789", id="short-phone"),
        pytest.param("phone", "+712345678901", id="long-phone"),
        pytest.param("phone", "+7abcdefghij", id="phone-letters"),
        pytest.param("guests", 0, id="zero-guests"),
        pytest.param("guests", 11, id="too-many-guests"),
        pytest.param("guests", 1.5, id="fractional-guests"),
        pytest.param("booking_date", "2026-02-30", id="invalid-date"),
        pytest.param("booking_time", "11:00", id="before-opening"),
        pytest.param("booking_time", "23:00", id="after-closing"),
        pytest.param("booking_time", "12:30", id="nonzero-minutes"),
    ],
)
async def test_invalid_fields_return_422(
    client, booking_payload, field, value
):

    response = await client.post(
        "/bookings",
        json=booking_payload | {field: value},
    )

    assert response.status_code == 422, response.text

    listed = await client.get("/bookings")
    assert listed.status_code == 200
    assert listed.json() == []



