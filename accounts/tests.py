import json

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

User = get_user_model()


@pytest.mark.django_db
def test_create_user():
    """Test creating a regular user"""
    user = User.objects.create_user(
        email="normal@user.com", student_id="ST12345", phone_number="1234567890", password="foo"
    )
    assert user.email == "normal@user.com"
    assert user.student_id == "ST12345"
    assert user.is_active is True
    assert user.is_staff is False
    assert user.is_superuser is False


@pytest.mark.django_db
def test_create_superuser():
    """Test creating a superuser"""
    admin_user = User.objects.create_superuser(
        email="super@admin.com", student_id="ADMIN", phone_number="000", password="foo"
    )
    assert admin_user.email == "super@admin.com"
    assert admin_user.is_active is True
    assert admin_user.is_staff is True
    assert admin_user.is_superuser is True


@pytest.mark.django_db
def test_user_string_representation():
    """Test the string representation of the custom User model"""
    user = User.objects.create_user(email="test@example.com", student_id="NA", phone_number="00", password="foo")
    assert "test@example.com" in str(user)


@pytest.mark.django_db
def test_login_url_resolves():
    """Test that the login page is accessible"""
    client = Client()
    response = client.get(reverse("accounts:login"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_mobile_login_api_resolves():
    """Test the mobile login API endpoint."""
    client = Client()
    user = User.objects.create_user(
        email="mobile@user.com",
        student_id="MOBILE1",
        phone_number="1234567890",
        password="password123",
    )

    response = client.post(
        reverse("accounts:api_login"),
        data=json.dumps({"email": user.email, "password": "password123"}),
        content_type="application/json",
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["user"]["email"] == user.email


@pytest.mark.django_db
def test_mobile_profile_api_resolves():
    """Test the mobile profile API endpoint."""
    client = Client()
    user = User.objects.create_user(
        email="profile@user.com",
        student_id="PROFILE1",
        phone_number="1234567890",
        password="password123",
    )

    response = client.get(reverse("accounts:api_profile"), {"user_id": user.id})

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["user"]["email"] == user.email
