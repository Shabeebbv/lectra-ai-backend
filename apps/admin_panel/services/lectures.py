"""
Lectures Service
Business logic for admin lecture management.
"""

from rest_framework.exceptions import NotFound, ValidationError

from apps.lectures.models import Lecture
from apps.admin_panel.selectors.lectures import (
    get_all_lectures_queryset,
    get_lecture_by_id,
)

# TODO: confirm the actual Celery task name/path used for lecture processing.
# Guessing based on your described pipeline (S3 upload -> FFmpeg -> Whisper ->
# chunking -> Chroma). Adjust this import to match your real task.
from apps.lectures.tasks import process_lecture_task


RETRIABLE_STATUSES = [
    Lecture.Status.FAILED,
]


def list_lectures(search=None, status=None):
    return get_all_lectures_queryset(search=search, status=status)


def get_lecture_detail(lecture_id):
    lecture = get_lecture_by_id(lecture_id)
    if not lecture:
        raise NotFound("Lecture not found.")
    return lecture


def delete_lecture(lecture_id):
    """
    Hard-deletes a lecture. No soft-delete field exists on this model —
    this also cascades to Transcript, LectureNote, TutorMessage, and
    TimelineHighlight via their FKs. If you want this to be recoverable
    like Users, say so and I'll add is_deleted/deleted_at here too.
    """
    lecture = get_lecture_detail(lecture_id)
    lecture.delete()
    return True


def retry_lecture(lecture_id):
    """
    Resets a failed lecture to pending and re-queues processing.
    Only allowed for lectures currently in a failed state, to avoid
    accidentally re-triggering an in-progress or already-completed job.
    """
    lecture = get_lecture_detail(lecture_id)

    if lecture.status not in RETRIABLE_STATUSES:
        raise ValidationError(
            f"Only failed lectures can be retried. Current status: {lecture.status}"
        )

    lecture.status = Lecture.Status.PENDING
    lecture.save(update_fields=["status"])

    process_lecture_task.delay(lecture.id)

    return lecture