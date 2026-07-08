import pytest
from datetime import timedelta
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.users.models import OTP
from apps.users import services

pytestmark = pytest.mark.django_db


class TestRegisterUser:
    def test_register_new_user_with_email_creates_otp_and_sends_email(self, mock_otp_tasks):
        user = services.register_user(full_name="Jane", email="jane@example.com")
        assert user.pk is not None
        assert user.is_verified is False

        otp = OTP.objects.get(user=user, purpose=OTP.Purpose.REGISTER)
        mock_otp_tasks["email"].delay.assert_called_once_with("jane@example.com", otp.otp_code)
        mock_otp_tasks["sms"].delay.assert_not_called()

    def test_register_new_user_with_phone_sends_sms(self, mock_otp_tasks):
        user = services.register_user(full_name="Sam", phone_number="+919876543210")
        otp = OTP.objects.get(user=user, purpose=OTP.Purpose.REGISTER)
        mock_otp_tasks["sms"].delay.assert_called_once_with("+919876543210", otp.otp_code)
        mock_otp_tasks["email"].delay.assert_not_called()

    def test_register_already_verified_user_raises(self, create_user, mock_otp_tasks):
        create_user(email="taken@example.com", is_verified=True)
        with pytest.raises(ValidationError):
            services.register_user(full_name="Someone", email="taken@example.com")

    def test_register_existing_unverified_user_resends_without_duplicating(self, create_user, mock_otp_tasks):
        existing = create_user(email="pending@example.com", is_verified=False)
        user = services.register_user(full_name="Pending", email="pending@example.com")
        assert user.pk == existing.pk
        mock_otp_tasks["email"].delay.assert_called_once()


class TestVerifyRegisterOtp:
    def test_correct_otp_marks_verified_and_returns_tokens(self, create_user):
        user = create_user(email="v@v.com")
        OTP.objects.create(
            user=user, otp_code="111111", purpose=OTP.Purpose.REGISTER,
            expires_at=timezone.now() + timedelta(minutes=5),
        )
        tokens = services.verify_register_otp(identifier="v@v.com", otp="111111")
        user.refresh_from_db()
        assert user.is_verified is True
        assert "access" in tokens and "refresh" in tokens

    def test_wrong_otp_raises(self, create_user):
        user = create_user(email="w@w.com")
        OTP.objects.create(
            user=user, otp_code="111111", purpose=OTP.Purpose.REGISTER,
            expires_at=timezone.now() + timedelta(minutes=5),
        )
        with pytest.raises(ValidationError):
            services.verify_register_otp(identifier="w@w.com", otp="000000")

    def test_expired_otp_raises(self, create_user):
        user = create_user(email="e@e.com")
        OTP.objects.create(
            user=user, otp_code="111111", purpose=OTP.Purpose.REGISTER,
            expires_at=timezone.now() - timedelta(minutes=1),
        )
        with pytest.raises(ValidationError):
            services.verify_register_otp(identifier="e@e.com", otp="111111")

    def test_already_used_otp_raises(self, create_user):
        user = create_user(email="u@u.com")
        OTP.objects.create(
            user=user, otp_code="111111", purpose=OTP.Purpose.REGISTER,
            expires_at=timezone.now() + timedelta(minutes=5), is_used=True,
        )
        with pytest.raises(ValidationError):
            services.verify_register_otp(identifier="u@u.com", otp="111111")

    def test_unknown_identifier_raises(self):
        with pytest.raises(ValidationError):
            services.verify_register_otp(identifier="ghost@example.com", otp="111111")


class TestLoginUser:
    def test_unverified_user_raises(self, create_user, mock_otp_tasks):
        create_user(email="nv@nv.com", is_verified=False)
        with pytest.raises(ValidationError):
            services.login_user(identifier="nv@nv.com")

    def test_verified_user_creates_login_otp_and_sends_email(self, create_user, mock_otp_tasks):
        create_user(email="ok@ok.com", is_verified=True)
        result = services.login_user(identifier="ok@ok.com")
        assert result is True
        assert OTP.objects.filter(purpose=OTP.Purpose.LOGIN).exists()
        mock_otp_tasks["email"].delay.assert_called_once()

    def test_phone_login_sends_sms(self, create_user, mock_otp_tasks):
        create_user(phone_number="+919999999999", is_verified=True)
        services.login_user(identifier="+919999999999")
        mock_otp_tasks["sms"].delay.assert_called_once()


class TestVerifyLoginOtp:
    def test_correct_otp_returns_tokens(self, create_user):
        user = create_user(email="l@l.com", is_verified=True)
        OTP.objects.create(
            user=user, otp_code="222222", purpose=OTP.Purpose.LOGIN,
            expires_at=timezone.now() + timedelta(minutes=5),
        )
        tokens = services.verify_login_otp(identifier="l@l.com", otp="222222")
        assert "access" in tokens


class TestResendOtp:
    def test_resend_replaces_old_otp_and_increments_count(self, create_user, mock_otp_tasks):
        user = create_user(email="r@r.com")
        old = OTP.objects.create(
            user=user, otp_code="333333", purpose=OTP.Purpose.REGISTER,
            expires_at=timezone.now() + timedelta(minutes=5),
            resend_count=2,
            last_resent_at=timezone.now() - timedelta(seconds=60),
        )
        services.resend_otp(identifier="r@r.com", purpose=OTP.Purpose.REGISTER)

        assert not OTP.objects.filter(pk=old.pk).exists()
        new_otp = OTP.objects.get(user=user, purpose=OTP.Purpose.REGISTER)
        assert new_otp.resend_count == 3
        mock_otp_tasks["email"].delay.assert_called_once()

    def test_resend_within_cooldown_raises(self, create_user, mock_otp_tasks):
        user = create_user(email="cd@cd.com")
        OTP.objects.create(
            user=user, otp_code="444444", purpose=OTP.Purpose.REGISTER,
            expires_at=timezone.now() + timedelta(minutes=5),
            last_resent_at=timezone.now(),
        )
        with pytest.raises(ValidationError):
            services.resend_otp(identifier="cd@cd.com", purpose=OTP.Purpose.REGISTER)

    def test_resend_with_no_prior_otp_starts_count_at_one(self, create_user, mock_otp_tasks):
        create_user(email="fresh@fresh.com")
        services.resend_otp(identifier="fresh@fresh.com", purpose=OTP.Purpose.REGISTER)
        otp = OTP.objects.get(purpose=OTP.Purpose.REGISTER)
        assert otp.resend_count == 1


class TestLogoutUser:
    def test_valid_refresh_token_blacklists_successfully(self, create_user):
        from rest_framework_simplejwt.tokens import RefreshToken
        user = create_user(email="lo@lo.com", is_verified=True)
        refresh = RefreshToken.for_user(user)
        assert services.logout_user(str(refresh)) is True

    def test_invalid_token_raises(self):
        with pytest.raises(ValidationError):
            services.logout_user("not-a-real-token")