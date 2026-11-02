"""Configuración centralizada: lectura de variables de entorno (.env) y parámetros del sistema.

Ninguna clave está escrita en el código: todo viene de variables de entorno,
cargadas desde `.env` con python-dotenv.
"""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from src.errors import ConfigError

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    """Parámetros de ejecución. Se pueden sobreescribir con variables de entorno."""

    openai_model: str = "gpt-4o"
    vision_detail: str = "high"        # "high" lee mejor el texto chico de un contrato escaneado
    request_timeout: float = 90.0      # segundos por llamada a la API
    max_retries: int = 3               # reintentos del cliente de OpenAI ante 429 / 5xx / timeouts
    max_image_mb: float = 15.0         # tamaño máximo por imagen
    max_validation_retries: int = 2    # reintentos del Agente 2 si su JSON no valida


def load_settings() -> Settings:
    """Carga `.env` (si existe) y arma los Settings, validando los valores numéricos."""
    load_dotenv(PROJECT_ROOT / ".env")
    try:
        return Settings(
            openai_model=os.getenv("OPENAI_MODEL", Settings.openai_model),
            vision_detail=os.getenv("VISION_DETAIL", Settings.vision_detail),
            request_timeout=float(os.getenv("OPENAI_TIMEOUT", Settings.request_timeout)),
            max_retries=int(os.getenv("OPENAI_MAX_RETRIES", Settings.max_retries)),
        )
    except ValueError as exc:
        raise ConfigError(f"Valor inválido en una variable de entorno numérica: {exc}") from exc


def require_openai_key() -> None:
    """Falla temprano y con un mensaje claro si falta la clave de OpenAI."""
    key = os.getenv("OPENAI_API_KEY", "")
    if not key or key == "your-key-here":
        raise ConfigError(
            "Falta OPENAI_API_KEY. Copiá .env.example a .env y completalo con tu clave de OpenAI."
        )


def langfuse_configured() -> bool:
    """True si hay credenciales de Langfuse reales (no los placeholders de .env.example)."""
    pub, sec = os.getenv("LANGFUSE_PUBLIC_KEY", ""), os.getenv("LANGFUSE_SECRET_KEY", "")
    return bool(pub and sec) and "xxx" not in pub and "xxx" not in sec
