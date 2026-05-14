from datetime import timedelta

import pytest
from django.utils import timezone

from booking.utils import BookingRuleEnforcer


class _FakeRule:
    max_duration_hours = 2


@pytest.mark.django_db
def test_booking_rule_enforcer_rejects_long_duration(monkeypatch):
    monkeypatch.setattr("booking.utils.BookingRule.objects.first", lambda: _FakeRule())

    enforcer = BookingRuleEnforcer()
    start_time = timezone.now()
    end_time = start_time + timedelta(hours=3)

    is_valid, message = enforcer.validate_booking_duration(start_time, end_time)

    assert is_valid is False
    assert "cannot exceed 2 hours" in message


@pytest.mark.django_db
def test_booking_rule_enforcer_allows_duration_within_limit(monkeypatch):
    monkeypatch.setattr("booking.utils.BookingRule.objects.first", lambda: _FakeRule())

    enforcer = BookingRuleEnforcer()
    start_time = timezone.now()
    end_time = start_time + timedelta(hours=2)

    is_valid, message = enforcer.validate_booking_duration(start_time, end_time)

    assert is_valid is True
    assert message == ""
