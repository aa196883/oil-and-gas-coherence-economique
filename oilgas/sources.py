"""Accès Yahoo et validation des données ; aucune conversion de prix."""
import csv
from datetime import date, datetime, time as day_time, timedelta, timezone
import io
import json
import math
import time
from urllib.parse import quote
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import requests


class DataError(Exception):
    pass


def fetch_yahoo(session, symbol, start, end):
    endpoint = 'https://query1.finance.yahoo.com/v8/finance/chart/' + quote(symbol, safe='')
    params = {'period1': int(datetime.combine(start, day_time(), timezone.utc).timestamp()),
              'period2': int(datetime.combine(end + timedelta(days=1), day_time(), timezone.utc).timestamp()),
              'interval': '1d'}
    for attempt in range(4):
        try:
            response = session.get(endpoint, params=params, headers={'User-Agent': 'Mozilla/5.0'}, timeout=30)
        except requests.RequestException:
            if attempt == 3:
                raise DataError('Échec réseau Yahoo après 4 tentatives') from None
        else:
            if response.status_code == 200:
                return response.content
            if response.status_code not in (429, 500, 502, 503, 504):
                raise DataError(f'Yahoo HTTP {response.status_code}')
            if attempt == 3:
                raise DataError(f'Yahoo HTTP {response.status_code} après 4 tentatives')
        time.sleep(2 ** attempt)
    raise DataError('Échec Yahoo')


def finite_price(value):
    if isinstance(value, bool):
        raise DataError('Prix booléen invalide')
    try:
        result = float(value)
    except (TypeError, ValueError):
        raise DataError('Prix non numérique') from None
    if not math.isfinite(result):
        raise DataError('Prix non fini')
    return result


def parse_yahoo(raw, series, start, end):
    try:
        document = json.loads(raw)
        chart = document['chart']
        if chart.get('error'):
            raise DataError('Erreur applicative Yahoo')
        result = chart['result'][0]
        meta = result['meta']
        tz = ZoneInfo(meta['exchangeTimezoneName'])
        if meta.get('symbol') != series['symbol']:
            raise DataError('Symbole retourné différent du symbole demandé')
        for key, expected in (('currency', series['currency']), ('exchangeName', series['exchange'])):
            if meta.get(key) and meta[key] != expected:
                raise DataError(f'Métadonnée {key} incompatible avec le catalogue')
        stamps = result.get('timestamp') or []
        prices = result['indicators']['quote'][0].get('close') or []
        if len(stamps) != len(prices):
            raise DataError('Longueurs dates/prix incohérentes')
        observations = {}
        missing = 0
        for stamp, value in zip(stamps, prices):
            d = datetime.fromtimestamp(stamp, tz).date()
            if not start <= d <= end:
                continue
            if value is None:
                missing += 1
                continue
            price = finite_price(value)
            if d.isoformat() in observations:
                raise DataError('Date dupliquée dans la réponse Yahoo')
            observations[d.isoformat()] = (d.isoformat(), price, None)
        warnings = []
        if missing:
            warnings.append(f'{missing} observations sans clôture ignorées')
        if not meta.get('currency') or not meta.get('shortName'):
            warnings.append('Métadonnées fournisseur incomplètes ; qualification du catalogue conservée')
        rows = sorted(observations.values())
        # Pas de calendrier boursier implicite : les bornes manquantes sont signalées sans cause supposée.
        if rows and (rows[0][0] != str(start) or rows[-1][0] != str(end)):
            warnings.append(f'Bornes observées {rows[0][0]} / {rows[-1][0]} différentes des bornes demandées')
        return rows, warnings
    except DataError:
        raise
    except (KeyError, IndexError, TypeError, ValueError, OverflowError, ZoneInfoNotFoundError):
        raise DataError('Réponse Yahoo invalide ou métadonnées temporelles absentes') from None


def parse_csv(raw):
    try:
        reader = csv.DictReader(io.StringIO(raw.decode('utf-8-sig')))
        if not reader.fieldnames or not {'date', 'price'} <= set(reader.fieldnames):
            raise DataError('Colonnes CSV requises : date,price ; contract facultative')
        rows = {}
        for row in reader:
            d = date.fromisoformat(row['date']).isoformat()
            if d in rows:
                raise DataError('Date dupliquée dans le CSV')
            rows[d] = (d, finite_price(row['price']), row.get('contract') or None)
        if not rows:
            raise DataError('CSV vide')
        return sorted(rows.values())
    except DataError:
        raise
    except (ValueError, TypeError, UnicodeError, csv.Error):
        raise DataError('CSV invalide') from None
