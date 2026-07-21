from datetime import timedelta

from amqp import NotFound
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

import pyotp
from .models import MFADevice

User = get_user_model()

# ── helpers ─────────────────────────────────────────────────────

def _get_user_by_identifier(identifier):
    """
    Excludes soft-deleted users — a deleted account's email/phone
    is treated as if it doesn't exist for login/register/OTP purposes.
    """
    if "@" in identifier:
        user = User.objects.filter(email__iexact=identifier, is_deleted=False).first()
    else:
        user = User.objects.filter(phone_number=identifier, is_deleted=False).first()

    if not user:
        raise ValidationError("User not found.")

    return user


def _issue_tokens(user):
    refresh = RefreshToken.for_user(user)
    refresh["role"] = user.role
    refresh["full_name"] = user.full_name
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

    # Only match against active (non-deleted) users — a soft-deleted
    # user's email/phone is free for re-registration.
    if email:
        user = User.objects.filter(email=email, is_deleted=False).first()

    if not user and phone_number:
        user = User.objects.filter(phone_number=phone_number, is_deleted=False).first()

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

    if user.is_blocked:
        raise ValidationError("Your account has been blocked. Contact support.")

    otp = create_otp(user, OTP.Purpose.LOGIN)
    _send_otp(user, identifier, otp)

    return True


def verify_login_otp(identifier, otp):
    user = _get_user_by_identifier(identifier)

    if user.is_blocked:
        raise ValidationError("Your account has been blocked. Contact support.")

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
    


# ── MFA setup (called by an already-logged-in admin) ──────────────

def generate_mfa_secret(user):
    """
    Creates or resets an MFA device for the user with a fresh secret.
    Not enabled until verify_and_enable_mfa() succeeds — prevents a
    half-finished setup from locking anyone out.
    """
    secret = pyotp.random_base32()

    device, _ = MFADevice.objects.update_or_create(
        user=user,
        defaults={"secret": secret, "is_enabled": False, "enabled_at": None},
    )

    issuer = "Lectra AI"
    account_name = user.email or user.phone_number
    provisioning_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=account_name, issuer_name=issuer
    )

    return {"secret": secret, "provisioning_uri": provisioning_uri}


def verify_and_enable_mfa(user, code):
    device = MFADevice.objects.filter(user=user).first()
    if not device:
        raise ValidationError("No MFA setup in progress. Start setup first.")

    totp = pyotp.TOTP(device.secret)
    if not totp.verify(code, valid_window=1):
        raise ValidationError("Invalid code. Please try again.")

    device.is_enabled = True
    device.enabled_at = timezone.now()
    device.save(update_fields=["is_enabled", "enabled_at"])

    return True


def disable_mfa(user):
    MFADevice.objects.filter(user=user).delete()
    return True


def get_mfa_status(user):
    device = MFADevice.objects.filter(user=user).first()
    return {"enabled": bool(device and device.is_enabled)}


# ── MFA-aware login ─────────────────────────────────────────────

def verify_login_otp(identifier, otp):
    """
    Verifies the primary OTP. For admin/super_admin with MFA enabled,
    tokens are withheld and mfa_required=True is returned instead —
    the frontend must then call verify_mfa_login() to finish.
    """
    user = _get_user_by_identifier(identifier)

    if user.is_blocked:
        raise ValidationError("Your account has been blocked. Contact support.")

    verify_otp(
        user=user,
        purpose=OTP.Purpose.LOGIN,
        otp_code=otp,
    )

    requires_mfa = (
        user.role in ("admin", "super_admin")
        and MFADevice.objects.filter(user=user, is_enabled=True).exists()
    )

    if requires_mfa:
        return {"mfa_required": True, "identifier": identifier}

    tokens = _issue_tokens(user)
    return {"mfa_required": False, "tokens": tokens}


def verify_mfa_login(identifier, code):
    """
    Second step for MFA-enabled admins — verifies the TOTP code and
    issues tokens. Only reachable after verify_login_otp already
    confirmed the primary OTP, so this doesn't re-check password/OTP.
    """
    user = _get_user_by_identifier(identifier)

    device = MFADevice.objects.filter(user=user, is_enabled=True).first()
    if not device:
        raise ValidationError("MFA is not enabled for this account.")

    totp = pyotp.TOTP(device.secret)
    if not totp.verify(code, valid_window=1):
        raise ValidationError("Invalid authentication code.")

    return _issue_tokens(user)

