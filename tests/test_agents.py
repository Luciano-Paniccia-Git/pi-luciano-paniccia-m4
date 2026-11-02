import json

import pytest
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage

from src.agents import ContextualizationAgent, ExtractionAgent
from src.errors import AgentExecutionError, OutputValidationError

GOOD = {"sections_changed": ["Cláusula Tercera"], "topics_touched": ["Precio"], "summary_of_the_change": "MODIFICACIÓN: ..."}


def fake(*contents):
    return FakeMessagesListChatModel(responses=[AIMessage(content=c) for c in contents])


def run(llm):
    return ExtractionAgent(llm, max_validation_retries=2).run("mapa", "original", "adenda")


def test_extraction_ok_first_try():
    result = run(fake(json.dumps(GOOD)))
    assert result.attempts == 1 and result.output.topics_touched == ["Precio"]


def test_extraction_accepts_code_fence():
    assert run(fake("```json\n" + json.dumps(GOOD) + "\n```")).attempts == 1


def test_extraction_retries_after_invalid_json_then_succeeds():
    result = run(fake("esto no es json", json.dumps({**GOOD, "extra": 1}), json.dumps(GOOD)))
    assert result.attempts == 3


def test_extraction_gives_up_with_clear_error():
    with pytest.raises(OutputValidationError, match="3 intentos"):
        run(fake("x", "y", "z"))


def test_contextualization_returns_text_and_rejects_empty():
    assert ContextualizationAgent(fake("## 1. Tipo ...")).run("a", "b").startswith("## 1")
    with pytest.raises(AgentExecutionError):
        ContextualizationAgent(fake("   ")).run("a", "b")
