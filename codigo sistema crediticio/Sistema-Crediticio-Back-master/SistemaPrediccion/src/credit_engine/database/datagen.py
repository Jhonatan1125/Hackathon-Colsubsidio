"""Synthetic person dataset generator — the Data layer's population source.

Generates N personas (default 20,000) following the **exact dataset schema**
consumed by ``encoding/column_definitions.py`` and materialized by
``scripts/create_database.sql`` (``dbo.persons``), with realistic,
internally-consistent distributions in the spirit of
``ROOT_IMPLEMENTATION.md`` §4 (synthetic members with planted signal):

- **Category ← income** (statutory wage tiers, ROOT §3.2): Category A ≤ 2
  SMMLV, B 2–4, C > 4 — population weighted toward A/B like the real fund.
- **Score ← delinquency**: ``score_datacredito`` degrades with
  ``mora_maxima_historica`` (~6% of the population carries 60/90+ days).
- **Debt coherence**: ``cuota_mensual_total_cop`` is a fraction of income,
  ``deuda_total_acumulada_cop`` a multiple of the cuota, and
  ``capacidad_endeudamiento_disponible_pct`` derives from the payment load.
- **Planted signal**: ``producto_colsubsidio_target`` (the training label)
  correlates with ``intereses`` plus noise — a model that recovers the
  interest→product signal is working, echoing ROOT §4's verifiable-signal
  philosophy. ~15% of rows carry no product (NULL).
- **Delivery fields**: telefono/correo + consent flags (dual-key rule,
  ROOT §7.1) so generated personas flow through channel selection.

Deterministic: same ``seed`` (default 42, per ROOT convention) → identical
population, byte for byte. Pure stdlib (``random``), no numpy needed at
this scale.
"""

from __future__ import annotations

import datetime as dt
import random
import unicodedata
from typing import Any

SMMLV_COP = 1_423_500  # salario mínimo mensual legal vigente (aprox. 2026)

DEFAULT_COUNT = 20_000
DEFAULT_SEED = 42

_FIRST_NAMES = (
    "María", "Carlos", "Ana", "Luis", "Elena", "Jorge", "Paula", "Andrés",
    "Sofía", "Diego", "Laura", "Mateo", "Camila", "Juan", "Valentina", "Pedro",
    "Isabella", "Santiago", "Daniela", "Felipe", "Gabriela", "Ricardo", "Lucía",
    "Fernando", "Adriana", "Óscar", "Natalia", "Héctor", "Carolina", "Iván",
)
_LAST_NAMES = (
    "Gómez", "Ruiz", "Torres", "Pardo", "Díaz", "Mora", "Nieto", "Vela",
    "Lara", "Rincón", "Cano", "Salas", "Rojas", "Castro", "Vargas", "Suárez",
    "Molina", "Ortega", "Peña", "Cárdenas", "Osorio", "Zapata", "Franco",
    "Serrano", "Quintero", "Mejía", "Navarro", "Cortés", "Guerrero", "Paredes",
)

_AREAS_TRABAJO = (
    "servicios", "comercio", "manufactura", "educacion", "salud",
    "construccion", "tecnologia", "transporte", "agro", "publico",
)
_INTERESES = (
    "educacion", "vivienda", "consolidacion", "turismo", "tecnologia",
    "salud", "recreacion", "impuestos", "seguros", "emprendimiento",
)
_PREFERENCIAS = ("digital", "presencial", "telefonico", "correo")
_MOMENTOS = (
    "nacimiento_hijo", "inicio_semestre", "primer_empleo", "cambio_empleo",
    "matrimonio", "mudanza", "jubilacion_cercana",
)
_COMPOSICION = ("soltero", "pareja", "hijos_1", "hijos_2", "hijos_3_mas", "adultos_mayores")
_HISTORIAL = ("consumo", "vivienda", "educativo", "tarjeta", "libranza")

_CIUDADES_VIA = ("Calle", "Carrera", "Diagonal", "Transversal")

# (categoria, peso poblacional, [min, max] ingresos en SMMLV)
_CATEGORIAS = (("A", 0.55, (1.0, 2.0)), ("B", 0.30, (2.0, 4.0)), ("C", 0.15, (4.0, 15.0)))

# (mora, peso) — ~6% con mora seria (60/90+), acorde a ROOT §4
_MORAS = (("0_DIAS", 0.82), ("30_DIAS", 0.12), ("60_DIAS", 0.03), ("90_MAS_DIAS", 0.03))

# interés → (producto del catálogo, probabilidad de que el interés mande)
_TARGET_BY_INTEREST = {
    "educacion": ("educativo", 0.70),
    "consolidacion": ("compra_cartera", 0.75),
    "vivienda": ("hipotecario", 0.55),
    "impuestos": ("impuestos_seguros", 0.60),
    "seguros": ("impuestos_seguros", 0.60),
}
# Fallback distribution includes a small leak of interest-mapped products so
# the planted signal is noisy in BOTH directions (positives can occur without
# the driving interest), like ROOT §4's additive-noise formulation — the
# negative class is never perfectly separable.
_FALLBACK_TARGETS = (
    ("libre_inversion", 0.47),
    ("cupo_rotativo", 0.37),
    ("educativo", 0.05),
    ("hipotecario", 0.04),
    ("compra_cartera", 0.04),
    ("impuestos_seguros", 0.03),
)
_NO_TARGET_RATE = 0.15


def _ascii(text: str) -> str:
    """Strip accents: 'Iván' → 'Ivan' (safe email local parts)."""
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")


def _pick_weighted(rng: random.Random, options: tuple[tuple[str, float], ...]) -> str:
    return rng.choices([o[0] for o in options], weights=[o[1] for o in options], k=1)[0]


def _sample_labels(rng: random.Random, vocab: tuple[str, ...], k_max: int, *, allow_empty: bool = False) -> list[str]:
    k_min = 0 if allow_empty else 1
    k = rng.randint(k_min, k_max)
    return sorted(rng.sample(vocab, k)) if k else []


def _target_for(rng: random.Random, intereses: list[str]) -> str | None:
    if rng.random() < _NO_TARGET_RATE:
        return None
    for interes in intereses:
        mapping = _TARGET_BY_INTEREST.get(interes)
        if mapping is not None and rng.random() < mapping[1]:
            return mapping[0]
    return _pick_weighted(rng, _FALLBACK_TARGETS)


def generate_personas(
    count: int = DEFAULT_COUNT,
    seed: int = DEFAULT_SEED,
    *,
    start_cedula: int = 100_000_000,
) -> list[dict[str, Any]]:
    """Generate ``count`` personas as dataset-schema dicts.

    Deterministic for a given ``(count, seed)``. Cédulas are unique
    sequential 9-digit numbers starting at ``start_cedula`` (valid per
    the ingestion validator: ASCII digits, 5–11 characters).
    """
    rng = random.Random(seed)
    today = dt.date(2026, 7, 25)  # fixed reference date → deterministic birthdates
    personas: list[dict[str, Any]] = []

    for i in range(count):
        cedula = str(start_cedula + i)
        nombre = f"{rng.choice(_FIRST_NAMES)} {rng.choice(_LAST_NAMES)}"
        edad = rng.randint(18, 69)

        categoria = _pick_weighted(rng, tuple((c, w) for c, w, _ in _CATEGORIAS))
        smmlv_lo, smmlv_hi = next(b for c, _, b in _CATEGORIAS if c == categoria)
        ingresos = round(rng.uniform(smmlv_lo, smmlv_hi) * SMMLV_COP, -3)

        mora = _pick_weighted(rng, _MORAS)
        mora_penalty = {"0_DIAS": 0, "30_DIAS": 90, "60_DIAS": 180, "90_MAS_DIAS": 300}[mora]
        score = max(150, min(950, int(rng.gauss(680, 90)) - mora_penalty))

        num_creditos = rng.choices((0, 1, 2, 3, 4), weights=(25, 35, 22, 12, 6), k=1)[0]
        carga = rng.uniform(0.05, 0.45) if num_creditos else 0.0
        cuota_mensual = round(ingresos * carga, -3)
        deuda_total = round(cuota_mensual * rng.uniform(6, 48), -3)
        capacidad = round(max(5.0, min(95.0, (0.5 - carga) * 100 + rng.uniform(-5, 15))), 1)

        intereses = _sample_labels(rng, _INTERESES, 3)
        momentos = _sample_labels(rng, _MOMENTOS, 2, allow_empty=True)
        telefono = f"57{rng.choice(('300', '301', '310', '311', '320', '321'))}{rng.randint(1_000_000, 9_999_999)}"
        correo = f"{_ascii(nombre.split()[0]).lower()}.{cedula[-4:]}@example.com"
        consent_whatsapp = rng.random() < 0.62
        consent_email = rng.random() < 0.48

        fecha_nacimiento = today.replace(year=today.year - edad) - dt.timedelta(days=rng.randint(0, 364))

        personas.append(
            {
                "cedula": cedula,
                "nombre": nombre,
                "correo": correo if consent_email or rng.random() < 0.7 else None,
                "direccion": f"{rng.choice(_CIUDADES_VIA)} {rng.randint(1, 170)} # {rng.randint(1, 99)}-{rng.randint(1, 99)}",
                "fecha_nacimiento": fecha_nacimiento,
                "telefono": telefono if consent_whatsapp or rng.random() < 0.8 else None,
                "consent_whatsapp": consent_whatsapp,
                "consent_email": consent_email,
                "edad": edad,
                "ingresos": float(ingresos),
                "score_datacredito": score,
                "num_creditos_activos": num_creditos,
                "deuda_total_acumulada_cop": float(deuda_total),
                "cuota_mensual_total_cop": float(cuota_mensual),
                "capacidad_endeudamiento_disponible_pct": capacidad,
                "categoria_afiliacion": categoria,
                "mora_maxima_historica": mora,
                "area_trabajo": _sample_labels(rng, _AREAS_TRABAJO, 2),
                "intereses": intereses,
                "preferencias": _sample_labels(rng, _PREFERENCIAS, 2),
                "momentos_clave": momentos,
                "composicion_familiar": _sample_labels(rng, _COMPOSICION, 2),
                "historial_creditos": _sample_labels(rng, _HISTORIAL, 3, allow_empty=True),
                "producto_colsubsidio_target": _target_for(rng, intereses),
            }
        )

    return personas
