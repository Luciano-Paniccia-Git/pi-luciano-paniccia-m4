from types import SimpleNamespace
from pathlib import Path

import openai
import pytest

from src.config import Settings
from src.errors import ImageParsingError, InvalidImageError
from src.image_parser import encode_image_base64, parse_contract_image, validate_image

ROOT = Path(__file__).resolve().parent.parent
PNG = ROOT / "data" / "test_contracts" / "par1_original.png"


class FakeClient:
    """Imita client.chat.completions.create sin llamar a la API."""

    def __init__(self, content="CLÁUSULA PRIMERA - Objeto. " * 5, error=None, refusal=None):
        self.calls = []
        self._content, self._error, self._refusal = content, error, refusal
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        if self._error:
            raise self._error
        msg = SimpleNamespace(content=self._content, refusal=self._refusal)
        return SimpleNamespace(
            choices=[SimpleNamespace(message=msg, finish_reason="stop")],
            usage=SimpleNamespace(prompt_tokens=1200, completion_tokens=300),
            model="gpt-4o-2024-08-06",
        )


def test_validate_missing_file():
    with pytest.raises(InvalidImageError, match="No existe"):
        validate_image("no_existe.png")


def test_validate_bad_extension(tmp_path):
    f = tmp_path / "doc.pdf"
    f.write_bytes(b"%PDF-1.4")
    with pytest.raises(InvalidImageError, match="Formato no soportado"):
        validate_image(f)


def test_validate_empty_and_fake_image(tmp_path):
    empty = tmp_path / "a.png"
    empty.write_bytes(b"")
    with pytest.raises(InvalidImageError, match="vacío"):
        validate_image(empty)
    fake = tmp_path / "b.png"
    fake.write_bytes(b"esto no es un png")
    with pytest.raises(InvalidImageError, match="no coincide"):
        validate_image(fake)


def test_validate_too_big(tmp_path):
    big = tmp_path / "big.png"
    big.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 2_000_000)
    with pytest.raises(InvalidImageError, match="máximo"):
        validate_image(big, max_mb=1)


def test_encode_base64_ok():
    b64, mime = encode_image_base64(PNG)
    assert mime == "image/png" and b64.startswith("iVBOR")  # cabecera PNG en base64


def test_parse_builds_multimodal_payload():
    client = FakeClient()
    text = parse_contract_image(PNG, Settings(), "contrato original", client)
    assert "CLÁUSULA PRIMERA" in text
    call = client.calls[0]
    assert call["model"] == "gpt-4o" and call["temperature"] == 0
    user_content = call["messages"][1]["content"]
    assert user_content[1]["type"] == "image_url"
    assert user_content[1]["image_url"]["url"].startswith("data:image/png;base64,")


def test_parse_rate_limit_is_friendly_error():
    err = openai.RateLimitError("429", response=SimpleNamespace(status_code=429, headers={}, request=None), body=None)
    with pytest.raises(ImageParsingError, match="429"):
        parse_contract_image(PNG, Settings(), client=FakeClient(error=err))


def test_parse_empty_and_refusal():
    with pytest.raises(ImageParsingError, match="No se pudo extraer"):
        parse_contract_image(PNG, Settings(), client=FakeClient(content="  "))
    with pytest.raises(ImageParsingError, match="se negó"):
        parse_contract_image(PNG, Settings(), client=FakeClient(refusal="no puedo"))
