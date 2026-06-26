import os

from celery import shared_task

from .models import Lecture
from .services import extract_audio, generate_transcript, generate_notes
from .utils import _download_file,_push_status
from .ai_services import split_transcript, store_chunks



@shared_task
def process_lecture_task(lecture_id):
    video_tmp = None
    audio_tmp = None

    try:
        lecture = Lecture.objects.get(id=lecture_id)

        lecture.status = Lecture.Status.PROCESSING
        lecture.save()
        _push_status(lecture)

        # 1. download video from S3
        video_tmp = _download_file(lecture.video_file, suffix=".mp4")

        # 2. extract audio to temp file
        audio_tmp = extract_audio(video_tmp)

        # 3. delete video temp — no longer needed
        os.remove(video_tmp)
        video_tmp = None

        # 4. transcribe audio
        generate_transcript(lecture, audio_tmp)

        # 5. chunk and store in ChromaDB
        chunks = split_transcript(lecture.transcript.content)
        store_chunks(lecture.id, chunks)

        # 6. generate notes
        generate_notes(lecture)

        lecture.status = Lecture.Status.COMPLETED
        lecture.save()
        _push_status(lecture)



    except Exception as e:
        lecture.status = Lecture.Status.FAILED
        lecture.save()
        _push_status(lecture)
        lecture.save()
        raise

    finally:
        if video_tmp and os.path.exists(video_tmp):
            os.remove(video_tmp)
        if audio_tmp and os.path.exists(audio_tmp):
            os.remove(audio_tmp)