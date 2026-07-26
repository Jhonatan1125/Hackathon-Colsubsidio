"""Message generation orchestrator — Facade combining prompts, client, and output cleaning.

Receives person + recommendation data, selects the right channel wrapper,
calls the LLM client, cleans the output, and returns a ready-to-send string.

Design patterns applied:
- **Facade**     — single public entry point hiding all internal complexity.
- **Constructor Injection** — the LLM client is passed in, not created inside,
  making the generator trivially testable with a mock.
- **Composition** — plain functions and objects, no inheritance.
- **Explicit Error Propagation** — raises directly; the worker decides what to do.
"""

from __future__ import annotations

import re
from typing import Literal, Protocol

from credit_engine.llm.prompts import (
    CHANNEL_WRAPPERS,
    SYSTEM_PROMPT,
    ChannelWrapper,
)

# ---------------------------------------------------------------------------
# Structural interface for any LLM client (Dependency Injection contract)
# ---------------------------------------------------------------------------


class LLMClient(Protocol):
    """Structural interface for an LLM chat-completion client.

    Any object with this signature satisfies the protocol — no
    inheritance needed.  This is the contract that
    ``MessageGenerator`` depends on.
    """

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Send prompts and return the LLM's text response."""
        ...


# ---------------------------------------------------------------------------
# Supported channel slugs
# ---------------------------------------------------------------------------

Channel = Literal["whatsapp", "sms", "email"]


class GenerationError(Exception):
    """Raised when message generation fails."""


class UnknownChannelError(GenerationError):
    """Raised when the requested channel is not recognised."""


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------


class MessageGenerator:
    """Orchestrates prompt construction, LLM invocation, and output cleaning."""

    _FENCE_PATTERN = re.compile(r"```[^\n]*\n?")
    _BOLD_WRAP_PATTERN = re.compile(r"\*\*(.+?)\*\*")

    _COMMON_PREFIXES: tuple[str, ...] = (
        "Mensaje:",
        "Mensaje personalizado:",
        "Aquí está el mensaje:",
        "Aquí tienes el mensaje:",
        "Claro, aquí tienes:",
        "¡Claro!",
        "Por supuesto:",
        "Mensaje de WhatsApp:",
        "Mensaje SMS:",
        "Correo electrónico:",
    )

    def __init__(self, client: LLMClient) -> None:
        """Initialise the message generator.

        Args:
            client: Any object implementing the ``LLMClient`` protocol
                (i.e. has a ``generate(system_prompt, user_prompt) -> str`` method).
        """
        self._client = client

    def generate_message(
        self,
        person_name: str,
        product: str,
        benefits: str,
        channel: Channel,
    ) -> str:
        """Generate a personalised message for the given person and product.

        Args:
            person_name: The recipient's name. Must not be empty.
            product: The financial product being recommended. Must not be empty.
            benefits: Key benefits of the product (e.g. "Tasa 1.2%, sin codeudor").
            channel: Delivery channel slug — one of ``"whatsapp"``, ``"sms"``, ``"email"``.

        Returns:
            The cleaned message text ready for dispatch.

        Raises:
            GenerationError: If ``person_name`` or ``product`` is empty.
            UnknownChannelError: If ``channel`` is not a recognised slug.
        """
        name: str = person_name.strip()
        prod: str = product.strip()
        ben: str = benefits.strip()

        if not name:
            raise GenerationError("person_name must not be empty")
        if not prod:
            raise GenerationError("product must not be empty")

        wrapper: ChannelWrapper | None = CHANNEL_WRAPPERS.get(channel)
        if wrapper is None:
            raise UnknownChannelError(
                f"Unknown channel '{channel}'. Valid channels: {', '.join(sorted(CHANNEL_WRAPPERS))}"
            )

        user_prompt: str = wrapper(name, prod, ben)
        raw_output: str = self._client.generate(SYSTEM_PROMPT, user_prompt)
        return self._clean_output(raw_output)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @classmethod
    def _clean_output(cls, text: str) -> str:
        """Strip markdown artefacts and common model boilerplate from the output."""
        cleaned: str = cls._FENCE_PATTERN.sub("", text.strip())
        cleaned = cleaned.replace("```", "")
        cleaned = cls._BOLD_WRAP_PATTERN.sub(r"\1", cleaned)

        for prefix in cls._COMMON_PREFIXES:
            if cleaned.lower().startswith(prefix.lower()):
                cleaned = cleaned[len(prefix) :].strip()
                break

        if (cleaned.startswith('"') and cleaned.endswith('"')) or (cleaned.startswith("'") and cleaned.endswith("'")):
            cleaned = cleaned[1:-1]

        cleaned = cleaned.strip()
        if not cleaned:
            raise GenerationError("Generated message is empty after cleanup")

        return cleaned
