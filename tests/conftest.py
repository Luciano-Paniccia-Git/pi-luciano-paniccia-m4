import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Los tests nunca deben hablar con Langfuse ni con OpenAI reales.
os.environ["LANGFUSE_TRACING_ENABLED"] = "false"
os.environ.pop("LANGFUSE_PUBLIC_KEY", None)
os.environ.pop("LANGFUSE_SECRET_KEY", None)
os.environ["OPENAI_API_KEY"] = "sk-test"
