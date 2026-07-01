from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import os

from .models import Lecture
from .services import extract_audio, generate_notes, generate_transcript
from .utils import _download_file
from .ai_services import split_transcript, store_chunks


def _push_status(lecture):
    """
    Push this lecture's current status to its owner via WebSocket.
    Celery is synchronous; async_to_sync bridges to the async channel layer.
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


@shared_task
def process_lecture_task(lecture_id):
    video_tmp = None
    audio_tmp = None

    try:
        lecture = Lecture.objects.get(id=lecture_id)

        lecture.status = Lecture.Status.PROCESSING
        lecture.save()
        _push_status(lecture)

        video_tmp = _download_file(lecture.video_file, suffix=".mp4")
        audio_tmp = extract_audio(video_tmp)

        os.remove(video_tmp)
        video_tmp = None

        # Push "transcribing" so the frontend shows the Whisper step
        # distinctly from the earlier download/audio-extraction step.
        lecture.status = Lecture.Status.TRANSCRIBING
        lecture.save()
        _push_status(lecture)

        generate_transcript(lecture, audio_tmp)

        chunks = split_transcript(lecture.transcript.content)
        store_chunks(lecture.id, chunks)

        generate_notes(lecture)

        lecture.status = Lecture.Status.COMPLETED
        lecture.save()
        _push_status(lecture)

    except Lecture.DoesNotExist:
        pass

    except Exception:
        lecture.status = Lecture.Status.FAILED
        lecture.save()
        _push_status(lecture)
        raise

    finally:
        if video_tmp and os.path.exists(video_tmp):
            os.remove(video_tmp)
        if audio_tmp and os.path.exists(audio_tmp):
            os.remove(audio_tmp)