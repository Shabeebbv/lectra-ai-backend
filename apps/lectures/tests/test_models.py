import pytest
from apps.lectures.models import (
    Lecture, Transcript, LectureNote, TutorMessage, Notification, TimelineHighlight
)

pytestmark = pytest.mark.django_db


class TestLectureModel:
    def test_create_lecture_defaults_to_pending(self, lecture):
        assert lecture.status == Lecture.Status.PENDING

    def test_str_returns_title(self, lecture):
        assert str(lecture) == "Intro to Testing"


class TestTranscriptModel:
    def test_create_transcript_with_segments(self, lecture):
        transcript = Transcript.objects.create(
            lecture=lecture,
            content="Hello world",
            segments=[{"start": 0.0, "end": 1.5, "text": "Hello world"}],
        )
        assert transcript.segments[0]["text"] == "Hello world"

    def test_segments_defaults_to_empty_list(self, lecture):
        transcript = Transcript.objects.create(lecture=lecture, content="x")
        assert transcript.segments == []

    def test_one_to_one_enforced(self, lecture):
        Transcript.objects.create(lecture=lecture, content="first")
        with pytest.raises(Exception):
            Transcript.objects.create(lecture=lecture, content="second")


class TestLectureNoteModel:
    def test_create_note_accessible_via_reverse_relation(self, lecture):
        LectureNote.objects.create(lecture=lecture, content="Sample notes")
        assert lecture.notes.content == "Sample notes"


class TestTutorMessageModel:
    def test_ordering_is_chronological(self, lecture):
        m1 = TutorMessage.objects.create(lecture=lecture, question="Q1", answer="A1")
        m2 = TutorMessage.objects.create(lecture=lecture, question="Q2", answer="A2")
        assert list(lecture.tutor_messages.all()) == [m1, m2]


class TestNotificationModel:
    def test_defaults_unread(self, lecture):
        n = Notification.objects.create(user=lecture.user, lecture=lecture, title="Done", body="Ready")
        assert n.is_read is False

    def test_ordering_newest_first(self, lecture):
        Notification.objects.create(user=lecture.user, title="First", body="x")
        second = Notification.objects.create(user=lecture.user, title="Second", body="y")
        assert Notification.objects.filter(user=lecture.user).first() == second

    def test_lecture_deletion_sets_null_not_cascade(self, lecture):
        n = Notification.objects.create(user=lecture.user, lecture=lecture, title="t", body="b")
        lecture.delete()
        n.refresh_from_db()
        assert n.lecture_id is None


class TestTimelineHighlightModel:
    def test_defaults_to_concept_type(self, lecture):
        h = TimelineHighlight.objects.create(
            lecture=lecture, start_time=0, end_time=60, title="Intro", description="Overview"
        )
        assert h.highlight_type == TimelineHighlight.HighlightType.CONCEPT
        assert h.equation == ""

    def test_ordering_by_start_time(self, lecture):
        second = TimelineHighlight.objects.create(lecture=lecture, start_time=100, end_time=150, title="Second", description="d")
        first = TimelineHighlight.objects.create(lecture=lecture, start_time=0, end_time=50, title="First", description="d")
        assert list(lecture.timeline_highlights.all()) == [first, second]