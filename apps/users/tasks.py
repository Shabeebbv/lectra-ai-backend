from celery import shared_task

from .sms import send_otp_sms


@shared_task(
    bind=True,
    max_retries=3
)
def send_otp_task(self, phone_number, otp):

    try:
        send_otp_sms(
            phone_number,
            otp
        )

    except Exception as exc:

        raise self.retry(exc=exc, countdown=5)