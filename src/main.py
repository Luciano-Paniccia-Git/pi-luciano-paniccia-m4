#!/usr/bin/env python3
"""Punto de entrada: compara un contrato original contra su adenda a partir de dos imágenes.

Uso:
    python src/main.py data/test_contracts/par1_original.png data/test_contracts/par1_adenda.png

Pipeline (cada etapa es un span de Langfuse dentro de la traza `contract-analysis`):
    1. parse_original_contract   -> GPT-4o Vision: imagen -> texto
    2. parse_amendment_contract  -> GPT-4o Vision: imagen -> texto
    3. contextualization_agent   -> Agente 1: mapa de estructura comparada
    4. extraction_agent          -> Agente 2: cambios -> JSON validado con Pydantic

La salida (JSON) va por stdout; los mensajes de progreso y errores van por stderr,
así se puede redirigir el JSON a un archivo o a otro programa sin ruido.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import uuid
from pathlib import Path

# Permite correr tanto `python src/main.py` como `python -m src.main`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.agents import ContextualizationAgent, ExtractionAgent  # noqa: E402
from src.config import Settings, load_settings, require_openai_key  # noqa: E402
from src.errors import ContractAnalysisError  # noqa: E402
from src.image_parser import build_openai_client, parse_contract_image_with_usage, validate_image  # noqa: E402
from src.llm import build_chat_model  # noqa: E402
from src.models import ContractChangeOutput  # noqa: E402
from src.tracing import Tracer  # noqa: E402


def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def run_pipeline(
    original_path: str,
    amendment_path: str,
    settings: Settings,
    tracer: Tracer,
    openai_client=None,
    parse_fn=parse_contract_image_with_usage,
    llm_factory=build_chat_model,
) -> ContractChangeOutput:
    """Ejecuta el pipeline completo bajo un span raíz. `parse_fn` y `llm_factory` son inyectables para tests."""
    # Falla rápido (y antes de gastar tokens) si alguna imagen es inválida.
    validate_image(original_path, settings.max_image_mb)
    validate_image(amendment_path, settings.max_image_mb)

    started = time.perf_counter()
    run_id = uuid.uuid4().hex[:8]
    contextualizer = ContextualizationAgent(llm_factory(settings))
    extractor = ExtractionAgent(llm_factory(settings, json_mode=True), settings.max_validation_retries)

    with tracer.attributes(session_id=f"contract-analysis-{run_id}", trace_name="contract-analysis",
                           tags=["pi4", "legalmove"]):
        with tracer.observation(
            "contract-analysis",
            as_type="span",
            input={"original_image": Path(original_path).name, "amendment_image": Path(amendment_path).name},
            metadata={"model": settings.openai_model, "run_id": run_id},
        ) as root:
            callbacks = tracer.callbacks()  # se crea dentro del span raíz para que los LLM queden anidados

            # ---------- Etapas 1 y 2: parsing multimodal ----------
            texts = {}
            for key, path, label, span_name in (
                ("original", original_path, "contrato original", "parse_original_contract"),
                ("amendment", amendment_path, "adenda / enmienda", "parse_amendment_contract"),
            ):
                log(f"[{span_name}] leyendo {Path(path).name} con {settings.openai_model} Vision...")
                with tracer.observation(
                    span_name,
                    as_type="generation",
                    model=settings.openai_model,
                    input={"image": Path(path).name, "task": f"transcribir {label}", "detail": settings.vision_detail},
                    metadata={"stage": "image_parsing"},
                ) as span:
                    parsed = parse_fn(path, settings=settings, label=label, client=openai_client)
                    span.update(
                        output=parsed.text,
                        usage_details={"input": parsed.prompt_tokens, "output": parsed.completion_tokens},
                        metadata={"latency_ms": round(parsed.latency_ms), "chars_extracted": len(parsed.text)},
                    )
                texts[key] = parsed.text
                log(f"    -> {len(parsed.text)} caracteres, {parsed.total_tokens} tokens, {parsed.latency_ms / 1000:.1f}s")

            config = {"callbacks": callbacks} if callbacks else {}

            # ---------- Etapa 3: Agente 1 ----------
            log("[contextualization_agent] armando el mapa contextual...")
            t0 = time.perf_counter()
            with tracer.observation(
                "contextualization_agent",
                as_type="agent",
                input={"original_text": texts["original"], "amendment_text": texts["amendment"]},
                metadata={"role": "Analista Legal Senior", "stage": "context_mapping"},
            ) as span:
                context_map = contextualizer.run(texts["original"], texts["amendment"], config=config)
                span.update(output=context_map, metadata={"latency_ms": round((time.perf_counter() - t0) * 1000)})
            log(f"    -> mapa de {len(context_map)} caracteres ({time.perf_counter() - t0:.1f}s)")

            # ---------- Etapa 4: Agente 2 (+ validación Pydantic) ----------
            log("[extraction_agent] extrayendo y validando los cambios...")
            t0 = time.perf_counter()
            with tracer.observation(
                "extraction_agent",
                as_type="agent",
                input={"context_map": context_map, "original_text": texts["original"],
                       "amendment_text": texts["amendment"]},
                metadata={"role": "Auditor Legal", "stage": "change_extraction"},
            ) as span:
                result = extractor.run(context_map, texts["original"], texts["amendment"], config=config)
                span.update(
                    output=result.output.model_dump(),
                    metadata={"latency_ms": round((time.perf_counter() - t0) * 1000),
                              "llm_attempts": result.attempts, "validation": "ok"},
                )
            log(f"    -> validado con Pydantic en {result.attempts} intento(s) ({time.perf_counter() - t0:.1f}s)")

            total_s = time.perf_counter() - started
            root.update(output=result.output.model_dump(),
                        metadata={"total_latency_s": round(total_s, 2), "validation": "ok"})
            trace_id = tracer.trace_id()

    url = tracer.trace_url(trace_id)
    log(f"Pipeline completo en {total_s:.1f}s." + (f"\nTraza en Langfuse: {url}" if url else ""))
    return result.output


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compara un contrato y su adenda (imágenes) y devuelve los cambios en JSON validado."
    )
    parser.add_argument("original", help="Path de la imagen del contrato original (JPEG/PNG)")
    parser.add_argument("amendment", help="Path de la imagen de la adenda / enmienda (JPEG/PNG)")
    parser.add_argument("--output", "-o", help="Guarda el JSON también en este archivo")
    parser.add_argument("--model", help="Modelo de OpenAI (por defecto gpt-4o o la variable OPENAI_MODEL)")
    parser.add_argument("--no-trace", action="store_true", help="Desactiva Langfuse para esta corrida")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        settings = load_settings()
        if args.model:
            settings = Settings(**{**settings.__dict__, "openai_model": args.model})
        require_openai_key()

        if args.no_trace:
            os.environ["LANGFUSE_TRACING_ENABLED"] = "false"
        tracer = Tracer(enabled=False if args.no_trace else None)
        if not tracer.enabled:
            log("Aviso: Langfuse desactivado (sin credenciales válidas o --no-trace). El pipeline corre sin traza.")

        try:
            output = run_pipeline(args.original, args.amendment, settings, tracer,
                                  openai_client=build_openai_client(settings))
        finally:
            tracer.flush()  # sin esto, un script corto puede terminar antes de enviar la traza
    except ContractAnalysisError as exc:
        log(f"\nERROR ({type(exc).__name__}): {exc}")
        return exc.exit_code
    except KeyboardInterrupt:
        log("\nInterrumpido por el usuario.")
        return 130

    payload = json.dumps(output.model_dump(), ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
        log(f"JSON guardado en {args.output}")
    print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
