import os
import uuid
import tempfile
import subprocess
from urllib.parse import quote
import json
import logging
import re
from groq import Groq
from amqp import NotFound
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from django.conf import settings
from .llm import llm
from .models import Lecture, Transcript, LectureNote ,TimelineHighlight
from .utils import get_s3_client, ALLOWED_VIDEO_TYPES, _download_file, _delete_from_s3,_key_from_url

logger = logging.getLogger(__name__)

groq_client = Groq(
    api_key=settings.GROQ_API_KEY
)

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
    """
    Extract compressed mono audio from a lecture video.

    The audio is optimized for speech transcription:
    - mono
    - 16 kHz
    - 32 kbps MP3

    This keeps uploads to the transcription API small.
    """

    audio_tmp = tempfile.mktemp(suffix=".mp3")

    try:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i", video_tmp_path,
                "-vn",
                "-ac", "1",
                "-ar", "16000",
                "-b:a", "32k",
                audio_tmp,
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        return audio_tmp

    except subprocess.CalledProcessError as exc:
        logger.error(
            "FFmpeg audio extraction failed: %s",
            exc.stderr,
        )

        if os.path.exists(audio_tmp):
            os.remove(audio_tmp)

        raise


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
    
    
    
#timeline 

timeline_prompt = PromptTemplate.from_template("""
You are an expert lecture analyst. Below is a lecture transcript broken into
timestamped segments (seconds).

Group these into 4 to 8 chronological "timeline highlights" that summarize the
key moments of the lecture. Do not create a highlight per segment — merge
related segments into meaningful chunks.

Return ONLY a JSON array, no other text, no markdown code fences, in exactly
this shape:
[
  {{
    "start_time": <integer seconds>,
    "end_time": <integer seconds>,
    "title": "<short title, max 8 words>",
    "description": "<2-3 sentence description>",
    "tags": ["<tag1>", "<tag2>"],
    "type": "concept" or "equation",
    "equation": "<only if type is equation, else null>"
  }}
]

Timestamped segments:
{segments}

JSON output:
""")

timeline_chain = timeline_prompt | llm | StrOutputParser()


def generate_transcript(lecture, audio_path):
    """
    Transcribe lecture audio using Groq-hosted Whisper.

    Stores:
    - full transcript text
    - timestamped segments for timeline generation
    """

    logger.info(
        "Starting Groq transcription for lecture %s",
        lecture.id,
    )

    try:
        with open(audio_path, "rb") as audio_file:
            transcription = groq_client.audio.transcriptions.create(
                file=(
                    os.path.basename(audio_path),
                    audio_file,
                ),
                model="whisper-large-v3-turbo",
                response_format="verbose_json",
                timestamp_granularities=["segment"],
                temperature=0.0,
            )

        segments = []

        for segment in transcription.segments or []:

            if isinstance(segment, dict):
                start = segment.get("start", 0)
                end = segment.get("end", 0)
                text = segment.get("text", "")

            else:
                start = getattr(segment, "start", 0)
                end = getattr(segment, "end", 0)
                text = getattr(segment, "text", "")

            text = (text or "").strip()

            if not text:
                continue

            segments.append(
                {
                    "start": round(float(start), 2),
                    "end": round(float(end), 2),
                    "text": text,
                }
            )

        transcript_text = (
            getattr(transcription, "text", "") or ""
        ).strip()

        if not transcript_text:
            raise ValueError(
                "Groq returned an empty transcription."
            )

        Transcript.objects.create(
            lecture=lecture,
            content=transcript_text,
            segments=segments,
        )

        logger.info(
            "Groq transcription completed for lecture %s. "
            "%s segments generated.",
            lecture.id,
            len(segments),
        )

    except Exception:
        logger.exception(
            "Groq transcription failed for lecture %s",
            lecture.id,
        )
        raise


def _format_segments_for_prompt(segments):
    return "\n".join(f"[{seg['start']}-{seg['end']}] {seg['text']}" for seg in segments)


def generate_timeline(lecture):
    """Generate structured timeline highlights from transcript segments using the LLM."""

    segments = lecture.transcript.segments

    if not segments:
        logger.warning("No segments for lecture %s, skipping timeline generation", lecture.id)
        return

    raw_output = timeline_chain.invoke({
        "segments": _format_segments_for_prompt(segments)
    })

    cleaned = re.sub(r"^```(json)?|```$", "", raw_output.strip(), flags=re.MULTILINE).strip()

    try:
        highlights = json.loads(cleaned)
    except json.JSONDecodeError:
        logger.exception("Failed to parse timeline JSON for lecture %s", lecture.id)
        return

    TimelineHighlight.objects.filter(lecture=lecture).delete()

    for h in highlights:
        TimelineHighlight.objects.create(
            lecture=lecture,
            start_time=h.get("start_time", 0),
            end_time=h.get("end_time", 0),
            title=(h.get("title") or "")[:255],
            description=h.get("description", ""),
            tags=h.get("tags", []),
            highlight_type=(
                TimelineHighlight.HighlightType.EQUATION
                if h.get("type") == "equation"
                else TimelineHighlight.HighlightType.CONCEPT
            ),
            equation=h.get("equation") or "",
        )


def get_lecture_video_url(user, lecture_id):

    try:
        lecture = Lecture.objects.get(
            id=lecture_id,
            user=user,
        )

    except Lecture.DoesNotExist:
        raise NotFound(
            "Lecture not found."
        )

    key = _key_from_url(
        lecture.video_file
    )

    s3 = get_s3_client()

    video_url = s3.generate_presigned_url(
        ClientMethod="get_object",
        Params={
            "Bucket": settings.AWS_STORAGE_BUCKET_NAME,
            "Key": key,
        },
        ExpiresIn=3600,
    )

    return {
        "video_url": video_url
    }