import json
import logging

import boto3
from django.conf import settings

from apps.lectures.models import Notification

logger = logging.getLogger(__name__)

sqs = boto3.client(
    "sqs",
    region_name=settings.AWS_REGION,
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
)


def _build_message(lecture):
    """
    Builds the (title, body) text shown in the bell dropdown and in the
    browser push notification. Keep both short — push notifications
    truncate long bodies on most platforms.
    """
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
    """
    Creates the persistent Notification row (powers the bell icon) and,
    if the user has any registered FCM tokens, publishes an event to SQS
    for the Lambda function to deliver as a browser push notification.

    This function is called from process_lecture_task AFTER the lecture's
    real status has already been saved and pushed via WebSocket. Any
    exception raised here should be caught by the caller and logged, never
    allowed to affect the lecture's actual status.
    """
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