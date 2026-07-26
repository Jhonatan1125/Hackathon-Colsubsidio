"""Demo stand-ins: seeded person data and a rule-based offer engine.

These make the end-to-end flow (API → ingestion → worker → outbox) produce
real data TODAY, before the ``database/`` and ``engine/`` packages land:

- ``build_demo_repository()`` seeds an ``InMemoryPersonRepository`` with 12
  personas following the **actual dataset schema** used by ``encoding/``
  (``column_definitions.py``: cedula, nombre, ingresos, score_datacredito,
  categoria_afiliacion, mora_maxima_historica, intereses, momentos_clave, …)
  plus the contact/consent fields delivery needs (ROOT §7.1 dual-key rule).
  The same schema is materialized by ``scripts/create_database.sql``
  (SQL Server) — when ``database/`` lands, its repository returns rows with
  these exact keys and this module's engine keeps working unchanged.

- ``DemoOfferEngine`` is a deterministic, rule-based ``OfferEngine``
  stand-in. It is **NOT** the ROOT §6 decision engine (no ML propensities,
  no EV ranking, no SHAP): it applies simple interest-based product rules,
  a French-amortization cuota, and consent-aware channel selection so every
  downstream stage receives a realistic, fully-populated ``Offer`` envelope.
  It is replaced through the ``OfferEngine`` Protocol when ``engine/`` lands.
"""

from __future__ import annotations

import logging
from typing import Any

from credit_engine.worker.contracts import Offer
from credit_engine.worker.repository import InMemoryPersonRepository

logger = logging.getLogger(__name__)

# Annual rates by affiliation category (Category A gets the lowest — ROOT §3.2)
_RATES_BY_CATEGORY: dict[str, float] = {"A": 0.145, "B": 0.165, "C": 0.185}
_DEFAULT_TERM_MONTHS = 36


def _cop(value: float) -> str:
    """Format a number as display-ready COP: 5600000 → ``$5.600.000``."""
    rounded = int(round(value / 1000.0) * 1000)
    return "$" + f"{rounded:,}".replace(",", ".")


def _pct(rate: float) -> str:
    """Format an annual rate: 0.145 → ``14,5% E.A.``"""
    return f"{rate * 100:.1f}".replace(".", ",") + "% E.A."


def _monthly_installment(amount: float, annual_rate: float, term_months: int) -> float:
    """French amortization: fixed monthly installment for the loan."""
    i = (1 + annual_rate) ** (1 / 12) - 1
    return amount * i / (1 - (1 + i) ** -term_months)


class DemoOfferEngine:
    """Rule-based ``OfferEngine`` stand-in (see module docstring).

    Decline rule: personas with historical delinquency of 90+ days get no
    offer (echoing — not implementing — the ROOT §6.2 risk gatekeeper).
    """

    def evaluate(self, person: dict[str, Any]) -> Offer | None:
        person_id = str(person.get("cedula", "?"))
        logger.debug("DemoOfferEngine evaluating person %s", person_id)

        if person.get("mora_maxima_historica") == "90_MAS_DIAS":
            logger.info("DemoOfferEngine | %s | DECLINED — mora_maxima_historica = 90_MAS_DIAS", person_id)
            return None

        intereses = [i.lower() for i in (person.get("intereses") or [])]
        if "educacion" in intereses:
            product_id, product_name = "educativo", "Crédito Educativo"
            logger.debug("DemoOfferEngine | %s | intereses: %s → producto: %s", person_id, intereses, product_id)
        elif "consolidacion" in intereses:
            product_id, product_name = "compra_cartera", "Compra de Cartera"
            logger.debug("DemoOfferEngine | %s | intereses: %s → producto: %s", person_id, intereses, product_id)
        elif "vivienda" in intereses:
            product_id, product_name = "hipotecario", "Crédito Hipotecario"
            logger.debug("DemoOfferEngine | %s | intereses: %s → producto: %s", person_id, intereses, product_id)
        else:
            product_id, product_name = "libre_inversion", "Crédito de Libre Inversión"
            logger.debug("DemoOfferEngine | %s | intereses: %s → producto: %s (default)", person_id, intereses, product_id)

        ingresos = float(person.get("ingresos", 0.0))
        capacidad_pct = float(person.get("capacidad_endeudamiento_disponible_pct", 30.0))
        categoria = str(person.get("categoria_afiliacion", "C"))
        rate = _RATES_BY_CATEGORY.get(categoria, _RATES_BY_CATEGORY["C"])

        logger.debug(
            "DemoOfferEngine | %s | financials: ingresos=%.0f, capacidad=%.0f%%, categoria=%s, rate=%.1f%%",
            person_id, ingresos, capacidad_pct, categoria, rate * 100,
        )

        # Max installment: 30% of income scaled by available capacity, then
        # the loan amount is the French-amortization inverse of it.
        max_cuota = ingresos * 0.30 * (capacidad_pct / 100.0)
        if max_cuota <= 0:
            logger.info("DemoOfferEngine | %s | DECLINED — max_cuota <= 0 (ingresos=%.0f, capacidad=%.0f%%)", person_id, ingresos, capacidad_pct)
            return None

        i = (1 + rate) ** (1 / 12) - 1
        amount = max_cuota * (1 - (1 + i) ** -_DEFAULT_TERM_MONTHS) / i
        cuota = _monthly_installment(amount, rate, _DEFAULT_TERM_MONTHS)

        channel, window = self._channel_and_window(person)
        trigger = self._trigger(person)

        logger.debug(
            "DemoOfferEngine | %s | offer: %s, amount=%s, channel=%s, window=%s, trigger=%s",
            person_id, product_id, _cop(amount), channel, window, trigger,
        )

        interes_txt = ", ".join(person.get("intereses") or []) or "tu perfil financiero"
        reason = (
            f"Te recomendamos {product_name} por tus intereses en {interes_txt} "
            f"y tu capacidad de pago disponible del {capacidad_pct:.0f}%."
        )

        return Offer(
            person_id=str(person.get("cedula", "")),
            person_name=str(person.get("nombre", "")),
            product_id=product_id,
            product_name=product_name,
            amount_cop=_cop(amount),
            annual_rate_pct=_pct(rate),
            term_months=_DEFAULT_TERM_MONTHS,
            cuota_cop=_cop(cuota),
            channel=channel,
            contact_window=window,
            trigger=trigger,
            reason=reason,
        )

    @staticmethod
    def _channel_and_window(person: dict[str, Any]) -> tuple[str, str]:
        """Consent-aware channel (dual-key: opt-in + contact data) and window."""
        if person.get("consent_whatsapp") and person.get("telefono"):
            channel = "whatsapp"
        elif person.get("consent_email") and person.get("correo"):
            channel = "email"
        else:
            channel = "app"
        window = "night" if int(person.get("edad", 40)) < 40 else "morning"
        return channel, window

    @staticmethod
    def _trigger(person: dict[str, Any]) -> str:
        momentos = person.get("momentos_clave") or []
        return momentos[0] if momentos else "inmediato"


def _persona(
    cedula: str,
    nombre: str,
    edad: int,
    ingresos: float,
    categoria: str,
    intereses: list[str],
    *,
    mora: str = "0_DIAS",
    capacidad: float = 60.0,
    momentos: list[str] | None = None,
    telefono: str | None = None,
    correo: str | None = None,
    consent_whatsapp: bool = False,
    consent_email: bool = False,
) -> dict[str, Any]:
    return {
        "cedula": cedula,
        "nombre": nombre,
        "edad": edad,
        "ingresos": ingresos,
        "score_datacredito": 700,
        "num_creditos_activos": 1,
        "deuda_total_acumulada_cop": ingresos * 2,
        "cuota_mensual_total_cop": ingresos * 0.15,
        "capacidad_endeudamiento_disponible_pct": capacidad,
        "categoria_afiliacion": categoria,
        "mora_maxima_historica": mora,
        "area_trabajo": ["servicios"],
        "intereses": intereses,
        "preferencias": ["digital"],
        "momentos_clave": momentos or [],
        "composicion_familiar": ["pareja"],
        "historial_creditos": ["consumo"],
        "telefono": telefono,
        "correo": correo,
        "consent_whatsapp": consent_whatsapp,
        "consent_email": consent_email,
    }


DEMO_PERSONS: dict[str, dict[str, Any]] = {
    p["cedula"]: p
    for p in (
        _persona("10000001", "María Gómez", 32, 2_600_000, "A", ["educacion"], momentos=["inicio_semestre"], telefono="573001112233", consent_whatsapp=True),
        _persona("10000002", "Carlos Ruiz", 45, 4_800_000, "B", ["consolidacion"], correo="carlos@example.com", consent_email=True),
        _persona("10000003", "Ana Torres", 29, 1_900_000, "A", ["vivienda"], momentos=["nacimiento_hijo"], telefono="573004445566", consent_whatsapp=True),
        _persona("10000004", "Luis Pardo", 51, 6_500_000, "C", ["turismo"], correo="luis@example.com", consent_email=True),
        _persona("10000005", "Elena Díaz", 38, 3_200_000, "B", ["educacion", "tecnologia"], telefono="573007778899", consent_whatsapp=True),
        _persona("10000006", "Jorge Mora", 42, 2_100_000, "A", ["consolidacion"], mora="90_MAS_DIAS"),
        _persona("P0001", "Paula Nieto", 27, 2_300_000, "A", ["educacion"], telefono="573001010101", consent_whatsapp=True),
        _persona("P0002", "Andrés Vela", 35, 3_900_000, "B", ["vivienda"], correo="andres@example.com", consent_email=True),
        _persona("P0003", "Sofía Lara", 48, 5_200_000, "C", ["turismo", "salud"]),
        _persona("P0004", "Diego Rincón", 31, 2_800_000, "B", ["consolidacion"], telefono="573002020202", consent_whatsapp=True),
        _persona("P0005", "Laura Cano", 26, 1_800_000, "A", ["educacion"], momentos=["primer_empleo"], correo="laura@example.com", consent_email=True),
        _persona("P0006", "Mateo Salas", 39, 4_100_000, "B", ["vivienda"], telefono="573003030303", consent_whatsapp=True),
    )
}
"""Twelve demo personas (≥ the 10-ID batch minimum) — cédulas and P-ids."""


def build_demo_repository() -> InMemoryPersonRepository:
    """Fresh repository seeded with the demo personas."""
    return InMemoryPersonRepository(DEMO_PERSONS)
