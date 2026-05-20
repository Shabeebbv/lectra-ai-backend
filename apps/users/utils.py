import random
from django.utils import timezone
from datetime import timedelta
from rest_framework.response import Response

def generate_otp():
    return str(random.randint(100000, 999999))


def otp_expiry_time(minutes=5):
    return timezone.now() + timedelta(minutes=minutes)


def success_response(
    message="Success",
    data=None,
    status_code=200
):

    return Response(
        {
            "success": True,
            "message": message,
            "data": data
        },
        status=status_code
    )