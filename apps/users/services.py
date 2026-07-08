from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone

from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken

from .models import OTP
from .selectors import get_active_otp
from .tasks import (
    send_otp_task,
    send_email_otp_task,
)
from .utils import (
    generate_otp,
    otp_expiry_time,
)

User = get_user_model()

# ── helpers ─────────────────────────────────────────────────────

def _get_user_by_identifier(identifier):
    if "@" in identifier:
        user = User.objects.filter(email__iexact=identifier).first()
    else:
        user = User.objects.filter(phone_number=identifier).first()

    if not user:
        raise ValidationError("User not found.")

    return user


def _issue_tokens(user):
    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }


def _send_otp(user, identifier, otp):
    """
    identifier: the email or phone string the user is authenticating with
    otp: the OTP model instance just created for this attempt
    """
    if "@" in identifier:
        if not user.email:
            raise ValidationError("Email not found.")
        send_email_otp_task.delay(user.email, otp.otp_code)
    else:
        if not user.phone_number:
            raise ValidationError("Phone number not found.")
        send_otp_task.delay(user.phone_number, otp.otp_code)


# ── OTP core ────────────────────────────────────────────────────

def create_otp(user, purpose):
    old_otp = get_active_otp(user, purpose)

    if old_otp:
        old_otp.delete()

    return OTP.objects.create(
        user=user,
        otp_code=generate_otp(),
        purpose=purpose,
        expires_at=otp_expiry_time(),
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

def register_user(full_name, email=None, phone_number=None):
    # normalize blanks to None so unique="" collisions can't happen
    email = email or None
    phone_number = phone_number or None

    user = None

    if email:
        user = User.objects.filter(email=email).first()

    if not user and phone_number:
        user = User.objects.filter(phone_number=phone_number).first()

    identifier = email or phone_number

    if user:
        if user.is_verified:
            raise ValidationError("User already exists.")

        otp = create_otp(user, OTP.Purpose.REGISTER)
        _send_otp(user, identifier, otp)
        return user

    user = User.objects.create_user(
        full_name=full_name,
        email=email,
        phone_number=phone_number,
        is_verified=False,
    )

    otp = create_otp(user, OTP.Purpose.REGISTER)
    _send_otp(user, identifier, otp)

    return user


def verify_register_otp(identifier, otp):
    user = _get_user_by_identifier(identifier)

    verify_otp(
        user=user,
        purpose=OTP.Purpose.REGISTER,
        otp_code=otp,
    )

    user.is_verified = True
    user.save()

    return _issue_tokens(user)


def login_user(identifier):
    user = _get_user_by_identifier(identifier)

    if not user.is_verified:
        raise ValidationError("Account is not verified.")

    otp = create_otp(user, OTP.Purpose.LOGIN)
    _send_otp(user, identifier, otp)

    return True


def verify_login_otp(identifier, otp):
    user = _get_user_by_identifier(identifier)

    verify_otp(
        user=user,
        purpose=OTP.Purpose.LOGIN,
        otp_code=otp,
    )

    return _issue_tokens(user)


def logout_user(refresh):
    try:
        RefreshToken(refresh).blacklist()
    except Exception:
        raise ValidationError("Invalid token")

    return True


def resend_otp(identifier, purpose):
    user = _get_user_by_identifier(identifier)

    existing_otp = get_active_otp(user=user, purpose=purpose)
    if existing_otp:
        _check_resend_cooldown(existing_otp)

    new_otp = create_otp(user=user, purpose=purpose)
    new_otp.resend_count = (existing_otp.resend_count + 1) if existing_otp else 1
    new_otp.last_resent_at = timezone.now()
    new_otp.save()

    _send_otp(user, identifier, new_otp)

    return True


def _check_resend_cooldown(otp, seconds=30):
    if not otp.last_resent_at:
        return

    cooldown = otp.last_resent_at + timedelta(seconds=seconds)

    if timezone.now() < cooldown:
        raise ValidationError("Please wait before requesting another OTP")