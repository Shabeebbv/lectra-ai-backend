from celery import shared_task
from .models import Lecture


@shared_task
def process_lecture_task(lecture_id):

    lecture = Lecture.objects.get(
        id=lecture_id
    )

    lecture.status = Lecture.Status.PROCESSING
    lecture.save()

    # future:
    # extract audio
    # speech to text
    # generate notes

    lecture.status = Lecture.Status.COMPLETED
    lecture.save()