"""Delivery composer — offer → natural-language message with graceful degradation.

Implements the "delivery pipeline" responsibilities that
``llm/IMPLEMENTATION.md`` assigns to the caller of the LLM module:

- the **offer-to-prompt mapping** (offer envelope → ``generate_message`` args,
  with financial figures passed as display-ready strings), and
- the **graceful degradation path**: on any typed LLM failure, a
  deterministic template with the same offer data is rendered instead —
  the batch is never blocked by the LLM.

LLM channels are ``whatsapp`` / ``sms`` / ``email`` only. Any other channel
the Channel Scorer may select (``app``, call center, branch — see the
routing note in ``llm/IMPLEMENTATION.md``) renders directly from the
deterministic template without touching the LLM.
"""

from __future__ import annotations

import logging
from typing import Protocol

from credit_engine.llm import GenerationError, LLMClientError
from credit_engine.worker.contracts import ComposedMessage, Offer

logger = logging.getLogger(__name__)

LLM_CHANNELS: tuple[str, ...] = ("whatsapp", "sms", "email")


class TextGenerator(Protocol):
    """Structural contract for the LLM message generator.

    Matches ``credit_engine.llm.MessageGenerator.generate_message`` —
    any object with this signature works (including test fakes).
    """

    def generate_message(self, person_name: str, product: str, benefits: str, channel: str) -> str: ...


def _benefits_text(offer: Offer) -> str:
    """Compose the immutable offer context passed to the LLM as `benefits`.

    Deterministic composition per the offer-to-prompt mapping in
    ``llm/IMPLEMENTATION.md``: SHAP-based reason + financial terms as
    display-ready strings.
    """
    return (
        f"{offer.reason} "
        f"Monto: {offer.amount_cop} · Tasa: {offer.annual_rate_pct} · "
        f"Plazo: {offer.term_months} meses · Cuota: {offer.cuota_cop}"
    )


def _template_text(offer: Offer) -> str:
    """Deterministic fallback message — same offer data, no LLM involved.

    A blank ``person_name`` degrades to a name-free greeting instead of
    rendering "Hola , ..." (the LLM path rejects blank names with
    ``GenerationError``; the template must not ship the malformed text
    that guard exists to block).
    """
    name = offer.person_name.strip()
    greeting = f"Hola {name}" if name else "Hola"
    return (
        f"{greeting}, tenemos una oferta de {offer.product_name} para ti: "
        f"monto {offer.amount_cop}, tasa {offer.annual_rate_pct}, "
        f"plazo {offer.term_months} meses y cuota mensual de {offer.cuota_cop}. "
        f"{offer.reason}"
    )


class DeliveryComposer:
    """Compose the outgoing message for an offer, LLM-first with template fallback.

    Args:
        generator: An object satisfying ``TextGenerator`` (normally
            ``credit_engine.llm.MessageGenerator``), or ``None`` to run
            template-only (no LLM configured — e.g. Ollama not running).
    """

    def __init__(self, generator: TextGenerator | None = None) -> None:
        self._generator = generator

    def compose(self, offer: Offer) -> ComposedMessage:
        """Produce the final message text for the offer.

        Never raises for LLM failures: typed LLM errors activate the
        deterministic template path (the pipeline records the source so
        no degradation is silent). Non-LLM channels always use the template.
        """
        person_id = offer.person_id

        if self._generator is None:
            logger.debug("Composer | %s | template path (no generator configured, channel=%s)", person_id, offer.channel)
            return ComposedMessage(text=_template_text(offer), source="template")

        if offer.channel not in LLM_CHANNELS:
            logger.debug("Composer | %s | template path (channel=%s not in LLM channels)", person_id, offer.channel)
            return ComposedMessage(text=_template_text(offer), source="template")

        logger.info("Composer | %s | attempting LLM generation (channel=%s)", person_id, offer.channel)
        try:
            text = self._generator.generate_message(
                person_name=offer.person_name,
                product=offer.product_name,
                benefits=_benefits_text(offer),
                channel=offer.channel,
            )
            logger.info("Composer | %s | LLM generation succeeded", person_id)
        except (LLMClientError, GenerationError) as exc:
            logger.warning("Composer | %s | LLM failed (%s: %s) — falling back to template", person_id, type(exc).__name__, exc)
            return ComposedMessage(text=_template_text(offer), source="template")

        return ComposedMessage(text=text, source="llm")
