from datetime import datetime
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from oilgas.store import connect, initialize, record


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = PROJECT_ROOT / "scripts" / "generate_json_dump.py"


class GenerateJsonDumpTests(unittest.TestCase):
    def test_exports_all_rows_and_preserves_nulls(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "source.sqlite"
            output = Path(directory) / "nested" / "dump.json"
            with connect(database) as db:
                initialize(db)
                record(
                    db,
                    "yahoo-brent",
                    "2024-01-02",
                    "2024-01-02",
                    [("2024-01-02", 80.5, None)],
                )
                expected_metadata = db.execute(
                    "SELECT COUNT(*) FROM metadata"
                ).fetchone()[0]
                expected_prices = db.execute("SELECT COUNT(*) FROM prices").fetchone()[0]
                expected_price_rows = [
                    dict(row)
                    for row in db.execute(
                        "SELECT * FROM prices ORDER BY metadata_id, date"
                    )
                ]

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--db",
                    str(database),
                    "--output",
                    str(output),
                ],
                cwd=Path(directory),
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            dump = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(set(dump), {"generated_at", "tables"})
            self.assertEqual(set(dump["tables"]), {"metadata", "prices"})
            self.assertEqual(len(dump["tables"]["metadata"]), expected_metadata)
            self.assertEqual(len(dump["tables"]["prices"]), expected_prices)
            datetime.fromisoformat(dump["generated_at"].replace("Z", "+00:00"))
            self.assertIsNone(dump["tables"]["metadata"][0]["series_id"])
            self.assertEqual(dump["tables"]["prices"], expected_price_rows)


if __name__ == "__main__":
    unittest.main()
