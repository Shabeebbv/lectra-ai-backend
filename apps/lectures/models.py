from django.db import models
from django.conf import settings


from django.core.exceptions import ValidationError


def validate_video(value):
    allowed = [".mp4", ".avi", ".mov"]

    if not any(value.name.endswith(ext) for ext in allowed):
        raise ValidationError("Only video files allowed")
    
    
class Lecture(models.Model):

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="lectures"
    )

    title = models.CharField(max_length=255)

    video_file = models.FileField(
        upload_to="lectures/videos/",
        validators=[validate_video]
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )
    
    audio_file = models.FileField(
    upload_to="lectures/audio/",
    null=True,
    blank=True
)

    def __str__(self):
        return self.title