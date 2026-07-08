import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def create_user(db):
    """Factory fixture — call create_user(email=...) or create_user(phone_number=...)."""
    def _create_user(full_name="Test User", email=None, phone_number=None, is_verified=False, **kwargs):
        return User.objects.create_user(
            full_name=full_name,
            email=email,
            phone_number=phone_number,
            is_verified=is_verified,
            **kwargs,
        )
    return _create_user


@pytest.fixture(autouse=True)
def mock_otp_tasks(mocker):
    """
    Applies to every test automatically. Patches the Celery task objects
    at the exact point services.py imports them, so no test ever touches
    real Twilio/SMTP/Celery — .delay() calls are just recorded as mocks.
    """
    mock_sms = mocker.patch("apps.users.services.send_otp_task")
    mock_email = mocker.patch("apps.users.services.send_email_otp_task")
    return {"sms": mock_sms, "email": mock_email}