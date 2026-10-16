#!/usr/bin/env python3
"""Export des prix spot EIA autour d'une date, sans interpolation."""
import argparse
from datetime import date, datetime, timedelta, timezone
import json
import math
import os
from pathlib import Path
import sys
import time

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import requests
from dotenv import load_dotenv

BASE = 'https://api.eia.gov/v2/'
SERIES = {
    'wti': ('petroleum/pri/spt', 'RWTC', 'Pétrole WTI — Cushing', 'USD/baril'),
    'brent': ('petroleum/pri/spt', 'RBRTE', 'Pétrole Brent — Europe', 'USD/baril'),
    'henry-hub': ('natural-gas/pri/fut', 'RNGWHHD', 'Gaz naturel — Henry Hub', 'USD/MMBtu'),
}


class EIAError(Exception):
    """Erreur présentable sans URL contenant la clé."""


def request_page(session, url, params):
    for attempt in range(4):
        try:
            response = session.get(url, params=params, timeout=(10, 60))
        except requests.RequestException:
            if attempt == 3:
                raise EIAError('Connexion EIA impossible après 4 tentatives.') from None
        else:
            if response.status_code == 200:
                try:
                    payload = response.json()
                except ValueError:
                    raise EIAError('Réponse EIA non JSON.') from None
                if not isinstance(payload, dict) or payload.get('error'):
                    raise EIAError('L’API EIA a renvoyé une erreur.')
                return payload
            if response.status_code not in (429, 500, 502, 503, 504):
                message = ' Vérifiez EIA_API_KEY.' if response.status_code in (401, 403) else ''
                raise EIAError(f'Erreur EIA HTTP {response.status_code}.{message}')
            if attempt == 3:
                raise EIAError(f'EIA indisponible après 4 tentatives (HTTP {response.status_code}).')
        time.sleep(2 ** attempt)


def fetch_series(session, key, name, start, end):
    route, identifier, label, unit = SERIES[name]
    params = {'api_key': key, 'frequency': 'daily', 'data[0]': 'value',
              'facets[series][]': identifier, 'start': start.isoformat(),
              'end': end.isoformat(), 'sort[0][column]': 'period',
              'sort[0][direction]': 'asc', 'offset': 0, 'length': 5000}
    values, warnings, source_units = {}, [], set()
    while True:
        payload = request_page(session, BASE + route + '/data/', params)
        try:
            body = payload['response']
            rows = body['data']
            total = int(body['total'])
            if not isinstance(rows, list) or total < 0:
                raise ValueError
        except (KeyError, TypeError, ValueError):
            raise EIAError(f'{name} : structure de réponse EIA invalide.') from None
        if payload.get('warning') or body.get('warning'):
            warnings.append('L’API a signalé un avertissement ; pagination appliquée.')
        for row in rows:
            try:
                period = date.fromisoformat(row['period'])
                if row['series'] != identifier or not start <= period <= end:
                    raise ValueError
                raw = row.get('value')
                try:
                    value = float(raw)
                    if not math.isfinite(value):
                        value = None
                except (TypeError, ValueError):
                    value = None
                if period in values and values[period] != value:
                    raise ValueError
                values[period] = value
                if row.get('units'):
                    source_units.add(row['units'])
            except (KeyError, TypeError, ValueError):
                raise EIAError(f'{name} : observation incohérente dans la réponse EIA.') from None
        params['offset'] += len(rows)
        if params['offset'] >= total:
            break
        if not rows:
            raise EIAError(f'{name} : pagination interrompue avant la fin des résultats.')
    observations = [{'date': (start + timedelta(days=i)).isoformat(),
                     'value': values.get(start + timedelta(days=i))}
                    for i in range((end - start).days + 1)]
    available = [point['date'] for point in observations if point['value'] is not None]
    if not available:
        warnings.append('Aucune cotation disponible dans la fenêtre demandée.')
    elif available[0] > start.isoformat() or available[-1] < end.isoformat():
        warnings.append('Les cotations ne couvrent pas les deux bornes (jours sans cotation ou historique indisponible).')
    return {'name': name, 'label': label, 'series_id': identifier, 'price_type': 'spot',
            'source': BASE + route + '/data/', 'unit': unit,
            'source_units': sorted(source_units), 'first_available': available[0] if available else None,
            'last_available': available[-1] if available else None, 'observation_count': len(available),
            'warnings': list(dict.fromkeys(warnings)), 'observations': observations}


def plot_prices(document, path):
    series = document['series']
    fig, axes = plt.subplots(len(series), 1, figsize=(12, 3.4 * len(series)),
                             sharex=True, squeeze=False)
    anchor = date.fromisoformat(document['anchor'])
    for axis, item, color in zip(axes[:, 0], series, ['#1769aa', '#db7324', '#258259']):
        dates = [date.fromisoformat(p['date']) for p in item['observations']]
        prices = [p['value'] if p['value'] is not None else float('nan') for p in item['observations']]
        axis.plot(dates, prices, color=color, marker='.', markersize=4, linewidth=1.4, label='Prix spot quotidien')
        axis.axvline(anchor, color='#a12435', linestyle='--', label=f'Ancrage : {anchor}')
        axis.set_title(item['label'], loc='left')
        axis.set_ylabel(item['unit'])
        axis.grid(alpha=0.25)
        axis.legend(loc='best', fontsize=8)
        if not item['observation_count']:
            axis.text(.5, .5, 'Aucune cotation disponible', transform=axis.transAxes, ha='center')
    start, end = date.fromisoformat(document['start']), date.fromisoformat(document['end'])
    axes[-1, 0].set_xlim(start - timedelta(days=1) if start == end else start,
                         end + timedelta(days=1) if start == end else end)
    locator = mdates.AutoDateLocator()
    axes[-1, 0].xaxis.set_major_locator(locator)
    axes[-1, 0].xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))
    axes[-1, 0].set_xlabel('Date de cotation')
    fig.suptitle(f'Prix au comptant — fenêtre de ±{document["days"]} jours calendaires')
    fig.text(.5, .01, 'Source : EIA • Jours sans prix laissés vides • Aucune interpolation ni prévision', ha='center', fontsize=9)
    fig.tight_layout(rect=(0, .035, 1, .96))
    fig.savefig(path, dpi=180)
    plt.close(fig)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--anchor', required=True, type=date.fromisoformat, help='Date ISO YYYY-MM-DD')
    parser.add_argument('--days', required=True, type=int, help='Nombre de jours calendaires de chaque côté')
    parser.add_argument('--series', nargs='+', choices=SERIES, default=list(SERIES))
    parser.add_argument('--output-dir', type=Path, default=Path('outputs'))
    args = parser.parse_args(argv)
    if args.days < 0:
        parser.error('--days doit être positif ou nul.')
    try:
        start, end = args.anchor - timedelta(days=args.days), args.anchor + timedelta(days=args.days)
    except OverflowError:
        parser.error('Fenêtre hors des dates représentables.')
    load_dotenv(Path(__file__).resolve().parent / '.env', override=False)
    key = os.environ.get('EIA_API_KEY', '').strip()
    if not key:
        print('Erreur : renseignez EIA_API_KEY dans .env ou dans l’environnement.', file=sys.stderr)
        return 1
    names = list(dict.fromkeys(args.series))
    try:
        with requests.Session() as session:
            series = [fetch_series(session, key, name, start, end) for name in names]
        document = {'schema_version': 1, 'provider': 'EIA', 'frequency': 'daily',
                    'anchor': args.anchor.isoformat(), 'days': args.days,
                    'start': start.isoformat(), 'end': end.isoformat(),
                    'retrieved_at': datetime.now(timezone.utc).isoformat(), 'series': series}
        args.output_dir.mkdir(parents=True, exist_ok=True)
        stem = f'prices_{args.anchor}_{args.days}d_{"_".join(names)}'
        if any((args.output_dir / (stem + ext)).exists() for ext in ('.json', '.png')):
            stem += '_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        json_path, png_path = [args.output_dir / (stem + ext) for ext in ('.json', '.png')]
        json_path.write_text(json.dumps(document, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
        plot_prices(document, png_path)
        for item in series:
            for warning in item['warnings']:
                print(f'Avertissement [{item["name"]}] : {warning}', file=sys.stderr)
        print(f'JSON : {json_path}\nPNG  : {png_path}')
        return 0 if any(item['observation_count'] for item in series) else 1
    except EIAError as exc:
        print(f'Erreur : {exc}', file=sys.stderr)
        return 1
    except OSError:
        print('Erreur : impossible de lire la configuration ou d’écrire les sorties.', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
