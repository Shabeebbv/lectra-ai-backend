from celery import shared_task
from .models import Lecture
from .services import extract_audio, generate_notes, generate_transcript
import os
from .utils import _download_file
from .ai_services import (
    split_transcript,
    store_chunks
)

@shared_task
def process_lecture_task(lecture_id):
    video_tmp = None
    audio_tmp = None

    try:
        lecture = Lecture.objects.get(id=lecture_id)

        lecture.status = Lecture.Status.PROCESSING
        lecture.save()

        # 1. download video from S3 once
        video_tmp = _download_file(
            lecture.video_file,
            suffix=".mp4"
        )

        # 2. extract audio to temp file
        audio_tmp = extract_audio(video_tmp)

        # 3. delete video temp — no longer needed
        os.remove(video_tmp)
        video_tmp = None

        # 4. transcribe audio
        generate_transcript(lecture, audio_tmp)
        
        chunks = split_transcript(lecture.transcript.content)

        store_chunks(lecture.id, chunks)

        # 5. generate notes
        generate_notes(lecture)

        lecture.status = Lecture.Status.COMPLETED
        lecture.save()

    except Lecture.DoesNotExist:
        pass

    except Exception:
        lecture.status = Lecture.Status.FAILED
        lecture.save()
        raise

    finally:
        # always clean up whatever temp files exist
        if video_tmp and os.path.exists(video_tmp):
            os.remove(video_tmp)
        if audio_tmp and os.path.exists(audio_tmp):
            os.remove(audio_tmp)