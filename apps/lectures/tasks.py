from celery import shared_task
from .models import Lecture
from .services import extract_audio, generate_transcript

@shared_task
def process_lecture_task(
    lecture_id
):

    lecture = Lecture.objects.get(
        id=lecture_id   
    )

    lecture.status = (
        Lecture.Status.PROCESSING
    )

    lecture.save()

    extract_audio(
        lecture
    )
    
    generate_transcript(
    lecture
)

    lecture.status = (
        Lecture.Status.COMPLETED
    )

    lecture.save()
    
    