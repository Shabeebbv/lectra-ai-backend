import pytest
from apps.lectures.models import Lecture, Transcript
from apps.lectures.tasks import process_lecture_task

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def mock_pipeline_steps(mocker, lecture):
    """
    Patches every external step process_lecture_task calls, so this file
    tests only the task's own control flow (status transitions, error
    isolation) without touching S3, ffmpeg, Whisper, ChromaDB, Groq, or the
    real WebSocket channel layer.
    """
    Transcript.objects.get_or_create(lecture=lecture, defaults={"content": "mock transcript"})

    return {
        "download": mocker.patch("apps.lectures.tasks._download_file", return_value="/tmp/video.mp4"),
        "extract": mocker.patch("apps.lectures.tasks.extract_audio", return_value="/tmp/audio.mp3"),
        "transcript": mocker.patch("apps.lectures.tasks.generate_transcript"),
        "split": mocker.patch("apps.lectures.tasks.split_transcript", return_value=["chunk"]),
        "store": mocker.patch("apps.lectures.tasks.store_chunks"),
        "notes": mocker.patch("apps.lectures.tasks.generate_notes"),
        "timeline": mocker.patch("apps.lectures.tasks.generate_timeline"),
        "notify": mocker.patch("apps.lectures.tasks.send_notification"),
        "push_status": mocker.patch("apps.lectures.tasks._push_status"),
        "os_remove": mocker.patch("apps.lectures.tasks.os.remove"),
        "os_path_exists": mocker.patch("apps.lectures.tasks.os.path.exists", return_value=True),
    }


class TestProcessLectureTaskSuccess:
    def test_completes_and_pushes_status_at_each_step(self, lecture, mock_pipeline_steps):
        process_lecture_task(lecture.id)

        lecture.refresh_from_db()
        assert lecture.status == Lecture.Status.COMPLETED
        assert mock_pipeline_steps["push_status"].call_count >= 3  # processing, transcribing, completed

    def test_notification_failure_does_not_fail_the_lecture(self, lecture, mock_pipeline_steps):
        mock_pipeline_steps["notify"].side_effect = Exception("SQS down")

        process_lecture_task(lecture.id)

        lecture.refresh_from_db()
        assert lecture.status == Lecture.Status.COMPLETED

    def test_timeline_failure_does_not_fail_the_lecture(self, lecture, mock_pipeline_steps):
        mock_pipeline_steps["timeline"].side_effect = Exception("LLM returned garbage")

        process_lecture_task(lecture.id)

        lecture.refresh_from_db()
        assert lecture.status == Lecture.Status.COMPLETED


class TestProcessLectureTaskFailure:
    def test_marks_failed_and_reraises_on_core_step_error(self, lecture, mock_pipeline_steps):
        mock_pipeline_steps["transcript"].side_effect = RuntimeError("whisper crashed")

        with pytest.raises(RuntimeError):
            process_lecture_task(lecture.id)

        lecture.refresh_from_db()
        assert lecture.status == Lecture.Status.FAILED

    def test_missing_lecture_does_not_raise(self, mock_pipeline_steps):
        process_lecture_task(999999)  # no such lecture id — should log and return quietly