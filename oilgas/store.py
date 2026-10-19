"""Création et entretien des deux tables SQLite : metadata et prices."""
import gzip
import hashlib
import json
from pathlib import Path
import sqlite3

from .sources import DataError

SCHEMA = '''
CREATE TABLE IF NOT EXISTS metadata (
 id INTEGER PRIMARY KEY,
 family TEXT NOT NULL, zone TEXT NOT NULL,
 logic TEXT NOT NULL CHECK(logic IN ('POL','POD')),
 benchmark_id TEXT NOT NULL, reference TEXT NOT NULL, expected_unit TEXT NOT NULL,
 bloomberg_ticker TEXT NOT NULL,
 series_id TEXT, provider TEXT, symbol TEXT, instrument TEXT, exchange TEXT,
 currency TEXT, unit TEXT, price_field TEXT, roll_rule TEXT, qualification TEXT,
 notes TEXT, enabled INTEGER NOT NULL DEFAULT 0 CHECK(enabled IN (0,1)),
 start_date TEXT, end_date TEXT, last_status TEXT, last_error TEXT,
 CHECK ((start_date IS NULL AND end_date IS NULL)
     OR (start_date IS NOT NULL AND end_date IS NOT NULL AND start_date <= end_date)),
 UNIQUE(family,zone,series_id));
CREATE UNIQUE INDEX IF NOT EXISTS metadata_empty_route
 ON metadata(family,zone) WHERE series_id IS NULL;
CREATE INDEX IF NOT EXISTS metadata_series ON metadata(series_id);
CREATE TABLE IF NOT EXISTS prices (
 date TEXT NOT NULL, price REAL NOT NULL,
 metadata_id INTEGER NOT NULL REFERENCES metadata(id),
 PRIMARY KEY(metadata_id,date));
'''

SERIES_COLUMNS = ('id', 'benchmark_id', 'provider', 'symbol', 'instrument', 'exchange',
                  'currency', 'unit', 'price_field', 'roll_rule', 'qualification', 'notes')


def connect(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    db.execute('PRAGMA busy_timeout=5000')
    return db


def query(db, sql, params=()):
    return [dict(row) for row in db.execute(sql, params)]


def insert_metadata(db, data):
    columns = ','.join(data)
    marks = ','.join('?' for _ in data)
    db.execute(f'INSERT INTO metadata ({columns}) VALUES ({marks})', list(data.values()))


def initialize(db):
    db.executescript(SCHEMA)
    catalog = json.loads(Path(__file__).with_name('catalog.json').read_text())
    benchmarks = {row['id']: row for row in catalog['benchmarks']}
    with db:
        for route in catalog['routes']:
            benchmark = benchmarks[route['benchmark_id']]
            sources = [s for s in catalog['series'] if s['benchmark_id'] == route['benchmark_id']]
            for source in sources or [None]:
                params = [route['family'], route['zone']]
                sql = 'SELECT id FROM metadata WHERE family=? AND zone=?'
                if source:
                    sql += ' AND series_id=?'
                    params.append(source['id'])
                if db.execute(sql, params).fetchone():
                    continue
                data = {**route, **{k: v for k, v in benchmark.items() if k != 'id'}}
                if source:
                    data.update({k: v for k, v in source.items() if k != 'id'})
                    data['series_id'] = source['id']
                insert_metadata(db, data)


def selected(db, names=None):
    columns = ','.join('series_id AS id' if c == 'id' else c for c in SERIES_COLUMNS)
    all_series = query(db, f'SELECT DISTINCT {columns},enabled FROM metadata WHERE series_id IS NOT NULL ORDER BY series_id')
    by_id = {s['id']: s for s in all_series}
    if names:
        unknown = set(names) - by_id.keys()
        if unknown:
            raise DataError('Séries inconnues : ' + ', '.join(sorted(unknown)))
        return [by_id[name] for name in dict.fromkeys(names)]
    return [s for s in all_series if s['enabled'] and s['provider'] == 'yahoo']


def register_series(db, data):
    if (not isinstance(data, dict) or set(data) != set(SERIES_COLUMNS)
            or any(not isinstance(data[k], str) or not data[k].strip() for k in SERIES_COLUMNS)):
        raise DataError('Métadonnées requises : ' + ', '.join(SERIES_COLUMNS))
    if data['provider'] == 'yahoo':
        raise DataError('register-series est réservé aux sources CSV externes')
    if db.execute('SELECT 1 FROM metadata WHERE series_id=?', (data['id'],)).fetchone():
        raise DataError('Série déjà enregistrée : ' + data['id'])
    routes = query(db, '''SELECT DISTINCT family,zone,logic,benchmark_id,reference,
        expected_unit,bloomberg_ticker FROM metadata WHERE benchmark_id=?''', (data['benchmark_id'],))
    if not routes:
        raise DataError('Benchmark inconnu : ' + data['benchmark_id'])
    with db:
        for route in routes:
            source = {k: v for k, v in data.items() if k != 'id'}
            source.update(series_id=data['id'], enabled=0)
            empty = db.execute('SELECT id FROM metadata WHERE family=? AND zone=? AND series_id IS NULL',
                               (route['family'], route['zone'])).fetchone()
            if empty:
                assignments = ','.join(f'{k}=?' for k in source)
                db.execute(f'UPDATE metadata SET {assignments} WHERE id=?', [*source.values(), empty['id']])
            else:
                insert_metadata(db, {**route, **source})


def route_count(db):
    return db.execute('SELECT COUNT(*) FROM (SELECT DISTINCT family,zone FROM metadata)').fetchone()[0]


def last_date(db, series_id):
    return db.execute('SELECT MAX(end_date) FROM metadata WHERE series_id=?', (series_id,)).fetchone()[0]


def catalog_rows(db):
    return query(db, 'SELECT *,unit AS native_unit FROM metadata ORDER BY family,zone,series_id')


def coverage(db):
    return query(db, '''SELECT m.*,m.unit AS native_unit,m.start_date AS first_date,
        m.end_date AS last_date,COUNT(p.date) AS observations
        FROM metadata m LEFT JOIN prices p ON p.metadata_id=m.id
        GROUP BY m.id ORDER BY m.family,m.zone,m.series_id''')


def price_rows(db, family, zone, start, end, series=None):
    if start > end:
        raise DataError('start doit précéder end')
    if not db.execute('SELECT 1 FROM metadata WHERE family=? AND zone=?', (family, zone)).fetchone():
        raise DataError('Couple famille/zone inconnu ; consulter catalog')
    sql = '''SELECT m.family,m.zone,m.logic,m.reference,m.expected_unit,
        m.series_id,m.provider,m.symbol,m.instrument,m.unit AS native_unit,
        m.price_field,m.roll_rule,m.qualification,m.notes,p.date,p.price
        FROM metadata m JOIN prices p ON p.metadata_id=m.id
        WHERE m.family=? AND m.zone=? AND p.date BETWEEN ? AND ?'''
    values = [family, zone, str(start), str(end)]
    if series:
        sql += ' AND m.series_id=?'
        values.append(series)
    rows = query(db, sql + ' ORDER BY m.series_id,p.date', values)
    if not rows:
        raise DataError('Aucun prix disponible pour cette route, série et période ; consulter coverage')
    return rows


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
    metadata = db.execute('SELECT id FROM metadata WHERE series_id=?', (series_id,)).fetchall()
    if not metadata:
        raise DataError('Série inconnue : ' + series_id)
    with db:
        for row in metadata:
            if not error:
                db.executemany('''INSERT INTO prices(date,price,metadata_id) VALUES (?,?,?)
                    ON CONFLICT(metadata_id,date) DO UPDATE SET price=excluded.price''',
                    [(d, p, row['id']) for d, p, _ in observations])
            db.execute('''UPDATE metadata SET
                start_date=(SELECT MIN(date) FROM prices WHERE metadata_id=metadata.id),
                end_date=(SELECT MAX(date) FROM prices WHERE metadata_id=metadata.id),
                last_status=?,last_error=? WHERE id=?''', (status, error, row['id']))
    return {'series': series_id, 'start': str(start), 'end': str(end), 'status': status,
            'count': 0 if error else len(observations), 'warnings': warnings, 'error': error,
            'raw_path': raw_path, 'sha256': sha256}
