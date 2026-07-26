"""Per-person pipeline: lookup → evaluate → compose → outbox.

One person's failure never stops the batch: every stage outcome is
mapped to a ``PersonResult`` and the processor moves on — mirroring the
"skip-and-log, continue batch" policy in ``llm/IMPLEMENTATION.md`` and
the non-fatal-dirt philosophy of the ingestion module.
"""

from __future__ import annotations

import logging
import time

from credit_engine.worker.contracts import (
    MessageComposer,
    OutboxStore,
    PersonRepository,
    OfferEngine,
    PersonResult,
    ScheduledMessage,
    _cop_display_to_decimal,
    _rate_display_to_decimal,
)

logger = logging.getLogger(__name__)


class PersonPipeline:
    """Runs the ROOT §2.1 worker stages for a single person ID.

    All four stages are constructor-injected Protocols — the pipeline
    owns only the orchestration order and the per-person error policy.
    """

    def __init__(
        self,
        repository: PersonRepository,
        engine: OfferEngine,
        composer: MessageComposer,
        outbox: OutboxStore,
    ) -> None:
        self._repository = repository
        self._engine = engine
        self._composer = composer
        self._outbox = outbox

    def process_person(self, person_id: str, batch_id: str = "") -> PersonResult:
        """Process one person end-to-end and report the outcome.

        ``batch_id`` is stamped on the stored message so batch-scoped
        reads (API messages endpoint, CSV export) never mix messages
        from different campaigns targeting the same person.

        Never raises: unexpected stage failures are captured as
        ``status="error"`` with the exception detail preserved.
        """
        start = time.time()
        logger.debug("Pipeline start for %s (batch: %s)", person_id, batch_id or "N/A")

        try:
            # Stage 1: Person Lookup
            t0 = time.time()
            person = self._repository.get_person(person_id)
            logger.debug("Pipeline | %s | lookup: %.3fs — %s", person_id, time.time() - t0, "found" if person else "NOT FOUND")
            if person is None:
                return PersonResult(person_id=person_id, status="person_not_found")

            # Stage 2: Offer Evaluation
            t0 = time.time()
            offer = self._engine.evaluate(person)
            logger.debug(
                "Pipeline | %s | evaluate: %.3fs — %s",
                person_id, time.time() - t0,
                f"offer={offer.product_id}" if offer else "NO OFFER",
            )
            if offer is None:
                return PersonResult(person_id=person_id, status="no_offer")

            # Stage 3: Message Composition
            t0 = time.time()
            message = self._composer.compose(offer)
            logger.debug(
                "Pipeline | %s | compose: %.3fs — source=%s",
                person_id, time.time() - t0, message.source,
            )

            # Stage 4: Outbox Store
            t0 = time.time()
            self._outbox.save(
                ScheduledMessage(
                    person_id=person_id,
                    product_id=offer.product_id,
                    channel=offer.channel,
                    contact_window=offer.contact_window,
                    trigger=offer.trigger,
                    message_text=message.text,
                    message_source=message.source,
                    batch_id=batch_id,
                    amount_cop=_cop_display_to_decimal(offer.amount_cop),
                    annual_rate_pct=_rate_display_to_decimal(offer.annual_rate_pct),
                    term_months=offer.term_months,
                    cuota_cop=_cop_display_to_decimal(offer.cuota_cop),
                )
            )
            logger.debug("Pipeline | %s | outbox: %.3fs", person_id, time.time() - t0)

        except Exception as exc:  # noqa: BLE001 — per-person isolation is the contract
            elapsed = time.time() - start
            logger.error("Pipeline | %s | ERROR after %.3fs: %s: %s", person_id, elapsed, type(exc).__name__, exc)
            return PersonResult(person_id=person_id, status="error", detail=f"{type(exc).__name__}: {exc}")

        elapsed = time.time() - start
        logger.info(
            "Pipeline | %s | DONE in %.3fs — product=%s, channel=%s, source=%s",
            person_id, elapsed, offer.product_id, offer.channel, message.source,
        )
        return PersonResult(person_id=person_id, status="processed", detail=message.source)
