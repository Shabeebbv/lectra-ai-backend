from .models import OTP
from .utils import generate_otp, otp_expiry_time
from .selectors import get_active_otp
from rest_framework.exceptions import ValidationError
from .selectors import get_active_otp
from django.contrib.auth import get_user_model,authenticate
from .sms import send_otp_sms
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.hashers import check_password

User=get_user_model()


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





def register_user(phone_number, password):

    existing_user = User.objects.filter(
        phone_number=phone_number
    ).first()   

    if existing_user:

        if existing_user.is_verified:
            raise ValidationError("User already exists")

        otp = create_otp(
            existing_user,
            OTP.Purpose.REGISTER
        )

        send_otp_sms(
            existing_user.phone_number,
            otp.otp_code
        )

        return existing_user

    user = User.objects.create_user(
        phone_number=phone_number,
        password=password,
        is_verified=False
    )

    otp = create_otp(user, OTP.Purpose.REGISTER)

    send_otp_sms(user.phone_number, otp.otp_code)

    return user




def verify_register_otp(phone_number, otp_code):

    try:
        user = User.objects.get(phone_number=phone_number)

    except User.DoesNotExist:
        raise ValidationError("User not found")

    verify_otp(
        user=user,
        purpose=OTP.Purpose.REGISTER,
        otp_code=otp_code
    )

    user.is_verified = True
    user.save()

    refresh = RefreshToken.for_user(user)

    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }   
    
    
    
    
    
def login_user(phone_number, password):

    user = authenticate(
        phone_number=phone_number,
        password=password
    )

    if not user:
        raise ValidationError("Invalid credentials")

    if not user.is_verified:
        raise ValidationError("Account is not verified")

    refresh = RefreshToken.for_user(user)

    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }
    
    
    
    
def forgot_password(phone_number):

    try:
        user = User.objects.get(phone_number=phone_number)

    except User.DoesNotExist:
        raise ValidationError("User not found")

    otp = create_otp(
        user=user,
        purpose=OTP.Purpose.FORGOT_PASSWORD
    )

    send_otp_sms(user.phone_number, otp.otp_code)

    return True


def reset_password(phone_number, otp_code, password):

    try:
        user = User.objects.get(phone_number=phone_number)

    except User.DoesNotExist:
        raise ValidationError("User not found")

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
        token = RefreshToken(refresh_token)

        token.blacklist()

    except Exception:
        raise ValidationError("Invalid token")

    return True



def resend_otp(phone_number):

    try:
        user = User.objects.get(phone_number=phone_number)

    except User.DoesNotExist:
        raise ValidationError("User not found")

    otp = get_active_otp(
        user=user,
        purpose=OTP.Purpose.REGISTER
    )

    if otp:

        if otp.last_resent_at:

            cooldown = otp.last_resent_at + timedelta(seconds=30)

            if timezone.now() < cooldown:
                raise ValidationError(
                    "Please wait before requesting another OTP"
                )

        otp.delete()

    new_otp = create_otp(
        user=user,
        purpose=OTP.Purpose.REGISTER
    )

    new_otp.resend_count += 1
    new_otp.last_resent_at = timezone.now()
    new_otp.save()

    send_otp_sms(user.phone_number, new_otp.otp_code)

    return True