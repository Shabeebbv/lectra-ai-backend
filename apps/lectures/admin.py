from django.contrib import admin
from .models import Lecture,Transcript,LectureNote

admin.site.register(Lecture)
admin.site.register(Transcript)
admin.site.register(LectureNote)