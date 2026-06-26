from unittest.mock import patch

from django.test import TestCase
from django.contrib.auth import get_user_model

from lectures.models import Lecture
from lectures.tasks import process_lecture_task

User = get_user_model()


class ProcessLectureTaskTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            phone_number="9999999999",
            password="password123"
        )

        self.lecture = Lecture.objects.create(
            user=self.user,
            title="Test",
            video_file="https://example.com/video.mp4"
        )

    @patch("lectures.tasks.generate_notes")
    @patch("lectures.tasks.store_chunks")
    @patch("lectures.tasks.split_transcript")
    @patch("lectures.tasks.generate_transcript")
    @patch("lectures.tasks.extract_audio")
    @patch("lectures.tasks._download_file")
    def test_process_lecture(
        self,
        mock_download,
        mock_extract,
        mock_transcript,
        mock_split,
        mock_store,
        mock_notes
    ):
        mock_download.return_value = "/tmp/video.mp4"
        mock_extract.return_value = "/tmp/audio.mp3"

        process_lecture_task(self.lecture.id)

        self.lecture.refresh_from_db()

        self.assertEqual(
            self.lecture.status,
            Lecture.Status.COMPLETED
        )