from django.conf import settings
from django.core.mail import send_mail


def send_otp_email(email, otp):

    send_mail(
        subject="Your Lectra AI OTP",
        message=f"Your OTP is {otp}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )