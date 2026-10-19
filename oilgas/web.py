"""Interface locale des deltas : python -m oilgas.web (port 5003)."""
import argparse
from datetime import date, timedelta
import math
from pathlib import Path
import sqlite3

from flask import Flask, render_template, request

from .deltas import calculate_deltas
from .sources import DataError, finite_price
from .store import catalog_rows, connect, initialize, price_rows


def chart_data(deltas):
    """Barres indépendantes, axe symétrique, teinte liée à |delta| sans seuil métier."""
    values = [value for _, value in deltas]
    peak = max(abs(value) for value in values)
    scale = max(peak, 0.01)
    step = 10 ** math.floor(math.log10(scale))
    limit = math.ceil(scale / step) * step
    width = max(840, len(deltas) * 12 + 100)
    left, right, zero, half = 70, width - 24, 178, 150
    first, last = date.fromisoformat(deltas[0][0]), date.fromisoformat(deltas[-1][0])
    span = max((last - first).days, 1)
    bar_width = max(2, min(24, (right - left) / (span + 1) * 0.65))
    bars = []
    for day, value in deltas:
        x = (left + right) / 2 if len(deltas) == 1 else left + bar_width / 2 + (date.fromisoformat(day) - first).days / span * (right - left - bar_width)
        height = abs(value) / limit * half
        intensity = abs(value) / (abs(value) + 0.15)
        light, dark = (221, 182, 151), (153, 49, 36)
        color = '#%02x%02x%02x' % tuple(round(a + (b - a) * intensity) for a, b in zip(light, dark))
        bars.append(dict(day=day, value=value, x=x-bar_width/2, y=zero-height if value > 0 else zero,
                         width=bar_width, height=max(height, 1), color=color))
    indexes = sorted({round(i * (len(deltas)-1) / min(6, max(1, len(deltas)-1))) for i in range(min(6, len(deltas)-1)+1)})
    ticks = [dict(y=zero - fraction * half, value=fraction * limit) for fraction in (1, .5, 0, -.5, -1)]
    labels = [dict(x=bars[i]['x']+bar_width/2, day=bars[i]['day']) for i in indexes]
    return dict(width=width, zero=zero, ticks=ticks, bars=bars, labels=labels,
                mean_abs=math.fsum(abs(v)/len(values) for v in values),
                peak=max(deltas, key=lambda pair: abs(pair[1])))


def create_app(database='data/oil_gas.sqlite'):
    app = Flask(__name__)
    app.config.update(DATABASE=str(Path(database).resolve()), MAX_CONTENT_LENGTH=16_384)
    db = connect(app.config['DATABASE'])
    try:
        initialize(db)
    finally:
        db.close()

    @app.template_filter('percent')
    def percent(value, signed=True):
        return (format(value * 100, '+.2f' if signed and value else '.2f').replace('.', ',') + ' %')

    @app.template_filter('number')
    def number(value):
        return f'{value:,.2f}'.replace(',', '\u202f').replace('.', ',')

    @app.template_filter('day')
    def day(value):
        return date.fromisoformat(value).strftime('%d/%m/%Y')

    @app.route('/', methods=['GET', 'POST'])
    def index():
        db = connect(app.config['DATABASE'])
        try:
            routes = catalog_rows(db)
            default = next((r for r in routes if r['family'] == 'Crude Oil (Brut)' and r['zone'] == 'Europe / Afrique'), routes[0])
            end = date.fromisoformat(default['end_date']) if default['end_date'] else date.today() - timedelta(days=1)
            form = dict(family=default['family'], zone=default['zone'], series='', price='',
                        start=str(end-timedelta(days=29)), end=str(end), eur_usd='')
            result = error = chart = fx = None
            used_default_fx = False
            status = 200
            if request.method == 'POST':
                form = {key: request.form.get(key, '').strip() for key in form}
                try:
                    try:
                        start, end = date.fromisoformat(form['start']), date.fromisoformat(form['end'])
                    except ValueError:
                        raise DataError('Renseignez deux dates valides.') from None
                    rows = price_rows(db, form['family'], form['zone'], start, end, form['series'] or None)
                    needs_fx = any(row['currency'] == 'EUR' for row in rows)
                    if form['eur_usd']:
                        fx = finite_price(form['eur_usd'].replace(',', '.'))
                    elif needs_fx:
                        fx, used_default_fx = 1.12, True
                    price = finite_price(form['price'].replace(',', '.'))
                    result = calculate_deltas(rows, price, fx)
                    chart = chart_data(result['deltas'])
                    if not needs_fx:
                        fx = None
                except (DataError, ValueError, OverflowError) as exc:
                    result = chart = None
                    error = (str(exc).replace('--eur-usd', 'Le taux EUR/USD')
                             .replace(' ; consulter coverage', '').replace(' ; consulter catalog', '')
                             .replace('sélectionner une série avec --series', 'choisissez une valeur dans le champ Série'))
                    status = 400
            families = list(dict.fromkeys(r['family'] for r in routes))
            zones = list(dict.fromkeys(r['zone'] for r in routes if r['family'] == form['family']))
            sources = [r for r in routes if r['family'] == form['family'] and r['zone'] == form['zone'] and r['series_id']]
            needs_fx = any(r['currency'] == 'EUR' for r in sources if not form['series'] or r['series_id'] == form['series'])
            return render_template('deltas.html', form=form, routes=routes, families=families, zones=zones,
                                   sources=sources, needs_fx=needs_fx, result=result, error=error, chart=chart,
                                   fx=fx, used_default_fx=used_default_fx), status
        except sqlite3.Error:
            app.logger.exception('Lecture SQLite impossible')
            return 'Base de données indisponible.', 503
        finally:
            db.close()

    return app


def main():
    parser = argparse.ArgumentParser(description='Interface locale des deltas sur http://127.0.0.1:5003')
    parser.add_argument('--db', default='data/oil_gas.sqlite')
    args = parser.parse_args()
    create_app(args.db).run(host='127.0.0.1', port=5003, debug=False)


if __name__ == '__main__':
    main()
