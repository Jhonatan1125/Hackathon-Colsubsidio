"""Generate the synthetic person dataset and load it into the database.

Default: 20,000 personas (seed 42, deterministic) into the configured
database (``CREDIT_ENGINE_DATABASE_URL`` or local SQLite), optionally
exporting a CSV for external loading (Excel, BULK INSERT, pandas):

    python scripts/generate_data.py                              # 20K → SQLite
    python scripts/generate_data.py --count 20000 --csv data/personas_20k.csv
    python scripts/generate_data.py --url "mssql+pyodbc://..." --replace

For SQL Server run ``scripts/create_database.sql`` first; ``--replace``
deletes existing person rows before loading (otherwise duplicate cédulas
fail the insert). Multilabel CSV columns are JSON arrays, matching the
ISJSON CHECK constraints.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from collections import Counter
from pathlib import Path

try:
    from credit_engine.database import build_engine, create_all, create_session_factory
except ImportError:  # running as a plain script without the package installed
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from credit_engine.database import build_engine, create_all, create_session_factory

from credit_engine.database.datagen import DEFAULT_COUNT, DEFAULT_SEED, generate_personas
from credit_engine.database.repositories import SqlPersonRepository

_MULTILABEL_FIELDS = (
    "area_trabajo",
    "intereses",
    "preferencias",
    "momentos_clave",
    "composicion_familiar",
    "historial_creditos",
)


_BOOL_FIELDS = ("consent_whatsapp", "consent_email")


def _write_csv(personas: list[dict], path: Path) -> None:
    if not personas:
        print("No personas generated — skipping CSV export")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(personas[0].keys())
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for persona in personas:
            row = dict(persona)
            for field in _MULTILABEL_FIELDS:
                row[field] = json.dumps(row[field], ensure_ascii=False)
            for field in _BOOL_FIELDS:
                row[field] = int(row[field])  # BIT-compatible 0/1 for BULK INSERT
            writer.writerow(row)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate and load the synthetic person dataset")
    parser.add_argument("--count", type=int, default=DEFAULT_COUNT, help=f"Personas to generate (default {DEFAULT_COUNT})")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help=f"Random seed (default {DEFAULT_SEED}, deterministic)")
    parser.add_argument("--url", default=None, help="Database URL (default: CREDIT_ENGINE_DATABASE_URL, then local SQLite)")
    parser.add_argument("--csv", default=None, help="Also export the dataset to this CSV path")
    parser.add_argument("--replace", action="store_true", help="Delete existing person rows before loading")
    parser.add_argument("--no-db", action="store_true", help="Skip the database load (CSV export only)")
    args = parser.parse_args()

    started = time.perf_counter()
    personas = generate_personas(args.count, args.seed)
    generated = time.perf_counter()
    print(f"Generated {len(personas):,} personas in {generated - started:.1f}s (seed {args.seed})")

    if args.csv and personas:
        csv_path = Path(args.csv)
        _write_csv(personas, csv_path)
        print(f"CSV written to {csv_path} ({csv_path.stat().st_size / 1_048_576:.1f} MB)")

    if not args.no_db:
        engine = build_engine(args.url)
        create_all(engine)
        repository = SqlPersonRepository(create_session_factory(engine))
        if args.replace:
            removed = repository.delete_all_persons()
            print(f"Removed {removed:,} existing person rows")
        inserted = repository.save_persons(personas)
        print(f"Loaded {inserted:,} personas into {engine.url} in {time.perf_counter() - generated:.1f}s")

    categorias = Counter(p["categoria_afiliacion"] for p in personas)
    targets = Counter(p["producto_colsubsidio_target"] or "(sin producto)" for p in personas)
    moras = Counter(p["mora_maxima_historica"] for p in personas)
    print(f"Categorías: {dict(sorted(categorias.items()))}")
    print(f"Mora: {dict(sorted(moras.items()))}")
    print("Top targets:", ", ".join(f"{k}={v:,}" for k, v in targets.most_common(5)))


if __name__ == "__main__":
    main()
