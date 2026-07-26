"""System prompt and channel-specific prompt templates.

Channel wrappers follow a Strategy-via-dictionary-dispatch pattern:
three plain functions selected by a ``dict`` lookup rather than a
full class hierarchy — KISS at 3 variants, trivially refactorable to
classes if channels grow.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeAlias

# ---------------------------------------------------------------------------
# System prompt — shared across every channel
# ---------------------------------------------------------------------------

SYSTEM_PROMPT: str = (
    "Eres un asistente colombiano amigable que genera mensajes personalizados "
    "para recomendar productos financieros. "
    "Tu tono es cálido, casual y cercano, como un amigo recomendando algo útil. "
    "Nunca uses lenguaje bancario formal ni frases corporativas. "
    "PROHIBIDO modificar, redondear o inventar valores numéricos, tasas, montos, "
    "plazos, cuotas o condiciones del crédito: repítelos EXACTAMENTE como aparecen "
    "en los datos que recibes. "
    "Responde ÚNICAMENTE con el texto del mensaje final, sin markdown, "
    "sin comillas alrededor del mensaje, sin comentarios adicionales "
    "y sin saludos extra como '¡Claro!' o 'Aquí tienes:'."
)

# ---------------------------------------------------------------------------
# Type alias for channel wrapper callables
# ---------------------------------------------------------------------------

ChannelWrapper: TypeAlias = Callable[[str, str, str], str]
"""Signature: ``(person_name: str, product: str, benefits: str) -> user_prompt: str``"""

# ---------------------------------------------------------------------------
# Channel-specific wrapper functions
# ---------------------------------------------------------------------------


def _sanitize(value: str) -> str:
    """Strip newlines and curly braces to block prompt injection."""
    return value.replace("{", "(").replace("}", ")").replace("\n", " ").replace("\r", " ").strip()


def _build_prompt(template_name: str, name: str, product: str, benefits: str) -> str:
    """Build a user prompt with XML-delimited inputs to separate data from instructions."""
    return (
        f"<persona>{name}</persona>\n"
        f"<producto>{product}</producto>\n"
        f"<beneficios>{benefits}</beneficios>\n\n"
        f"Crea un mensaje de {template_name} para la persona recomendando el producto. "
        f"Menciona los beneficios listados arriba, copiando los valores numéricos "
        f"(tasas, montos, plazos y cuotas) exactamente como aparecen, sin modificarlos, "
        f"redondearlos ni inventar otros.\n\n"
        "Reglas:\n"
    )


def wrap_whatsapp(name: str, product: str, benefits: str) -> str:
    """Build a WhatsApp-style user prompt — short, emoji-friendly, conversational."""
    return _build_prompt("WhatsApp", _sanitize(name), _sanitize(product), _sanitize(benefits)) + (
        "- 1 a 3 oraciones cortas.\n"
        "- Puedes usar emojis para dar calidez.\n"
        "- Tono conversacional, como un mensaje entre amigos.\n"
        "- Solo el texto del mensaje, nada más."
    )


def wrap_sms(name: str, product: str, benefits: str) -> str:
    """Build an SMS-style user prompt — short, no emojis, ~160 characters."""
    return _build_prompt("SMS", _sanitize(name), _sanitize(product), _sanitize(benefits)) + (
        "- 1 o 2 oraciones máximo.\n"
        "- Aproximadamente 160 caracteres.\n"
        "- Sin emojis.\n"
        "- Directo y conciso.\n"
        "- Solo el texto del mensaje, nada más."
    )


def wrap_email(name: str, product: str, benefits: str) -> str:
    """Build an email-style user prompt — greeting, body, sign-off."""
    return _build_prompt("correo electrónico", _sanitize(name), _sanitize(product), _sanitize(benefits)) + (
        "- 2 a 4 oraciones.\n"
        "- Incluye un saludo inicial (ej. 'Hola María,') y una despedida cordial.\n"
        "- Más detallado pero manteniendo un tono amigable y cercano.\n"
        "- Sin asunto (subject), solo el cuerpo del correo.\n"
        "- Solo el texto del mensaje, nada más."
    )


# ---------------------------------------------------------------------------
# Dictionary dispatch — maps channel slug → wrapper callable
# ---------------------------------------------------------------------------

CHANNEL_WRAPPERS: dict[str, ChannelWrapper] = {
    "whatsapp": wrap_whatsapp,
    "sms": wrap_sms,
    "email": wrap_email,
}
