import os
import uuid
import tempfile
import subprocess
from urllib.parse import quote

import whisper
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from django.conf import settings
from .llm import llm
from .models import Lecture, Transcript, LectureNote
from .utils import get_s3_client, ALLOWED_VIDEO_TYPES, _download_file, _delete_from_s3


whisper_model = whisper.load_model("tiny")

notes_prompt = PromptTemplate.from_template("""
You are an expert study assistant.
Generate clear, structured notes from the lecture transcript below.

Format your notes like this:
## Summary
(2-3 sentence overview of the lecture)

## Key Topics
(main topics covered as bullet points)

## Important Points
(detailed important points explained clearly)

## Key Terms
(important terms and their definitions)

## Quick Recap
(3-5 bullet points to remember)

Transcript:
{transcript}

Generate the notes now:
""")

notes_chain = notes_prompt | llm | StrOutputParser()


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
    """Extract audio from video. Returns temp audio path."""
    audio_tmp = tempfile.mktemp(suffix=".mp3")

    subprocess.run(
        [
            "ffmpeg", "-y",
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
    """Transcribe audio using Whisper and save to DB."""

    result = whisper_model.transcribe(audio_path)

    Transcript.objects.create(
        lecture=lecture,
        content=result["text"]
    )



def generate_notes(lecture):
    """Generate structured notes from transcript using Groq LLM."""

    transcript_text = lecture.transcript.content

    notes_content = notes_chain.invoke({
        "transcript": transcript_text
    })

    LectureNote.objects.create(
        lecture=lecture,
        content=notes_content
    )



def delete_lecture(lecture):
    """Delete lecture, video from S3, and chunks from ChromaDB."""
    if lecture.video_file:
        _delete_from_s3(lecture.video_file)

    from .vector_store import collection
    collection.delete(
        where={"lecture_id": str(lecture.id)}
    )

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

    encoded_key = quote(key, safe="/")

    file_url = (
        f"https://{settings.AWS_STORAGE_BUCKET_NAME}"
        f".s3.{settings.AWS_REGION}.amazonaws.com/{encoded_key}"
    )

    return {
        "upload_url":   upload_url,
        "file_url":     file_url,
        "content_type": content_type
    }