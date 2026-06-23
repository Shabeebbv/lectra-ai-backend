import os
import uuid
import tempfile
import subprocess

import whisper

from django.conf import settings

from .models import Lecture, Transcript, LectureNote
from .utils import get_s3_client, ALLOWED_VIDEO_TYPES,_download_file, _upload_to_s3, _delete_from_s3

whisper_model = whisper.load_model("base")


# ── services ────────────────────────────────────────────────────

def create_lecture(user, title, video_file):
    lecture = Lecture.objects.create(
        user=user,
        title=title,
        video_file=video_file
    )

    from .tasks import process_lecture_task
    process_lecture_task.delay(lecture.id)

    return lecture


def extract_audio(video_tmp_path):
    """Extract audio from video file. Returns temp audio path."""
    audio_tmp = tempfile.mktemp(suffix=".mp3")

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i", video_tmp_path,
            "-vn",
            "-acodec", "mp3",
            audio_tmp
        ],
        capture_output=True,
        check=True
    )

    return audio_tmp


def generate_transcript(lecture, audio_path):
    result = whisper_model.transcribe(audio_path)

    Transcript.objects.create(
        lecture=lecture,
        content=result["text"]
    )


def generate_notes(lecture):
    """Generate AI notes from transcript using OpenAI."""
    transcript_text = lecture.transcript.content

    # TODO: replace with real OpenAI/Gemini call
    # import openai
    # response = openai.chat.completions.create(
    #     model="gpt-4",
    #     messages=[{
    #         "role": "user",
    #         "content": f"Generate structured notes from:\n{transcript_text}"
    #     }]
    # )
    # notes_content = response.choices[0].message.content

    notes_content = transcript_text  # placeholder until AI integrated

    LectureNote.objects.create(
        lecture=lecture,
        content=notes_content
    )


def delete_lecture(lecture):
    """Delete lecture and its files from S3."""
    # ✅ delete from S3 using boto3
    if lecture.video_file:
        _delete_from_s3(lecture.video_file)

    if lecture.audio_file:
        _delete_from_s3(lecture.audio_file)

    lecture.delete()


def generate_presigned_url(filename):
    s3  = get_s3_client()
    key = f"lectures/videos/{uuid.uuid4()}-{filename}"

    ext          = filename.rsplit('.', 1)[-1].lower()
    content_type = ALLOWED_VIDEO_TYPES.get(ext, 'video/mp4')

    upload_url = s3.generate_presigned_url(
        "put_object",
        Params={
            "Bucket":      settings.AWS_STORAGE_BUCKET_NAME,
            "Key":         key,
            "ContentType": content_type
        },
        ExpiresIn=3600
    )

    file_url = (
        f"https://{settings.AWS_STORAGE_BUCKET_NAME}"
        f".s3.{settings.AWS_REGION}.amazonaws.com/{key}"
    )

    return {
        "upload_url":   upload_url,
        "file_url":     file_url,
        "content_type": content_type
    }