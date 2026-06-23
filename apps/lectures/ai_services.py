from langchain_text_splitters import RecursiveCharacterTextSplitter
from .vector_store import collection

def split_transcript(transcript_text):

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

    return splitter.split_text(
        transcript_text
    )




def store_chunks(
    lecture_id,
    chunks
):

    ids = []

    metadatas = []

    for i, chunk in enumerate(chunks):

        ids.append(
            f"{lecture_id}_{i}"
        )

        metadatas.append(
            {
                "lecture_id": lecture_id
            }
        )

    collection.add(
        documents=chunks,
        ids=ids,
        metadatas=metadatas
    )