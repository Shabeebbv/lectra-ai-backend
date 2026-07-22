import json
import logging

import boto3
from django.conf import settings

from apps.lectures.models import Notification

logger = logging.getLogger(__name__)

sqs = boto3.client(
    "sqs",
    region_name=settings.AWS_REGION,
)


def _build_message(lecture):

    if lecture.status == "completed":
        title = f"{lecture.title} is ready"
        body = "Your lecture has been transcribed and notes are ready to view."
    elif lecture.status == "failed":
        title = f"{lecture.title} failed to process"
        body = "Something went wrong while processing this lecture. Please try re-uploading."
    else:
        title = lecture.title
        body = f"Lecture status updated: {lecture.status}"

    return title, body


def send_notification(lecture):

    user = lecture.user
    title, body = _build_message(lecture)

    Notification.objects.create(
        user=user,
        lecture=lecture,
        title=title,
        body=body,
    )

    tokens = list(user.fcm_tokens.values_list("token", flat=True))
    if not tokens:
        logger.info(
            "No FCM tokens registered for user %s — skipping push, bell notification saved.",
            user.id,
        )
        return

    response = sqs.send_message(
        QueueUrl=settings.AWS_SQS_URL,
        MessageBody=json.dumps({
            "tokens": tokens,
            "title": title,
            "body": body,
        }),
    )
    logger.info("SQS message sent: %s", response.get("MessageId"))