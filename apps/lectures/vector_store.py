import chromadb
from django.conf import settings

client = chromadb.PersistentClient(
    path=str(settings.CHROMA_DB_PATH)   
)

collection = client.get_or_create_collection(
    name="lecture_chunks"
)