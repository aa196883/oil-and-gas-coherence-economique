import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from oilgas.cli import main as cli_main
from oilgas.deltas import calculate_deltas
from oilgas.store import connect, initialize, record, price_rows, register_series, selected
from oilgas.web import create_app, chart_data


class WebTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / 'web.sqlite'
        self.db = connect(self.path)
        initialize(self.db)
        record(self.db, 'yahoo-brent', '2024-01-02', '2024-01-04', [
            ('2024-01-02', 80, None), ('2024-01-03', 100, None), ('2024-01-04', 125, None)])
        record(self.db, 'yahoo-ttf', '2024-01-02', '2024-01-02', [('2024-01-02', 50, None)])
        self.app = create_app(self.path)
        self.app.testing = True
        self.client = self.app.test_client()
        self.form = dict(price='733', family='Crude Oil (Brut)', zone='Europe / Afrique',
                         series='', start='2024-01-01', end='2024-01-31', eur_usd='')

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_get_and_shared_calculation_without_data_mutation(self):
        before = list(self.db.iterdump())
        self.assertEqual(self.client.get('/').status_code, 200)
        response = self.client.post('/', data=self.form)
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('+25,00 %', html)
        self.assertIn('Zéro = prix égal à la référence', html)
        self.assertIn('-20,00 %', html)
        self.assertEqual(html.count('class="delta-bar"'), 3)
        rows = price_rows(self.db, self.form['family'], self.form['zone'], self.form['start'], self.form['end'])
        with contextlib.redirect_stdout(io.StringIO()) as out:
            code = cli_main(['--db', str(self.path), 'deltas', '--price', '733', '--family', self.form['family'],
                             '--zone', self.form['zone'], '--start', self.form['start'], '--end', self.form['end']])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out.getvalue()), calculate_deltas(rows, 733))
        self.assertEqual(list(self.db.iterdump()), before)

    def test_ui_exchange_default_and_cli_still_requires_rate(self):
        form = {**self.form, 'family': 'GNL (LNG)', 'zone': 'Europe', 'price': '853,4230432'}
        html = self.client.post('/', data=form).get_data(as_text=True)
        self.assertIn('1,12', html)
        self.assertIn('valeur par défaut', html)
        self.assertIn('0,00 %', html)
        explicit = self.client.post('/', data={**form, 'eur_usd': '1,10'})
        self.assertEqual(explicit.status_code, 200)
        self.assertIn('1,10', explicit.get_data(as_text=True))
        self.assertNotIn('valeur par défaut', explicit.get_data(as_text=True))
        with contextlib.redirect_stderr(io.StringIO()) as err:
            code = cli_main(['--db', str(self.path), 'deltas', '--price', '800', '--family', form['family'],
                             '--zone', form['zone'], '--start', form['start'], '--end', form['end']])
        self.assertEqual(code, 1)
        self.assertIn('--eur-usd est obligatoire', err.getvalue())

    def test_validation_and_absence_of_partial_chart(self):
        cases = [dict(price='nan'), dict(price=''), dict(start='bad'), dict(start='2024-02-01'),
                 dict(family='unknown'), dict(series='unknown'), dict(start='2025-01-01', end='2025-01-31'),
                 dict(family='GNL (LNG)', zone='Europe', eur_usd='0'),
                 dict(family='GNL (LNG)', zone='Europe', eur_usd='-1'),
                 dict(family='GNL (LNG)', zone='Europe', eur_usd='inf')]
        for changes in cases:
            with self.subTest(changes=changes):
                response = self.client.post('/', data={**self.form, **changes})
                self.assertEqual(response.status_code, 400)
                html = response.get_data(as_text=True)
                self.assertIn('role="alert"', html)
                self.assertNotIn('class="delta-bar"', html)

    def test_multiple_series_and_missing_conversion(self):
        source = {k:v for k,v in selected(self.db, ['yahoo-brent'])[0].items() if k != 'enabled'}
        source.update(id='external-brent', provider='csv')
        register_series(self.db, source)
        record(self.db, source['id'], '2024-01-02', '2024-01-02', [('2024-01-02', 100, None)])
        self.assertEqual(self.client.post('/', data=self.form).status_code, 400)
        self.assertEqual(self.client.post('/', data={**self.form, 'series':'external-brent'}).status_code, 200)
        with self.db:
            self.db.execute("UPDATE metadata SET unit='unknown' WHERE series_id='external-brent'")
        self.assertEqual(self.client.post('/', data={**self.form, 'series':'external-brent'}).status_code, 400)

    def test_chart_signed_symmetric_single_zero_and_long(self):
        chart = chart_data([['2024-01-01', .2], ['2024-01-02', -.2]])
        positive, negative = chart['bars']
        self.assertEqual(positive['color'], negative['color'])
        self.assertEqual(positive['height'], negative['height'])
        self.assertLess(positive['y'], chart['zero'])
        self.assertEqual(negative['y'], chart['zero'])
        self.assertAlmostEqual(chart['mean_abs'], .2)
        zero = chart_data([['2024-01-01', 0]])
        self.assertEqual(zero['bars'][0]['height'], 1)
        self.assertGreater(zero['ticks'][0]['value'], 0)
        self.assertEqual(len(zero['labels']), 1)
