"""Fábrica de modelos de chat de LangChain para los agentes."""

from langchain_openai import ChatOpenAI

from src.config import Settings


def build_chat_model(settings: Settings, json_mode: bool = False) -> ChatOpenAI:
    """GPT-4o con temperatura 0 (queremos análisis determinista, no creativo).

    json_mode=True activa response_format=json_object: el modelo solo puede devolver JSON válido.
    El esquema exacto de los campos lo valida después Pydantic.
    """
    kwargs = {"response_format": {"type": "json_object"}} if json_mode else {}
    return ChatOpenAI(
        model=settings.openai_model,
        temperature=0,
        timeout=settings.request_timeout,
        max_retries=settings.max_retries,
        model_kwargs=kwargs,
    )
