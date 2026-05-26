from twilio.rest import Client

from django.conf import settings


client = Client(
    settings.TWILIO_ACCOUNT_SID,
    settings.TWILIO_AUTH_TOKEN
)


def send_otp_sms(phone_number, otp):

    try:
        message = client.messages.create(
            body=f"Your Lectra AI OTP is: {otp}",
            from_=settings.TWILIO_PHONE_NUMBER,
            to=phone_number
        )

        return message.sid

    except Exception as e:
        print("TWILIO ERROR:", e)
        raise