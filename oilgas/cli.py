import argparse
import csv
from datetime import date, timedelta
import json
import math
from pathlib import Path
import sqlite3
import sys
import requests
from .sources import DataError, fetch_yahoo, parse_yahoo, parse_csv, finite_price
from .store import connect, initialize, archive, record


def emit(rows, fmt='json'):
    if fmt == 'json':
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    elif rows:
        writer = csv.DictWriter(sys.stdout, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def emit_deltas(rows, price):
    if len({row['series_id'] for row in rows}) != 1:
        raise DataError('Plusieurs séries disponibles ; sélectionner une série avec --series')
    ref = {key: rows[0][key] for key in ('logic', 'reference', 'expected_unit', 'instrument')}
    deltas = []
    for row in rows:
        if row['native_unit'] != ref['expected_unit']:
            raise DataError('Unité native incompatible avec expected_unit ; conversion nécessaire')
        reference_price = finite_price(row['price'])
        if reference_price == 0:
            raise DataError(f"Prix de référence nul le {row['date']} : delta indéfini")
        delta = (price - reference_price) / reference_price
        if not math.isfinite(delta):
            raise DataError(f"Delta non fini le {row['date']}")
        deltas.append(json.dumps([row['date'], delta], ensure_ascii=False, allow_nan=False))
    # Une paire par ligne pour garder la série lisible, même sur une longue période.
    reference = json.dumps(ref, ensure_ascii=False, indent=2).replace('\n', '\n  ')
    print('{\n  "ref": ' + reference + ',\n  "deltas": [\n    '
          + ',\n    '.join(deltas) + '\n  ]\n}')


def query(db, sql, params=()):
    return [dict(row) for row in db.execute(sql, params)]


def chunks(start, end):
    while start <= end:
        stop = min(end, date(start.year, 12, 31))
        yield start, stop
        start = stop + timedelta(days=1)


def selected(db, names):
    all_series = query(db, 'SELECT * FROM series ORDER BY id')
    by_id = {s['id']: s for s in all_series}
    if names:
        unknown = set(names) - by_id.keys()
        if unknown:
            raise DataError('Séries inconnues : ' + ', '.join(sorted(unknown)))
        return [by_id[name] for name in dict.fromkeys(names)]
    return [s for s in all_series if s['enabled'] and s['provider'] == 'yahoo']


def collect(db, series, start, end, raw_dir, session):
    path = digest = None
    try:
        if series['provider'] != 'yahoo':
            raise DataError('Cette série se charge par import-csv')
        raw = fetch_yahoo(session, series['symbol'], start, end)
        path, digest = archive(raw, raw_dir)
        rows, warnings = parse_yahoo(raw, series, start, end)
        return record(db, series['id'], start, end, rows, raw_path=path, sha256=digest, warnings=warnings)
    except DataError as exc:
        return record(db, series['id'], start, end, [], raw_path=path, sha256=digest, error=str(exc))


def coverage(db):
    return query(db, '''SELECT b.id AS benchmark_id,b.reference,b.expected_unit,
        s.id AS series_id,s.provider,s.symbol,s.unit AS native_unit,s.qualification,s.roll_rule,
        MIN(p.date) AS first_date,MAX(p.date) AS last_date,COUNT(p.date) AS observations,
        (SELECT status FROM ingestions i WHERE i.series_id=s.id ORDER BY i.id DESC LIMIT 1) AS last_status,
        (SELECT error FROM ingestions i WHERE i.series_id=s.id ORDER BY i.id DESC LIMIT 1) AS last_error
        FROM benchmarks b LEFT JOIN series s ON s.benchmark_id=b.id
        LEFT JOIN prices p ON p.series_id=s.id GROUP BY b.id,s.id ORDER BY b.id,s.id''')


def parser():
    p = argparse.ArgumentParser(description='Prix Oil & Gas natifs, génériques fournisseurs et provenance SQLite')
    p.add_argument('--db', default='data/oil_gas.sqlite')
    sub = p.add_subparsers(dest='command', required=True)
    sub.add_parser('init')
    for name in ('catalog', 'coverage'):
        cmd = sub.add_parser(name)
        cmd.add_argument('--format', choices=['json', 'csv'], default='json')
    for name in ('fetch', 'update'):
        cmd = sub.add_parser(name)
        cmd.add_argument('--series', nargs='+')
        if name == 'fetch':
            cmd.add_argument('--start', type=date.fromisoformat, default=date(2020, 1, 1))
            cmd.add_argument('--end', type=date.fromisoformat, default=date.today() - timedelta(days=1))
    for name in ('prices', 'deltas'):
        cmd = sub.add_parser(name)
        cmd.add_argument('--family', required=True)
        cmd.add_argument('--zone', required=True)
        cmd.add_argument('--start', required=True, type=date.fromisoformat)
        cmd.add_argument('--end', required=True, type=date.fromisoformat)
        cmd.add_argument('--series')
        if name == 'prices':
            cmd.add_argument('--format', choices=['json', 'csv'], default='json')
        else:
            cmd.add_argument('--price', required=True, type=float)
    cmd = sub.add_parser('import-csv')
    cmd.add_argument('--series', required=True)
    cmd.add_argument('--file', type=Path, required=True)
    cmd = sub.add_parser('register-series', help='Déclarer une série CSV et toutes ses métadonnées via JSON')
    cmd.add_argument('--file', required=True, type=Path)
    return p


def run(args, db):
    raw_dir = Path(args.db).resolve().parent / 'raw'
    if args.command == 'init':
        emit({'database': str(Path(args.db).resolve()), 'routes': db.execute('SELECT COUNT(*) FROM routes').fetchone()[0]})
    elif args.command == 'catalog':
        emit(query(db, '''SELECT r.*,b.reference,b.expected_unit,b.bloomberg_ticker,
            s.id AS series_id,s.provider,s.symbol,s.instrument,s.exchange,s.unit AS native_unit,
            s.price_field,s.roll_rule,s.qualification,s.notes
            FROM routes r JOIN benchmarks b ON b.id=r.benchmark_id
            LEFT JOIN series s ON s.benchmark_id=b.id ORDER BY r.family,r.zone,s.id'''), args.format)
    elif args.command == 'coverage':
        emit(coverage(db), args.format)
    elif args.command in ('fetch', 'update'):
        reports = []
        with requests.Session() as session:
            for series in selected(db, args.series):
                end = args.end if args.command == 'fetch' else date.today() - timedelta(days=1)
                start = args.start if args.command == 'fetch' else date(2020, 1, 1)
                if args.command == 'update':
                    last = db.execute('SELECT MAX(date) FROM prices WHERE series_id=?', (series['id'],)).fetchone()[0]
                    if last:
                        start = max(start, date.fromisoformat(last) - timedelta(days=9))
                if start > end or end >= date.today():
                    raise DataError('Période invalide : start <= end et end au plus tard hier')
                for a, b in chunks(start, end):
                    report = collect(db, series, a, b, raw_dir, session)
                    reports.append(report)
                    print(f"{series['id']} {a}/{b}: {report['status']} ({report['count']})", file=sys.stderr)
        emit(reports)
        return int(any(r['status'] in ('error', 'empty') for r in reports) or not reports)
    elif args.command in ('prices', 'deltas'):
        if args.start > args.end:
            raise DataError('start doit précéder end')
        route = db.execute('SELECT * FROM routes WHERE family=? AND zone=?', (args.family, args.zone)).fetchone()
        if route is None:
            raise DataError('Couple famille/zone inconnu ; consulter catalog')
        sql = '''SELECT r.family,r.zone,r.logic,b.reference,b.expected_unit,
            s.id AS series_id,s.provider,s.symbol,s.instrument,s.unit AS native_unit,
            s.price_field,s.roll_rule,s.qualification,s.notes,p.date,p.price,p.contract,
            i.retrieved_at,i.raw_path,i.sha256
            FROM routes r JOIN benchmarks b ON b.id=r.benchmark_id
            JOIN series s ON s.benchmark_id=b.id JOIN prices p ON p.series_id=s.id
            JOIN ingestions i ON i.id=p.ingestion_id
            WHERE r.family=? AND r.zone=? AND p.date BETWEEN ? AND ?'''
        values = [args.family, args.zone, str(args.start), str(args.end)]
        if args.series:
            sql += ' AND s.id=?'
            values.append(args.series)
        rows = query(db, sql + ' ORDER BY s.id,p.date', values)
        if not rows:
            raise DataError('Aucun prix disponible pour cette route, série et période ; consulter coverage')
        if args.command == 'deltas':
            emit_deltas(rows, finite_price(args.price))
        else:
            emit(rows, args.format)
    elif args.command == 'register-series':
        data = json.loads(args.file.read_text())
        columns = ['id','benchmark_id','provider','symbol','instrument','exchange','currency','unit',
                   'price_field','roll_rule','qualification','notes']
        if set(data) != set(columns) or any(not isinstance(data[k], str) or not data[k].strip() for k in columns):
            raise DataError('Métadonnées requises : ' + ', '.join(columns))
        if data['provider'] == 'yahoo':
            raise DataError('register-series est réservé aux sources CSV externes')
        with db:
            db.execute(f"INSERT INTO series ({','.join(columns)},enabled) VALUES ({','.join('?' for _ in columns)},0)",
                       [data[k] for k in columns])
        emit({'registered': data['id']})
    elif args.command == 'import-csv':
        series = selected(db, [args.series])[0]
        if series['provider'] == 'yahoo':
            raise DataError('Déclarer une série CSV distincte pour préserver la provenance Yahoo')
        raw = args.file.read_bytes()
        path, digest = archive(raw, raw_dir)
        try:
            rows = parse_csv(raw)
        except DataError as exc:
            record(db, series['id'], '', '', [], raw_path=path, sha256=digest, error=str(exc))
            raise
        emit(record(db, series['id'], rows[0][0], rows[-1][0], rows, raw_path=path, sha256=digest))
    return 0


def main(argv=None):
    p = parser()
    args = p.parse_args(argv)
    db = None
    try:
        db = connect(args.db)
        initialize(db)
        return run(args, db)
    except (DataError, OSError, sqlite3.Error, ValueError) as exc:
        print(f'Erreur : {exc}', file=sys.stderr)
        return 1
    finally:
        if db is not None:
            db.close()
