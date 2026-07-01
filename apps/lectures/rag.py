from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from .vector_store import collection
from .llm import llm


def retrieve_context(
    lecture_id: int,
    question: str,
    top_k: int = 3,
) -> str:
    """
    Retrieve the most relevant chunks
    from the vector database.
    """

    lecture_chunks = collection.get(where={"lecture_id": str(lecture_id)})
    chunk_ids = lecture_chunks.get("ids", [])

    if not chunk_ids:
        return ""

    safe_top_k = min(top_k, len(chunk_ids))

    results = collection.query(
        query_texts=[question],
        n_results=safe_top_k,
        ids=chunk_ids,
    )

    documents = results.get("documents", [[]])[0]

    return "\n\n".join(documents)


rag_prompt = PromptTemplate.from_template(
    """
You are an educational AI assistant.

Your task is to answer questions using ONLY the provided lecture context.

Rules:
1. Answer strictly from the provided context.
2. Do not make up or assume information.
3. If the answer is not present in the context, respond exactly with:
   "I could not find the answer in this lecture."
4. Keep the answer clear and concise.

Lecture Context:
{context}

Student Question:
{question}

Answer:
"""
)


rag_chain = (
    rag_prompt
    | llm
    | StrOutputParser()
)


def ask_question(
    lecture_id: int,
    question: str,
) -> str:
    """
    Retrieve context and generate
    an answer using RAG.
    """

    context = retrieve_context(
        lecture_id=lecture_id,
        question=question,
    )

    if not context:
        return "I could not find the answer in this lecture."

    answer = rag_chain.invoke(
        {
            "context": context,
            "question": question,
        }
    )

    return answer.strip()