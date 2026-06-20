from django.contrib.auth import get_user_model, authenticate
from django.utils import timezone
from datetime import timedelta
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken

from .models import OTP
from .utils import generate_otp, otp_expiry_time
from .selectors import get_active_otp
from .tasks import send_otp_task

User = get_user_model()


# ── helpers ─────────────────────────────────────────────────────

def _get_user_by_phone(phone_number):
    """Fetch user or raise ValidationError."""
    try:
        return User.objects.get(phone_number=phone_number)
    except User.DoesNotExist:
        raise ValidationError("User not found")


def _issue_tokens(user):
    """Return JWT access + refresh tokens for a user."""
    refresh = RefreshToken.for_user(user)
    return {
        "access":  str(refresh.access_token),
        "refresh": str(refresh),
    }


def _send_otp(user, purpose):
    """Create OTP and dispatch SMS task."""
    otp = create_otp(user, purpose)
    send_otp_task.delay(user.phone_number, otp.otp_code)
    return otp


# ── OTP core ────────────────────────────────────────────────────

def create_otp(user, purpose):
    old_otp = get_active_otp(user, purpose)

    if old_otp and not old_otp.is_expired():
        old_otp.delete()

    return OTP.objects.create(
        user=user,
        otp_code=generate_otp(),
        purpose=purpose,
        expires_at=otp_expiry_time()
    )


def verify_otp(user, purpose, otp_code):
    otp = get_active_otp(user, purpose)

    if not otp:
        raise ValidationError("OTP not found")

    if otp.is_expired():
        raise ValidationError("OTP expired")

    if otp.is_used:
        raise ValidationError("OTP already used")

    if otp.otp_code != otp_code:
        raise ValidationError("Invalid OTP")

    otp.is_used = True
    otp.save()

    return True


# ── auth services ────────────────────────────────────────────────

def register_user(full_name, phone_number, password):
    existing_user = User.objects.filter(
        phone_number=phone_number
    ).first()

    if existing_user:
        if existing_user.is_verified:
            raise ValidationError("User already registered")

        # resend OTP to unverified existing user
        _send_otp(existing_user, OTP.Purpose.REGISTER)
        return existing_user

    user = User.objects.create_user(
        full_name=full_name,
        phone_number=phone_number,
        password=password,
        is_verified=False
    )

    _send_otp(user, OTP.Purpose.REGISTER)

    return user


def verify_register_otp(phone_number, otp_code):
    user = _get_user_by_phone(phone_number)

    verify_otp(
        user=user,
        purpose=OTP.Purpose.REGISTER,
        otp_code=otp_code
    )

    user.is_verified = True
    user.save()

    return _issue_tokens(user)


def login_user(phone_number, password):
    user = authenticate(
        phone_number=phone_number,
        password=password
    )

    if not user:
        raise ValidationError("Invalid credentials")

    if not user.is_verified:
        raise ValidationError("Account is not verified")

    return _issue_tokens(user)


def forgot_password(phone_number):
    try:
        user = User.objects.get(phone_number=phone_number)
        _send_otp(user, OTP.Purpose.FORGOT_PASSWORD)

    except User.DoesNotExist:
        pass

    return True


def reset_password(phone_number, otp_code, password):
    user = _get_user_by_phone(phone_number)

    verify_otp(
        user=user,
        purpose=OTP.Purpose.FORGOT_PASSWORD,
        otp_code=otp_code
    )

    user.set_password(password)
    user.save()

    return True


def logout_user(refresh_token):
    try:
        RefreshToken(refresh_token).blacklist()
    except Exception:
        raise ValidationError("Invalid token")

    return True


def resend_otp(phone_number, purpose):
    user = _get_user_by_phone(phone_number)

    otp = get_active_otp(user=user, purpose=purpose)

    if otp:
        _check_resend_cooldown(otp)
        otp.delete()

    new_otp = create_otp(user=user, purpose=purpose)
    new_otp.resend_count += 1
    new_otp.last_resent_at = timezone.now()
    new_otp.save()

    send_otp_task.delay(user.phone_number, new_otp.otp_code)

    return True


def _check_resend_cooldown(otp, seconds=30):
    """Raise if OTP was resent too recently."""
    if not otp.last_resent_at:
        return

    cooldown = otp.last_resent_at + timedelta(seconds=seconds)

    if timezone.now() < cooldown:
        raise ValidationError(
            "Please wait before requesting another OTP"
        )