import pytest
from apps.lectures.serializers import (
    LectureCreateSerializer,
    LectureDetailSerializer,
    GenerateUploadURLSerializer,
    NotificationSerializer,
    TimelineHighlightSerializer,
)
from apps.lectures.models import Transcript, LectureNote, Notification, TimelineHighlight

pytestmark = pytest.mark.django_db


class TestGenerateUploadURLSerializer:
    @pytest.mark.parametrize("filename", ["lecture.mp4", "class.MOV", "video.webm"])
    def test_allowed_extensions_pass(self, filename):
        assert GenerateUploadURLSerializer(data={"filename": filename}).is_valid()

    @pytest.mark.parametrize("filename", ["lecture.exe", "notes.pdf", "noext"])
    def test_disallowed_extensions_fail(self, filename):
        assert not GenerateUploadURLSerializer(data={"filename": filename}).is_valid()


class TestLectureCreateSerializer:
    def test_requires_title_and_video_file(self):
        serializer = LectureCreateSerializer(data={})
        assert not serializer.is_valid()
        assert "title" in serializer.errors
        assert "video_file" in serializer.errors


class TestLectureDetailSerializer:
    def test_transcript_and_notes_none_when_absent(self, lecture):
        data = LectureDetailSerializer(lecture).data
        assert data["transcript"] is None
        assert data["notes"] is None

    def test_transcript_and_notes_present(self, lecture):
        Transcript.objects.create(lecture=lecture, content="hello")
        LectureNote.objects.create(lecture=lecture, content="notes here")
        data = LectureDetailSerializer(lecture).data
        assert data["transcript"] == "hello"
        assert data["notes"] == "notes here"


class TestNotificationSerializer:
    def test_lecture_id_null_when_no_lecture(self, lecture):
        n = Notification.objects.create(user=lecture.user, title="t", body="b")
        assert NotificationSerializer(n).data["lecture_id"] is None

    def test_lecture_id_present(self, lecture):
        n = Notification.objects.create(user=lecture.user, lecture=lecture, title="t", body="b")
        assert NotificationSerializer(n).data["lecture_id"] == lecture.id


class TestTimelineHighlightSerializer:
    def test_serializes_expected_fields(self, lecture):
        h = TimelineHighlight.objects.create(lecture=lecture, start_time=10, end_time=20, title="t", description="d")
        assert set(TimelineHighlightSerializer(h).data.keys()) == {
            "id", "start_time", "end_time", "title", "description", "tags", "highlight_type", "equation"
        }