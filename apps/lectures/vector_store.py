import chromadb

from django.conf import settings

from chromadb.utils.embedding_functions import (
    SentenceTransformerEmbeddingFunction
)


_embedding_function = None
_client = None
_collection = None


def get_embedding_function():
    """
    Load the embedding model only when it is actually needed.
    This prevents Django startup/system checks from downloading
    or loading the SentenceTransformer model.
    """
    global _embedding_function

    if _embedding_function is None:
        _embedding_function = SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )

    return _embedding_function


def get_chroma_client():
    """
    Connect to Chroma only when vector storage is actually used.
    """
    global _client

    if _client is None:
        _client = chromadb.HttpClient(
            host=settings.CHROMA_HOST,
            port=settings.CHROMA_PORT,
        )

    return _client


def get_collection():
    """
    Get/create the lecture collection lazily.
    """
    global _collection

    if _collection is None:
        client = get_chroma_client()

        _collection = client.get_or_create_collection(
            name="lecture_chunks",
            embedding_function=get_embedding_function(),
        )

    return _collection