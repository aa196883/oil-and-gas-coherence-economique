#!/usr/bin/env python3
"""Exporte l'intégralité de la base Oil & Gas dans un fichier JSON."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import tempfile


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE = PROJECT_ROOT / "data" / "oil_gas.sqlite"
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "dumps" / "dump.json"


def rows_as_dicts(db, query):
    return [dict(row) for row in db.execute(query)]


def build_dump(database):
    database = Path(database).resolve()
    if not database.is_file():
        raise FileNotFoundError(f"Base SQLite introuvable : {database}")

    uri = f"{database.as_uri()}?mode=ro"
    with sqlite3.connect(uri, uri=True) as db:
        db.row_factory = sqlite3.Row
        db.execute("BEGIN")
        metadata = rows_as_dicts(db, "SELECT * FROM metadata ORDER BY id")
        prices = rows_as_dicts(
            db, "SELECT * FROM prices ORDER BY metadata_id, date"
        )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "tables": {
            "metadata": metadata,
            "prices": prices,
        },
    }


def write_dump(payload, output):
    output = Path(output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=output.parent, delete=False
    ) as temporary:
        json.dump(payload, temporary, ensure_ascii=False, indent=2, allow_nan=False)
        temporary.write("\n")
        temporary_path = Path(temporary.name)
    temporary_path.replace(output)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Génère un dump JSON complet de la base Oil & Gas."
    )
    parser.add_argument("--db", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    try:
        payload = build_dump(args.db)
        write_dump(payload, args.output)
    except (FileNotFoundError, OSError, sqlite3.Error, ValueError) as error:
        raise SystemExit(f"Erreur : {error}") from error
    print(
        f"Dump généré : {args.output.resolve()} "
        f"({len(payload['tables']['metadata'])} metadata, "
        f"{len(payload['tables']['prices'])} prix)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
