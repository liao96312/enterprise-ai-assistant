from typing import List

from app.config import settings
from app.memory import Message


def llm_available() -> bool:
    return bool(settings.api_key and settings.resolved_chat_model)


def chat_completion(messages: List[Message]) -> str:
    if not llm_available():
        raise RuntimeError("API_KEY or CHAT_MODEL is not configured")

    from langchain_openai import ChatOpenAI

    kwargs = {
        "api_key": settings.api_key,
        "model": settings.resolved_chat_model,
        "temperature": 0.2,
    }
    if settings.resolved_base_url:
        kwargs["base_url"] = settings.resolved_base_url

    llm = ChatOpenAI(**kwargs)
    response = llm.invoke(messages)
    return str(response.content)
