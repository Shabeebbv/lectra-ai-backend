from django.conf import settings
from langchain_groq import ChatGroq

llm = ChatGroq(
    api_key=settings.GROQ_API_KEY,
    model="llama-3.1-8b-instant",
    temperature=0.3
)