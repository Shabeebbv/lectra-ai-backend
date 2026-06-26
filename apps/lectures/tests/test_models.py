from django.test import TestCase
from django.contrib.auth import get_user_model

from lectures.models import Lecture, Transcript, LectureNote

User = get_user_model()


class LectureModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            phone_number="9999999999",
            password="password123"
        )

    def test_create_lecture(self):
        lecture = Lecture.objects.create(
            user=self.user,
            title="Python Basics",
            video_file="https://example.com/video.mp4"
        )

        self.assertEqual(lecture.title, "Python Basics")
        self.assertEqual(
            lecture.status,
            Lecture.Status.PENDING
        )

    def test_create_transcript(self):
        lecture = Lecture.objects.create(
            user=self.user,
            title="Python",
            video_file="https://example.com/video.mp4"
        )

        transcript = Transcript.objects.create(
            lecture=lecture,
            content="Sample transcript"
        )

        self.assertEqual(
            transcript.content,
            "Sample transcript"
        )

    def test_create_note(self):
        lecture = Lecture.objects.create(
            user=self.user,
            title="Python",
            video_file="https://example.com/video.mp4"
        )

        note = LectureNote.objects.create(
            lecture=lecture,
            content="Sample notes"
        )

        self.assertEqual(
            note.content,
            "Sample notes"
        )