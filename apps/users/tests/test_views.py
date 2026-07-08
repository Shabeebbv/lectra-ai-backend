import pytest
from datetime import timedelta
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import OTP, FCMToken

pytestmark = pytest.mark.django_db


def auth_header(user):
    token = RefreshToken.for_user(user).access_token
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


class TestRegisterView:
    def test_register_with_email_returns_201(self, api_client, mock_otp_tasks):
        response = api_client.post("/api/users/register/", {
            "full_name": "New User",
            "email": "newuser@example.com",
        })
        assert response.status_code == 201

    def test_register_without_identifier_returns_400(self, api_client):
        response = api_client.post("/api/users/register/", {"full_name": "No Identifier"})
        assert response.status_code == 400

    def test_register_invalid_phone_returns_400(self, api_client):
        response = api_client.post("/api/users/register/", {
            "full_name": "Bad Phone",
            "phone_number": "abc123",
        })
        assert response.status_code == 400


class TestVerifyOtpView:
    def test_correct_otp_issues_tokens(self, api_client, create_user, mock_otp_tasks):
        user = create_user(email="verify@example.com")
        OTP.objects.create(
            user=user, otp_code="123456", purpose=OTP.Purpose.REGISTER,
            expires_at=timezone.now() + timedelta(minutes=5),
        )
        response = api_client.post("/api/users/verify-otp/", {
            "identifier": "verify@example.com",
            "otp": "123456",
        })
        assert response.status_code == 200
        assert "access" in response.data["data"]["tokens"]

    def test_wrong_otp_returns_400(self, api_client, create_user):
        create_user(email="wrongotp@example.com")
        response = api_client.post("/api/users/verify-otp/", {
            "identifier": "wrongotp@example.com",
            "otp": "000000",
        })
        assert response.status_code == 400


class TestLoginView:
    def test_verified_user_gets_otp_sent(self, api_client, create_user, mock_otp_tasks):
        create_user(email="login@example.com", is_verified=True)
        response = api_client.post("/api/users/login/", {"identifier": "login@example.com"})
        assert response.status_code == 200

    def test_unverified_user_returns_400(self, api_client, create_user, mock_otp_tasks):
        create_user(email="unverified@example.com", is_verified=False)
        response = api_client.post("/api/users/login/", {"identifier": "unverified@example.com"})
        assert response.status_code == 400


class TestMeView:
    def test_requires_authentication(self, api_client):
        response = api_client.get("/api/users/me/")
        assert response.status_code == 401

    def test_returns_user_data_when_authenticated(self, api_client, create_user):
        user = create_user(email="me@example.com", is_verified=True)
        response = api_client.get("/api/users/me/", **auth_header(user))
        assert response.status_code == 200
        assert response.data["data"]["email"] == "me@example.com"


class TestSaveFCMTokenView:
    def test_requires_authentication(self, api_client):
        response = api_client.post("/api/users/fcm-token/", {"token": "abc"})
        assert response.status_code == 401

    def test_saves_token_for_authenticated_user(self, api_client, create_user):
        user = create_user(email="fcm@example.com", is_verified=True)
        response = api_client.post(
            "/api/users/fcm-token/", {"token": "some-fcm-token-value"}, **auth_header(user)
        )
        assert response.status_code == 200
        assert FCMToken.objects.filter(user=user, token="some-fcm-token-value").exists()