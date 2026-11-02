"""Excepciones propias del proyecto.

Tener una jerarquía de errores permite que `main.py` distinga el tipo de fallo
(archivo inválido, error de API, error de validación...) y devuelva un mensaje
claro y un código de salida distinto en cada caso, en lugar de un traceback.
"""


class ContractAnalysisError(Exception):
    """Clase base de todos los errores controlados del pipeline."""

    exit_code = 1


class ConfigError(ContractAnalysisError):
    """Falta una variable de entorno obligatoria o hay una configuración inválida."""

    exit_code = 1


class InvalidImageError(ContractAnalysisError):
    """El archivo de entrada no existe, no es JPEG/PNG, está vacío o es demasiado grande."""

    exit_code = 2


class ImageParsingError(ContractAnalysisError):
    """Falló la llamada de visión a GPT-4o (red, timeout, límite de uso, respuesta vacía...)."""

    exit_code = 3


class AgentExecutionError(ContractAnalysisError):
    """Falló la ejecución de uno de los agentes (API caída, respuesta vacía...)."""

    exit_code = 4


class OutputValidationError(ContractAnalysisError):
    """El output del agente de extracción no cumplió el esquema, incluso tras reintentar."""

    exit_code = 5
