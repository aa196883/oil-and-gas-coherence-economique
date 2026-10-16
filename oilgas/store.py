"""SQLite, provenance et imports atomiques par tranche."""
import gzip
import hashlib
import json
from pathlib import Path
import sqlite3
from datetime import datetime, timezone

SCHEMA = '''
CREATE TABLE IF NOT EXISTS benchmarks (
 id TEXT PRIMARY KEY, reference TEXT NOT NULL, expected_unit TEXT NOT NULL,
 bloomberg_ticker TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS routes (
 family TEXT NOT NULL, zone TEXT NOT NULL, logic TEXT NOT NULL CHECK(logic IN ('POL','POD')),
 benchmark_id TEXT NOT NULL REFERENCES benchmarks(id), PRIMARY KEY(family,zone));
CREATE TABLE IF NOT EXISTS series (
 id TEXT PRIMARY KEY, benchmark_id TEXT NOT NULL REFERENCES benchmarks(id),
 provider TEXT NOT NULL, symbol TEXT NOT NULL, instrument TEXT NOT NULL,
 exchange TEXT NOT NULL, currency TEXT NOT NULL, unit TEXT NOT NULL,
 price_field TEXT NOT NULL, roll_rule TEXT NOT NULL, qualification TEXT NOT NULL,
 notes TEXT NOT NULL, enabled INTEGER NOT NULL CHECK(enabled IN (0,1)));
CREATE TABLE IF NOT EXISTS ingestions (
 id INTEGER PRIMARY KEY, series_id TEXT NOT NULL REFERENCES series(id),
 start_date TEXT NOT NULL, end_date TEXT NOT NULL, retrieved_at TEXT NOT NULL,
 status TEXT NOT NULL, count INTEGER NOT NULL, error TEXT, warnings TEXT NOT NULL,
 raw_path TEXT, sha256 TEXT);
CREATE TABLE IF NOT EXISTS prices (
 series_id TEXT NOT NULL REFERENCES series(id), date TEXT NOT NULL, price REAL NOT NULL,
 contract TEXT, ingestion_id INTEGER NOT NULL REFERENCES ingestions(id),
 PRIMARY KEY(series_id,date));
'''


def connect(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    db.execute('PRAGMA busy_timeout=5000')
    return db


def initialize(db):
    db.executescript(SCHEMA)
    catalog = json.loads(Path(__file__).with_name('catalog.json').read_text())
    with db:
        for table in ('benchmarks', 'routes', 'series'):
            for row in catalog[table]:
                columns = ','.join(row)
                marks = ','.join('?' for _ in row)
                db.execute(f'INSERT OR IGNORE INTO {table} ({columns}) VALUES ({marks})', list(row.values()))


def archive(raw, directory):
    digest = hashlib.sha256(raw).hexdigest()
    directory = Path(directory).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / (digest + '.gz')
    if not target.exists():
        target.write_bytes(gzip.compress(raw, mtime=0))
    return str(target), digest


def record(db, series_id, start, end, observations, *, raw_path=None, sha256=None,
           error=None, warnings=None):
    warnings = warnings or []
    status = 'error' if error else ('empty' if not observations else ('partial' if warnings else 'ok'))
    with db:
        cursor = db.execute('''INSERT INTO ingestions
            (series_id,start_date,end_date,retrieved_at,status,count,error,warnings,raw_path,sha256)
            VALUES (?,?,?,?,?,?,?,?,?,?)''',
            (series_id, str(start), str(end), datetime.now(timezone.utc).isoformat(), status,
             0 if error else len(observations), error, json.dumps(warnings, ensure_ascii=False), raw_path, sha256))
        if not error:
            db.executemany('''INSERT INTO prices VALUES (?,?,?,?,?)
                ON CONFLICT(series_id,date) DO UPDATE SET price=excluded.price,
                contract=excluded.contract, ingestion_id=excluded.ingestion_id''',
                [(series_id, d, p, c, cursor.lastrowid) for d, p, c in observations])
    return {'series': series_id, 'start': str(start), 'end': str(end), 'status': status,
            'count': 0 if error else len(observations), 'warnings': warnings, 'error': error}
