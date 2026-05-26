import pytest

from booking.models import Room


@pytest.mark.django_db
def test_room_creation():
    """Test creating a new room operates as expected in Pytest"""
    Room.objects.create(
        name="Pytest Suite Room",
        room_number="PYT100",
        capacity=20,
        room_type="conference",
        is_available=True,
        description="A sample room exclusively for pytest tests.",
    )

    assert Room.objects.count() == 1

    # Fetch from database
    db_room = Room.objects.get(room_number="PYT100")
    assert db_room.name == "Pytest Suite Room"
    assert db_room.capacity == 20
    assert db_room.is_available is True


@pytest.mark.django_db
def test_room_capacity_is_positive():
    Room.objects.create(name="Pytest Small Room", room_number="PYT101", capacity=5)
    room = Room.objects.get(room_number="PYT101")
    assert room.capacity > 0


@pytest.mark.django_db
def test_room_string_representation():
    room = Room.objects.create(name="String Test Room", room_number="PYT102", capacity=10)
    assert str(room) == "String Test Room (PYT102)"
