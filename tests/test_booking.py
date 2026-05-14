from datetime import time, timedelta

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from booking.models import BookingRule, validate_booking_time_slot


@pytest.mark.django_db
def test_validate_booking_time_slot_allows_valid_window():
    BookingRule.objects.create(
        name="CI Booking Rule",
        max_duration_hours=4,
        daily_booking_limit=2,
        weekly_booking_limit=5,
        max_advance_days=14,
        min_advance_hours=2,
        min_cancel_hours=2,
        min_modify_hours=2,
        booking_start_time=time(7, 0),
        booking_end_time=time(22, 0),
        is_active=True,
    )

    start_time = (timezone.now() + timedelta(days=1)).replace(
        hour=10,
        minute=0,
        second=0,
        microsecond=0,
    )
    end_time = start_time + timedelta(hours=1)

    assert validate_booking_time_slot(start_time, end_time) is True


@pytest.mark.django_db
def test_validate_booking_time_slot_rejects_outside_allowed_hours():
    BookingRule.objects.create(
        name="CI Booking Rule",
        max_duration_hours=4,
        daily_booking_limit=2,
        weekly_booking_limit=5,
        max_advance_days=14,
        min_advance_hours=2,
        min_cancel_hours=2,
        min_modify_hours=2,
        booking_start_time=time(7, 0),
        booking_end_time=time(22, 0),
        is_active=True,
    )

    start_time = (timezone.now() + timedelta(days=1)).replace(
        hour=6,
        minute=0,
        second=0,
        microsecond=0,
    )
    end_time = start_time + timedelta(hours=1)

    with pytest.raises(ValidationError, match="Booking validation error"):
        validate_booking_time_slot(start_time, end_time)
