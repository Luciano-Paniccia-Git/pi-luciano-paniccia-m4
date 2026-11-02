"""Capa fina sobre Langfuse.

Centraliza la creación de trazas y spans para que el resto del código no tenga que
preguntar si Langfuse está activo: si no hay claves, los spans son "nulos" y el pipeline
funciona igual (sin trazabilidad).
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator, List, Optional

from src.config import langfuse_configured


class _NullObservation:
    """Span de mentira que acepta .update() y no hace nada (Langfuse desactivado)."""

    trace_id = None

    def update(self, **_: Any) -> None:  # noqa: D401
        return None


class Tracer:
    def __init__(self, enabled: Optional[bool] = None):
        want = langfuse_configured() if enabled is None else enabled
        self.enabled = False
        self._client = None
        if want:
            from langfuse import get_client

            client = get_client()
            try:
                self.enabled = bool(client.auth_check())
            except Exception:  # noqa: BLE001 - sin red o credenciales inválidas: seguimos sin tracing
                self.enabled = False
            self._client = client if self.enabled else None

    @contextmanager
    def observation(self, name: str, as_type: str = "span", **kwargs: Any) -> Iterator[Any]:
        """Abre un span (hijo del span actual, o raíz si no hay ninguno)."""
        if not self.enabled:
            yield _NullObservation()
            return
        with self._client.start_as_current_observation(name=name, as_type=as_type, **kwargs) as obs:
            yield obs

    @contextmanager
    def attributes(self, **kwargs: Any) -> Iterator[None]:
        """Propaga session_id / tags / trace_name a todos los spans de la traza."""
        if not self.enabled:
            yield
            return
        from langfuse import propagate_attributes

        with propagate_attributes(**kwargs):
            yield

    def callbacks(self) -> List[Any]:
        """Callback de LangChain: registra cada llamada al LLM (tokens, latencia) como span hijo."""
        if not self.enabled:
            return []
        from langfuse.langchain import CallbackHandler

        return [CallbackHandler()]

    def trace_id(self) -> Optional[str]:
        return self._client.get_current_trace_id() if self.enabled else None

    def trace_url(self, trace_id: Optional[str]) -> Optional[str]:
        if not (self.enabled and trace_id):
            return None
        try:
            return self._client.get_trace_url(trace_id=trace_id)
        except Exception:  # noqa: BLE001 - el link es un extra, no debe romper la corrida
            return None

    def flush(self) -> None:
        """Envía a Langfuse todo lo pendiente (imprescindible en scripts cortos antes de salir)."""
        if self.enabled:
            self._client.flush()
