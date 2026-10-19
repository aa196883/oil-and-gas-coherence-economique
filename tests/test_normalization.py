"""Conversions conventionnelles explicites, sans réseau ni écriture des prix."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from oilgas.cli import main
from oilgas.deltas import emit_deltas
from oilgas.sources import DataError
from oilgas.store import connect, initialize, record, register_series, selected


class NormalizationTests(unittest.TestCase):
    def row(self, benchmark='brent', unit='USD/BBL', price=100, currency='USD'):
        return dict(benchmark_id=benchmark, native_unit=unit, price=price, currency=currency,
                    date='2024-01-02', series_id='test', logic='POL', reference='Test',
                    expected_unit=unit, instrument='Test')

    def delta(self, row, price, eur_usd=None):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            emit_deltas([row], price, eur_usd)
        return json.loads(out.getvalue())

    def test_explicit_conversions(self):
        cases = [
            ('brent', 'USD/BBL', 100, 733),
            ('wti', 'USD/BBL', 100, 733),
            ('oman', 'USD/BBL', 100, 733),
            ('ulsd', 'USD/Gallon', 2, 625.8),
            ('ulsd', 'US Cents/Gallon', 200, 625.8),
            ('rbob', 'USD/Gallon', 2, 714),
            ('rbob', 'US Cents/Gallon', 200, 714),
            ('propane', 'US Cents/Gallon', 100, 520.8),
            ('gasoil-ice', 'USD/MT', 700, 700),
            ('gasoil-singapore', 'USD/MT', 700, 700),
            ('jkm', 'USD/MMBtu', 10, 520),
            ('henry-hub', 'USD/MMBtu', 10, 520),
        ]
        for benchmark, unit, native, normalized in cases:
            with self.subTest(benchmark=benchmark, unit=unit):
                row = self.row(benchmark, unit, native)
                output = self.delta(row, normalized)
                self.assertAlmostEqual(output['deltas'][0][1], 0)
                self.assertEqual(output['ref']['expected_unit'], 'USD/MT')
                self.assertEqual(row['price'], native)
                self.assertEqual(row['expected_unit'], unit)

    def test_ttf_energy_and_explicit_exchange(self):
        row = self.row('ttf', 'EUR/MWh', 50, 'EUR')
        # 52 MMBtu/tonne × 0,2930711 MWh/MMBtu × 50 EUR/MWh × 1,10 USD/EUR.
        self.assertAlmostEqual(self.delta(row, 838.183346, 1.1)['deltas'][0][1], 0)
        self.assertAlmostEqual(self.delta(row, 1676.366692, 1.1)['deltas'][0][1], 1)
        with self.assertRaisesRegex(DataError, '--eur-usd est obligatoire'):
            self.delta(row, 1000)
        self.assertEqual(self.delta(self.row(), 733, 2)['deltas'][0][1], 0)

    def test_invalid_rates_and_coefficients(self):
        for bad in (0, -1, float('nan'), float('inf'), True):
            with self.subTest(bad=bad):
                with self.assertRaisesRegex(DataError, '--eur-usd'):
                    self.delta(self.row(), 733, bad)
                catalog = {'conversions': {'brent': {'USD/BBL': {'currency': 'USD', 'factor': bad}}}}
                with patch('oilgas.deltas.Path.read_text', return_value=json.dumps(catalog)):
                    with self.assertRaisesRegex(DataError, 'Coefficient'):
                        self.delta(self.row(), 733)

    def test_missing_conversion_and_incompatible_currency(self):
        for row in (self.row('jet-singapore'), self.row('unknown'), self.row(unit='usd/bbl'),
                    self.row(unit='USD/MT')):
            with self.subTest(row=row), self.assertRaisesRegex(DataError, 'non renseignée'):
                self.delta(row, 733)
        for currency in ('EUR', 'GBP', None):
            with self.subTest(currency=currency), self.assertRaisesRegex(DataError, 'Devise'):
                self.delta(self.row(currency=currency), 733, 1.1)

    def test_negative_zero_and_nonfinite_results_without_partial_output(self):
        self.assertEqual(self.delta(self.row(price=-100), 733)['deltas'][0][1], -2)
        self.assertEqual(self.delta(self.row(), 0)['deltas'][0][1], -1)
        for bad in (0, float('inf'), float('nan'), 1e308):
            with self.subTest(bad=bad), contextlib.redirect_stdout(io.StringIO()) as out:
                with self.assertRaises(DataError):
                    emit_deltas([self.row(), self.row(price=bad)], 733)
                self.assertEqual(out.getvalue(), '')
        with self.assertRaises(DataError):
            self.delta(self.row(price=1e-300), 1e308)

    def test_cli_shared_brent_external_sources_and_unchanged_storage(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'test.sqlite'
            db = connect(path)
            try:
                initialize(db)
                record(db, 'yahoo-brent', '2024-01-02', '2024-01-02', [('2024-01-02', 100, None)])
                record(db, 'yahoo-ttf', '2024-01-02', '2024-01-03', [
                    ('2024-01-02', 50, None), ('2024-01-03', 100, None)])
                source = {k: v for k, v in selected(db, ['yahoo-ulsd'])[0].items() if k != 'enabled'}
                source.update(id='csv-cents', provider='csv', unit='US Cents/Gallon')
                register_series(db, source)
                record(db, 'csv-cents', '2024-01-02', '2024-01-02', [('2024-01-02', 200, None)])
                before = list(db.iterdump())

                def call(command, family, zone, *options):
                    with contextlib.redirect_stdout(io.StringIO()) as out, contextlib.redirect_stderr(io.StringIO()) as err:
                        code = main(['--db', str(path), command, '--family', family, '--zone', zone,
                                     '--start', '2024-01-01', '--end', '2024-01-31', *options])
                    return code, out.getvalue(), err.getvalue()

                for family, zone in [('Crude Oil (Brut)', 'Europe / Afrique'), ('Gasoline (Essence)', 'Reste du Monde')]:
                    code, output, _ = call('deltas', family, zone, '--price', '733')
                    self.assertEqual(code, 0)
                    self.assertEqual(json.loads(output)['deltas'][0][1], 0)
                    code, output, _ = call('prices', family, zone)
                    self.assertEqual(code, 0)
                    self.assertEqual(json.loads(output)[0]['price'], 100)
                    self.assertEqual(json.loads(output)[0]['native_unit'], 'USD/BBL')
                code, output, _ = call('deltas', 'Gasoil / Diesel', 'Amériques', '--series', 'csv-cents', '--price', '625.8')
                self.assertEqual(code, 0)
                self.assertAlmostEqual(json.loads(output)['deltas'][0][1], 0)
                code, output, err = call('deltas', 'GNL (LNG)', 'Europe', '--price', '838.183346')
                self.assertEqual((code, output), (1, ''))
                self.assertIn('--eur-usd', err)
                code, output, _ = call('deltas', 'GNL (LNG)', 'Europe', '--price', '838.183346', '--eur-usd', '1.1')
                self.assertEqual(code, 0)
                for row, expected in zip(json.loads(output)['deltas'], [0, -0.5]):
                    self.assertAlmostEqual(row[1], expected)
                self.assertEqual(list(db.iterdump()), before)
            finally:
                db.close()
