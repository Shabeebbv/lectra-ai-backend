import tempfile
import requests
import boto3
from botocore.config import Config

from urllib.parse import urlparse, unquote
from django.conf import settings
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

ALLOWED_EXTENSIONS = ['mp4', 'mov', 'avi', 'mkv', 'webm']

ALLOWED_VIDEO_TYPES = {
    'mp4':  'video/mp4',
    'mov':  'video/quicktime',
    'avi':  'video/x-msvideo',
    'mkv':  'video/x-matroska',
    'webm': 'video/webm',
}


def get_s3_client():
    return boto3.client(
        "s3",
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        endpoint_url=f"https://s3.{settings.AWS_REGION}.amazonaws.com",
        config=Config(
            signature_version="s3v4",
            s3={"addressing_style": "virtual"},
        ),
    )


def _key_from_url(file_url):
    """
    Extract the real S3 object key from a stored video_file URL.

    video_file is saved percent-encoded (e.g. %20 for spaces) so it passes
    Django's URLField validation. The actual object in S3 is named with the
    raw, decoded characters — so the path must be unquoted before being used
    as a Key in any boto3 call, or lookups will silently miss.
    """
    parsed = urlparse(file_url)
    return unquote(parsed.path.lstrip("/"))


def _download_file(file_url, suffix=".mp4"):
    """
    Download a lecture video from S3 to a local temp file.

    The bucket is private, so a plain unauthenticated GET against video_file
    (its bare HTTPS URL) returns 403 — there's no plain "object_url" field
    storing a presigned/public link, only the permanent S3 URL. Using boto3's
    own download_file() instead authenticates with the same credentials the
    rest of the app already uses, with no separate presigning step needed.
    """
    key = _key_from_url(file_url)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.close()

    s3 = get_s3_client()
    s3.download_file(
        settings.AWS_STORAGE_BUCKET_NAME,
        key,
        tmp.name,
    )

    return tmp.name


def _upload_to_s3(local_path, s3_key):
    """Upload local file to S3, return public URL."""
    s3 = get_s3_client()
    s3.upload_file(
        local_path,
        settings.AWS_STORAGE_BUCKET_NAME,
        s3_key
    )

    return (
        f"https://{settings.AWS_STORAGE_BUCKET_NAME}"
        f".s3.{settings.AWS_REGION}.amazonaws.com/{s3_key}"
    )


def _delete_from_s3(file_url):
    """Delete file from S3 using its stored URL."""
    key = _key_from_url(file_url)

    s3 = get_s3_client()
    s3.delete_object(
        Bucket=settings.AWS_STORAGE_BUCKET_NAME,
        Key=key
    )
    
    
    
 
def _push_status(lecture):
    print(f"Sending {lecture.status} to user_{lecture.user_id}")

    """
    Send this lecture's current status to its owner over WebSocket.
 
    Celery tasks run synchronously, but the channel layer's API is async —
    async_to_sync bridges that, the same way Channels' own consumers do
    internally for database_sync_to_async.
    """
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_{lecture.user_id}",
        {
            "type": "lecture_status_update",
            "lecture_id": lecture.id,
            "status": lecture.status,
        },
    )
 