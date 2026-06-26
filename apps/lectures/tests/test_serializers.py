from django.test import TestCase

from lectures.serializers import (
    GenerateUploadURLSerializer
)


class GenerateUploadURLSerializerTest(TestCase):

    def test_valid_filename(self):
        serializer = GenerateUploadURLSerializer(
            data={
                "filename": "lecture.mp4"
            }
        )

        self.assertTrue(serializer.is_valid())

    def test_invalid_filename(self):
        serializer = GenerateUploadURLSerializer(
            data={
                "filename": "lecture.exe"
            }
        )

        self.assertFalse(serializer.is_valid())