from .models import OTP
from .utils import generate_otp, otp_expiry_time
from .selectors import get_active_otp
from rest_framework.exceptions import ValidationError
from .selectors import get_active_otp

def create_otp(user, purpose):

    old_otp = get_active_otp(user, purpose)

    if old_otp and not old_otp.is_expired():
        old_otp.delete()

    otp = OTP.objects.create(
        user=user,
        otp_code=generate_otp(),
        purpose=purpose,
        expires_at=otp_expiry_time()
    )

    return otp



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