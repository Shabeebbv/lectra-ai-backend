import pytest
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.users.models import OTP

User = get_user_model()
pytestmark = pytest.mark.django_db


class TestUserManager:
    def test_create_user_with_email_has_unusable_password(self, create_user):
        user = create_user(email="test@example.com")
        assert user.has_usable_password() is False
        assert user.email == "test@example.com"

    def test_create_user_with_phone_number(self, create_user):
        user = create_user(phone_number="+919876543210")
        assert user.phone_number == "+919876543210"
        assert user.email is None

    def test_create_user_without_identifier_raises(self):
        with pytest.raises(ValueError):
            User.objects.create_user(full_name="No Identifier")

    def test_create_superuser_sets_admin_role_and_flags(self):
        admin = User.objects.create_superuser(full_name="Admin", email="admin@example.com")
        assert admin.is_staff is True
        assert admin.is_superuser is True
        assert admin.role == "admin"


class TestOTPModel:
    def test_is_expired_false_for_future_expiry(self, create_user):
        user = create_user(email="a@a.com")
        otp = OTP.objects.create(
            user=user, otp_code="123456", purpose=OTP.Purpose.REGISTER,
            expires_at=timezone.now() + timedelta(minutes=5),
        )
        assert otp.is_expired() is False

    def test_is_expired_true_for_past_expiry(self, create_user):
        user = create_user(email="b@b.com")
        otp = OTP.objects.create(
            user=user, otp_code="123456", purpose=OTP.Purpose.REGISTER,
            expires_at=timezone.now() - timedelta(minutes=1),
        )
        assert otp.is_expired() is True

    def test_is_valid_false_when_used(self, create_user):
        user = create_user(email="c@c.com")
        otp = OTP.objects.create(
            user=user, otp_code="123456", purpose=OTP.Purpose.REGISTER,
            expires_at=timezone.now() + timedelta(minutes=5), is_used=True,
        )
        assert otp.is_valid() is False

    def test_is_valid_true_when_fresh(self, create_user):
        user = create_user(email="d@d.com")
        otp = OTP.objects.create(
            user=user, otp_code="123456", purpose=OTP.Purpose.REGISTER,
            expires_at=timezone.now() + timedelta(minutes=5),
        )
        assert otp.is_valid() is True