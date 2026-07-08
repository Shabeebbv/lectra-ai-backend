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
    segments   = models.JSONField(default=list, blank=True)  # [{start, end, text}, ...] from Whisper
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
    
    
class TutorMessage(models.Model):
    """
    One question-and-answer exchange with the AI Tutor for a given lecture.
    Ordered chronologically per lecture via created_at.
    """
 
    lecture = models.ForeignKey(
        Lecture,
        on_delete=models.CASCADE,
        related_name="tutor_messages"
    )
    question = models.TextField()
    answer = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        ordering = ["created_at"]
 
    def __str__(self):
        return f"{self.lecture.title} — {self.question[:50]}"
    
    
class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications"
    )
    lecture = models.ForeignKey(Lecture, null=True, blank=True, on_delete=models.SET_NULL)
    title = models.CharField(max_length=255)
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        
        
class TimelineHighlight(models.Model):

    class HighlightType(models.TextChoices):
        CONCEPT  = "concept",  "Concept"
        EQUATION = "equation", "Equation"

    lecture = models.ForeignKey(
        Lecture,
        on_delete=models.CASCADE,
        related_name="timeline_highlights"
    )
    start_time = models.PositiveIntegerField(help_text="Seconds from lecture start")
    end_time   = models.PositiveIntegerField(help_text="Seconds from lecture start")
    title       = models.CharField(max_length=255)
    description = models.TextField()
    tags        = models.JSONField(default=list, blank=True)
    highlight_type = models.CharField(
        max_length=20,
        choices=HighlightType.choices,
        default=HighlightType.CONCEPT
    )
    equation   = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["start_time"]

    def __str__(self):
        return f"{self.lecture.title} — {self.title}"