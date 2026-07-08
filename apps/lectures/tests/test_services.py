import pytest
from apps.lectures.models import Lecture, Transcript, LectureNote, TimelineHighlight
from apps.lectures import services

pytestmark = pytest.mark.django_db


class TestCreateLecture:
    def test_creates_lecture_and_queues_task(self, create_user, mocker):
        # process_lecture_task is imported locally inside create_lecture,
        # so it must be patched at its source module (apps.lectures.tasks),
        # not on the services module itself.
        mock_task = mocker.patch("apps.lectures.tasks.process_lecture_task")

        user = create_user(email="c@c.com")
        lecture = services.create_lecture(user=user, title="New Lecture", video_file="https://x/video.mp4")

        assert lecture.status == Lecture.Status.PENDING
        mock_task.delay.assert_called_once_with(lecture.id)


class TestExtractAudio:
    def test_calls_ffmpeg_and_returns_mp3_path(self, mocker):
        mock_run = mocker.patch("apps.lectures.services.subprocess.run")

        result = services.extract_audio("/tmp/video.mp4")

        assert result.endswith(".mp3")
        args = mock_run.call_args[0][0]
        assert args[0] == "ffmpeg"
        assert "/tmp/video.mp4" in args


class TestGenerateTranscript:
    def test_saves_content_and_rounded_segments(self, lecture, mocker):
        mock_whisper = mocker.patch("apps.lectures.services.whisper_model")
        mock_whisper.transcribe.return_value = {
            "text": "full transcript text",
            "segments": [{"start": 0.001, "end": 2.005, "text": "  Hello  "}],
        }

        services.generate_transcript(lecture, "/tmp/audio.mp3")

        transcript = Transcript.objects.get(lecture=lecture)
        assert transcript.content == "full transcript text"
        assert transcript.segments[0] == {"start": 0.0, "end": 2.0, "text": "Hello"}

    def test_handles_missing_segments_key(self, lecture, mocker):
        mock_whisper = mocker.patch("apps.lectures.services.whisper_model")
        mock_whisper.transcribe.return_value = {"text": "text only"}

        services.generate_transcript(lecture, "/tmp/audio.mp3")

        assert Transcript.objects.get(lecture=lecture).segments == []


class TestGenerateNotes:
    def test_creates_note_from_transcript(self, lecture, mocker):
        Transcript.objects.create(lecture=lecture, content="lecture content here")
        mock_chain = mocker.patch("apps.lectures.services.notes_chain")
        mock_chain.invoke.return_value = "## Summary\nGenerated notes"

        services.generate_notes(lecture)

        note = LectureNote.objects.get(lecture=lecture)
        assert note.content == "## Summary\nGenerated notes"
        mock_chain.invoke.assert_called_once_with({"transcript": "lecture content here"})


class TestDeleteLecture:
    def test_deletes_s3_chroma_and_db_row(self, lecture, mocker):
        mock_delete_s3 = mocker.patch("apps.lectures.services._delete_from_s3")
        mock_collection = mocker.patch("apps.lectures.vector_store.collection")
        lecture_id = lecture.id
        video_file = lecture.video_file

        services.delete_lecture(lecture)

        mock_delete_s3.assert_called_once_with(video_file)
        mock_collection.delete.assert_called_once_with(where={"lecture_id": str(lecture_id)})
        assert not Lecture.objects.filter(id=lecture_id).exists()

    def test_skips_s3_delete_when_no_video_file(self, lecture, mocker):
        lecture.video_file = ""
        lecture.save()
        mock_delete_s3 = mocker.patch("apps.lectures.services._delete_from_s3")
        mocker.patch("apps.lectures.vector_store.collection")

        services.delete_lecture(lecture)

        mock_delete_s3.assert_not_called()


class TestGeneratePresignedUrl:
    def test_returns_upload_and_encoded_file_url(self, mocker, settings):
        settings.AWS_STORAGE_BUCKET_NAME = "mybucket"
        settings.AWS_REGION = "ap-south-1"

        mock_s3 = mocker.MagicMock()
        mock_s3.generate_presigned_url.return_value = "https://presigned.example.com/put"
        mocker.patch("apps.lectures.services.get_s3_client", return_value=mock_s3)

        result = services.generate_presigned_url("My Lecture.mp4")

        assert result["upload_url"] == "https://presigned.example.com/put"
        assert result["content_type"] == "video/mp4"
        assert "My%20Lecture.mp4" in result["file_url"]
        assert result["file_url"].startswith("https://mybucket.s3.ap-south-1.amazonaws.com/")


class TestGenerateTimeline:
    def test_skips_when_no_segments(self, lecture):
        Transcript.objects.create(lecture=lecture, content="text", segments=[])
        services.generate_timeline(lecture)
        assert TimelineHighlight.objects.filter(lecture=lecture).count() == 0

    def test_creates_highlights_from_valid_json(self, lecture, mocker):
        Transcript.objects.create(lecture=lecture, content="text", segments=[{"start": 0, "end": 10, "text": "intro"}])
        mock_chain = mocker.patch("apps.lectures.services.timeline_chain")
        mock_chain.invoke.return_value = (
            '[{"start_time": 0, "end_time": 10, "title": "Intro", "description": "Overview", '
            '"tags": ["intro"], "type": "concept"}]'
        )

        services.generate_timeline(lecture)

        highlight = TimelineHighlight.objects.get(lecture=lecture)
        assert highlight.title == "Intro"
        assert highlight.highlight_type == TimelineHighlight.HighlightType.CONCEPT

    def test_strips_markdown_code_fences_before_parsing(self, lecture, mocker):
        Transcript.objects.create(lecture=lecture, content="text", segments=[{"start": 0, "end": 5, "text": "hi"}])
        mock_chain = mocker.patch("apps.lectures.services.timeline_chain")
        mock_chain.invoke.return_value = (
            '```json\n[{"start_time": 0, "end_time": 5, "title": "A", "description": "d", '
            '"tags": [], "type": "equation", "equation": "E=mc^2"}]\n```'
        )

        services.generate_timeline(lecture)

        highlight = TimelineHighlight.objects.get(lecture=lecture)
        assert highlight.highlight_type == TimelineHighlight.HighlightType.EQUATION
        assert highlight.equation == "E=mc^2"

    def test_replaces_existing_highlights_rather_than_appending(self, lecture, mocker):
        Transcript.objects.create(lecture=lecture, content="text", segments=[{"start": 0, "end": 5, "text": "hi"}])
        TimelineHighlight.objects.create(lecture=lecture, start_time=0, end_time=5, title="Old", description="old")

        mock_chain = mocker.patch("apps.lectures.services.timeline_chain")
        mock_chain.invoke.return_value = '[{"start_time": 0, "end_time": 5, "title": "New", "description": "d", "tags": [], "type": "concept"}]'

        services.generate_timeline(lecture)

        highlights = TimelineHighlight.objects.filter(lecture=lecture)
        assert highlights.count() == 1
        assert highlights.first().title == "New"

    def test_handles_malformed_json_without_raising(self, lecture, mocker):
        Transcript.objects.create(lecture=lecture, content="text", segments=[{"start": 0, "end": 5, "text": "hi"}])
        mock_chain = mocker.patch("apps.lectures.services.timeline_chain")
        mock_chain.invoke.return_value = "not valid json at all"

        services.generate_timeline(lecture)  # should not raise

        assert TimelineHighlight.objects.filter(lecture=lecture).count() == 0