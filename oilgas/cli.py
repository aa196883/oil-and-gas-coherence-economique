import argparse
import csv
from datetime import date, timedelta
import json
from pathlib import Path
import sqlite3
import sys
import requests
from .sources import DataError, fetch_yahoo, parse_yahoo, parse_csv, finite_price
from .deltas import emit_deltas
from .store import (connect, initialize, archive, record, selected, coverage,
                    catalog_rows, price_rows, register_series, route_count, last_date)


def emit(rows, fmt='json'):
    if fmt == 'json':
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    elif rows:
        writer = csv.DictWriter(sys.stdout, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def chunks(start, end):
    while start <= end:
        stop = min(end, date(start.year, 12, 31))
        yield start, stop
        start = stop + timedelta(days=1)


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


def parser():
    p = argparse.ArgumentParser(description='Prix Oil & Gas natifs, génériques fournisseurs et deltas SQLite')
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
            cmd.add_argument('--price', required=True, type=float, help='Prix à comparer en USD/MT (dollars par tonne métrique)')
            cmd.add_argument('--eur-usd', type=float, help='USD pour 1 EUR, constant sur la période ; obligatoire pour une référence en EUR')
    cmd = sub.add_parser('import-csv')
    cmd.add_argument('--series', required=True)
    cmd.add_argument('--file', type=Path, required=True)
    cmd = sub.add_parser('register-series', help='Déclarer une série CSV et toutes ses métadonnées via JSON')
    cmd.add_argument('--file', required=True, type=Path)
    return p


def run(args, db):
    raw_dir = Path(args.db).resolve().parent / 'raw'
    if args.command == 'init':
        emit({'database': str(Path(args.db).resolve()), 'routes': route_count(db)})
    elif args.command == 'catalog':
        emit(catalog_rows(db), args.format)
    elif args.command == 'coverage':
        emit(coverage(db), args.format)
    elif args.command in ('fetch', 'update'):
        reports = []
        with requests.Session() as session:
            for series in selected(db, args.series):
                end = args.end if args.command == 'fetch' else date.today() - timedelta(days=1)
                start = args.start if args.command == 'fetch' else date(2020, 1, 1)
                if args.command == 'update':
                    last = last_date(db, series['id'])
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
        rows = price_rows(db, args.family, args.zone, args.start, args.end, args.series)
        if args.command == 'deltas':
            emit_deltas(rows, finite_price(args.price), args.eur_usd)
        else:
            emit(rows, args.format)
    elif args.command == 'register-series':
        data = json.loads(args.file.read_text())
        register_series(db, data)
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
