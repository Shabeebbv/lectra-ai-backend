from django.contrib.auth import get_user_model
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
    try:
        return User.objects.get(phone_number=phone_number)
    except User.DoesNotExist:
        raise ValidationError("User not found")


def _issue_tokens(user):
    refresh = RefreshToken.for_user(user)
    return {
        "access":  str(refresh.access_token),
        "refresh": str(refresh),
    }


def _send_otp(user, purpose):
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

def register_user(full_name, phone_number):
    existing_user = User.objects.filter(phone_number=phone_number).first()

    if existing_user:
        if existing_user.is_verified:
            raise ValidationError("Phone number already registered")

        # resend OTP to unverified existing user
        _send_otp(existing_user, OTP.Purpose.REGISTER)
        return existing_user

    user = User.objects.create_user(
        full_name=full_name,
        phone_number=phone_number,   
        is_verified=False
    )

    _send_otp(user, OTP.Purpose.REGISTER)

    return user


def verify_register_otp(phone_number, otp):
    user = _get_user_by_phone(phone_number)

    verify_otp(user=user, purpose=OTP.Purpose.REGISTER, otp_code=otp)

    user.is_verified = True
    user.save()

    return _issue_tokens(user)


def login_user(phone_number):
    user = _get_user_by_phone(phone_number)

    if not user.is_verified:
        raise ValidationError("Account is not verified")

    _send_otp(user, OTP.Purpose.LOGIN)

    return True


def verify_login_otp(phone_number, otp):
    user = _get_user_by_phone(phone_number)

    verify_otp(user=user, purpose=OTP.Purpose.LOGIN, otp_code=otp)

    return _issue_tokens(user)


def logout_user(refresh):
    try:
        RefreshToken(refresh).blacklist()
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
    new_otp.resend_count    += 1
    new_otp.last_resent_at  = timezone.now()
    new_otp.save()

    send_otp_task.delay(user.phone_number, new_otp.otp_code)

    return True


def _check_resend_cooldown(otp, seconds=30):
    if not otp.last_resent_at:
        return

    cooldown = otp.last_resent_at + timedelta(seconds=seconds)

    if timezone.now() < cooldown:
        raise ValidationError(
            "Please wait before requesting another OTP"
        )

