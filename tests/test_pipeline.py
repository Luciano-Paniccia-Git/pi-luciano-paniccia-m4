import json
from types import SimpleNamespace
from pathlib import Path

import pytest
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage

from src.config import Settings
from src.errors import InvalidImageError
from src.image_parser import ParseResult
from src.main import main, run_pipeline
from src.tracing import Tracer

ROOT = Path(__file__).resolve().parent.parent
A = str(ROOT / "data" / "test_contracts" / "par1_original.png")
B = str(ROOT / "data" / "test_contracts" / "par1_adenda.png")
GOOD = {"sections_changed": ["Cláusula Tercera"], "topics_touched": ["Precio"], "summary_of_the_change": "MODIFICACIÓN: ..."}


def fake_parse(path, settings=None, label="", client=None):
    return ParseResult(text=f"texto de {Path(path).name}", model="gpt-4o", prompt_tokens=10, completion_tokens=5, latency_ms=12.0)


def fake_llm_factory(settings, json_mode=False):
    reply = json.dumps(GOOD) if json_mode else "## 1. Mapa contextual"
    return FakeMessagesListChatModel(responses=[AIMessage(content=reply)])


def test_full_pipeline_with_fakes():
    out = run_pipeline(A, B, Settings(), Tracer(enabled=False), parse_fn=fake_parse, llm_factory=fake_llm_factory)
    assert out.model_dump() == GOOD


def test_pipeline_fails_fast_on_invalid_input():
    with pytest.raises(InvalidImageError):
        run_pipeline("nada.png", B, Settings(), Tracer(enabled=False), parse_fn=fake_parse, llm_factory=fake_llm_factory)


def test_cli_returns_input_error_code(capsys):
    assert main(["nada.png", B, "--no-trace"]) == InvalidImageError.exit_code
    assert "ERROR (InvalidImageError)" in capsys.readouterr().err
