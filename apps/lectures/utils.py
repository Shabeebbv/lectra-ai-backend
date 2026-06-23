import tempfile

import requests

import boto3
from django.conf import settings


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
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
    )
    
def _download_file(url, suffix=".mp4"):
    """Download a file from URL to a local temp file."""
    response = requests.get(url, timeout=120)
    response.raise_for_status()

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(response.content)
    tmp.close()

    return tmp.name
    
    
def _upload_to_s3(local_path, s3_key):
    """Upload a local file to S3 and return its public URL."""
    s3 = get_s3_client()
    s3.upload_file(local_path, settings.AWS_STORAGE_BUCKET_NAME, s3_key)

    return (
        f"https://{settings.AWS_STORAGE_BUCKET_NAME}"
        f".s3.{settings.AWS_REGION}.amazonaws.com/{s3_key}"
    )


def _delete_from_s3(file_url):
    """Delete a file from S3 using its public URL."""
    key = file_url.split(
        f"{settings.AWS_STORAGE_BUCKET_NAME}"
        f".s3.{settings.AWS_REGION}.amazonaws.com/"
    )[-1]

    s3 = get_s3_client()
    s3.delete_object(
        Bucket=settings.AWS_STORAGE_BUCKET_NAME,
        Key=key
    )