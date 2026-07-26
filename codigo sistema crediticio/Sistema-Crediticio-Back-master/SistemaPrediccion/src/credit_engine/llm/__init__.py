"""LLM integration — personalised message generation via Ollama.

Public API surface (Facade through ``MessageGenerator``)::

    from credit_engine.llm import MessageGenerator, OllamaClient

    client = OllamaClient()
    generator = MessageGenerator(client)
    message = generator.generate_message(
        person_name="Carlos",
        product="Crédito de Libre Inversión",
        benefits="Tasa preferencial 1.2%, aprobación en 24h, sin codeudor",
        channel="whatsapp",
    )

Lower-level components (``OllamaClient``, ``SYSTEM_PROMPT``,
``CHANNEL_WRAPPERS``) are also exported for advanced use and testing.
"""

from __future__ import annotations

from credit_engine.llm.client import (
    LLMClientError,
    LLMConnectionError,
    LLMEmptyResponseError,
    OllamaClient,
)
from credit_engine.llm.generator import (
    Channel,
    GenerationError,
    MessageGenerator,
    UnknownChannelError,
)
from credit_engine.llm.prompts import (
    CHANNEL_WRAPPERS,
    SYSTEM_PROMPT,
    ChannelWrapper,
)

__all__ = [
    "OllamaClient",
    "LLMClientError",
    "LLMConnectionError",
    "LLMEmptyResponseError",
    "Channel",
    "MessageGenerator",
    "GenerationError",
    "UnknownChannelError",
    "SYSTEM_PROMPT",
    "CHANNEL_WRAPPERS",
    "ChannelWrapper",
]
