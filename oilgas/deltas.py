"""Calcul et restitution compacte des deltas relatifs."""
import json
import math

from .sources import DataError, finite_price


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

