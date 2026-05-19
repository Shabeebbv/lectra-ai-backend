from .models import OTP


def get_active_otp(user, purpose):

    return OTP.objects.filter(
        user=user,
        purpose=purpose,
        is_used=False
    ).order_by('-created_at').first()