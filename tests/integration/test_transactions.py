from unittest.mock import AsyncMock

import pytest

pytestmark = pytest.mark.asyncio


async def test_commit_failure_propagates_and_rolls_back(
    service,
    session,
    session_factory,
    service_factory,
    booking_data,
    monkeypatch,
):
    failing_commit = AsyncMock(side_effect=RuntimeError("simulated commit failure"))
    monkeypatch.setattr(session, "commit", failing_commit)

    with pytest.raises(RuntimeError, match="simulated commit failure"):
        await service.create_booking(booking_data)

    failing_commit.assert_awaited_once()
    assert not session.in_transaction()

    async with session_factory() as fresh_session:
        fresh_service = service_factory(fresh_session)
        assert await fresh_service.get_bookings() == []
