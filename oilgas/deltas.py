"""Calcul et restitution compacte des deltas relatifs."""
import json
import math
from pathlib import Path

from .sources import DataError, finite_price


def positive_number(value, label):
    try:
        number = finite_price(value)
    except DataError:
        raise DataError(f'{label} doit être un nombre fini strictement positif') from None
    if number <= 0:
        raise DataError(f'{label} doit être un nombre fini strictement positif')
    return number


def conversion_factor(row, conversions, eur_usd):
    benchmark, unit = row['benchmark_id'], row['native_unit']
    conversion = conversions.get(benchmark, {}).get(unit)
    if conversion is None:
        raise DataError(f'Conversion vers USD/MT non renseignée : {benchmark}, {unit}')
    currency = row['currency']
    if currency not in ('USD', 'EUR') or currency != conversion['currency']:
        raise DataError(f'Devise incompatible avec la conversion : {currency}')
    factor = positive_number(conversion['factor'], 'Coefficient de conversion')
    if currency == 'EUR':
        if eur_usd is None:
            raise DataError('--eur-usd est obligatoire pour une référence en EUR (USD pour 1 EUR)')
        factor *= eur_usd
    return positive_number(factor, 'Coefficient de conversion avec change')


def calculate_deltas(rows, price, eur_usd=None):
    if not rows:
        raise DataError('Aucun prix disponible pour le calcul')
    if len({row['series_id'] for row in rows}) != 1:
        raise DataError('Plusieurs séries disponibles ; sélectionner une série avec --series')
    price = finite_price(price)
    if eur_usd is not None:
        eur_usd = positive_number(eur_usd, '--eur-usd')
    conversions = json.loads(Path(__file__).with_name('catalog.json').read_text())['conversions']
    ref = {key: rows[0][key] for key in ('logic', 'reference', 'expected_unit', 'instrument')}
    ref['expected_unit'] = 'USD/MT'
    deltas = []
    for row in rows:
        factor = conversion_factor(row, conversions, eur_usd)
        reference_price = finite_price(finite_price(row['price']) * factor)
        if reference_price == 0:
            raise DataError(f"Prix de référence nul le {row['date']} : delta indéfini")
        delta = (price - reference_price) / reference_price
        if not math.isfinite(delta):
            raise DataError(f"Delta non fini le {row['date']}")
        deltas.append([row['date'], delta])
    return {'ref': ref, 'deltas': deltas}


def emit_deltas(rows, price, eur_usd=None):
    result = calculate_deltas(rows, price, eur_usd)
    ref = result['ref']
    deltas = [json.dumps(pair, ensure_ascii=False, allow_nan=False) for pair in result['deltas']]
    # Une paire par ligne pour garder la série lisible, même sur une longue période.
    reference = json.dumps(ref, ensure_ascii=False, indent=2).replace('\n', '\n  ')
    print('{\n  "ref": ' + reference + ',\n  "deltas": [\n    '
          + ',\n    '.join(deltas) + '\n  ]\n}')

