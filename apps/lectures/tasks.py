import logging
import os

from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from .ai_services import split_transcript, store_chunks
from .models import Lecture
from .notification_service import send_notification
from .services import extract_audio, generate_notes, generate_transcript,generate_timeline
from .utils import _download_file
from apps.lectures.models import Notification

logger = logging.getLogger(__name__)


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
        
        try:
            generate_timeline(lecture)
        except Exception:
            logger.exception(
                "Failed to generate timeline for lecture %s (core processing succeeded)",
                lecture.id,
            )

        # --- Core pipeline is done. Mark completed and tell the frontend
        # immediately, BEFORE touching anything non-essential like
        # notifications. Nothing after this point should be able to flip
        # a successfully-processed lecture back to "failed".
        lecture.status = Lecture.Status.COMPLETED
        lecture.save()
        _push_status(lecture)

        # Notifications are best-effort. A failure here (bad AWS creds,
        # SQS down, missing FCM tokens, etc.) must never affect the
        # lecture's real status — the actual work already succeeded.
        try:
            send_notification(lecture)
        except Exception:
            logger.exception(
                "Failed to send notification for lecture %s (processing itself succeeded)",
                lecture.id,
            )

    except Lecture.DoesNotExist:
        logger.warning("process_lecture_task: Lecture %s does not exist", lecture_id)

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
            
            
@shared_task
def delete_old_notifications():
    """
    Deletes Notification rows older than NOTIFICATION_RETENTION_DAYS.
    Runs on a schedule via Celery Beat (see settings.CELERY_BEAT_SCHEDULE).
    """
    retention_days = getattr(settings, "NOTIFICATION_RETENTION_DAYS", 30)
    cutoff = timezone.now() - timedelta(days=retention_days)

    deleted_count, _ = Notification.objects.filter(created_at__lt=cutoff).delete()

    return f"Deleted {deleted_count} notifications older than {retention_days} days."

