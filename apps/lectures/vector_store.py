import chromadb

from django.conf import settings

from chromadb.utils.embedding_functions import (
    SentenceTransformerEmbeddingFunction
)


embedding_function = (
    SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
)


client = chromadb.HttpClient(
    host=settings.CHROMA_HOST,
    port=settings.CHROMA_PORT,
)
 
collection = client.get_or_create_collection(
    name="lecture_chunks"
)