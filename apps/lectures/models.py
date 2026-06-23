from django.db import models
from django.conf import settings


class Lecture(models.Model):

    class Status(models.TextChoices):
        PENDING    = "pending",    "Pending"
        PROCESSING = "processing", "Processing"
        TRANSCRIBING = "transcribing", "Transcribing"
        COMPLETED  = "completed",  "Completed"
        FAILED     = "failed",     "Failed"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="lectures"
    )
    title      = models.CharField(max_length=255)
    video_file = models.URLField(max_length=500)       

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Transcript(models.Model):

    lecture = models.OneToOneField(
        Lecture,
        on_delete=models.CASCADE,
        related_name="transcript"
    )
    content    = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.lecture.title


class LectureNote(models.Model):

    lecture = models.OneToOneField(
        Lecture,
        on_delete=models.CASCADE,
        related_name="notes"
    )
    content    = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.lecture.title