"""Column definitions matching the dataset schema.

Each constant maps to columns in the raw person dataset. Grouped by encoding
strategy to keep responsibilities clear.
"""

from __future__ import annotations

NUMERIC_COLS: tuple[str, ...] = (
    "edad",
    "ingresos",
    "score_datacredito",
    "num_creditos_activos",
    "deuda_total_acumulada_cop",
    "cuota_mensual_total_cop",
    "capacidad_endeudamiento_disponible_pct",
)

ONEHOT_COLS: tuple[str, ...] = ("categoria_afiliacion",)

ORDINAL_COLS: tuple[str, ...] = ("mora_maxima_historica",)

ORDINAL_ORDER: list[list[str]] = [["0_DIAS", "30_DIAS", "60_DIAS", "90_MAS_DIAS"]]

MULTILABEL_COLS: tuple[str, ...] = (
    "area_trabajo",
    "intereses",
    "preferencias",
    "momentos_clave",
    "composicion_familiar",
    "historial_creditos",
)

TARGET_COL: str = "producto_colsubsidio_target"

EXCLUDED_COLS: tuple[str, ...] = (
    "cedula",
    "nombre",
    "correo",
    "direccion",
    "fecha_nacimiento",
    "telefono",
    "consent_whatsapp",
    "consent_email",
)

ALL_FEATURE_COLS: tuple[str, ...] = (
    *NUMERIC_COLS,
    *ONEHOT_COLS,
    *ORDINAL_COLS,
    *MULTILABEL_COLS,
)
