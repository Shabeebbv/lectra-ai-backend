import json
import boto3

from django.conf import settings


sqs = boto3.client(
    "sqs",

    region_name=
    settings.AWS_REGION,

    aws_access_key_id=
    settings.AWS_ACCESS_KEY_ID,

    aws_secret_access_key=
    settings.AWS_SECRET_ACCESS_KEY,
)


def send_notification(
    lecture
):

    sqs.send_message(
        QueueUrl=
        settings.AWS_SQS_URL,

        MessageBody=
        json.dumps({

            "user_id":
                lecture.user.id,

            "lecture_id":
                lecture.id,

            "title":
                lecture.title,

            "status":
                lecture.status,
        })
    )
    
    