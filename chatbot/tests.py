import pytest
from django.test import Client
from django.urls import reverse


@pytest.mark.django_db
def test_chatbot_index_page():
    """Test the standalone chatbot index endpoint."""
    client = Client()
    url = reverse("chatbot:index")
    response = client.get(url)
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "chatbot"
    assert data["status"] == "ok"
    assert "Use /chatbot/chat/" in data["message"]


@pytest.mark.django_db
def test_health_check_endpoint():
    """Test the health endpoint returns a JSON response."""
    client = Client()
    url = reverse("chatbot:health")
    response = client.get(url)
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "ok"
