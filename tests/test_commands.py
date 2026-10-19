"""Parcours CLI et invariants du stockage à deux tables, hors réseau."""
import contextlib
import csv
from datetime import date
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from oilgas.cli import main
from oilgas.sources import DataError
from oilgas.store import connect, initialize, record, register_series, selected


class CommandTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / 'prices.sqlite'
        self.db = connect(self.path)
        initialize(self.db)

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def command(self, *args):
        output, errors = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            code = main(['--db', str(self.path), *args])
        return code, output.getvalue(), errors.getvalue()

    def external(self, benchmark='brent'):
        source = {k: v for k, v in selected(self.db, ['yahoo-brent'])[0].items() if k != 'enabled'}
        source.update(id='csv-test', provider='csv', benchmark_id=benchmark)
        return source

    def test_exact_two_tables_and_foreign_key(self):
        tables = {r[0] for r in self.db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertEqual(tables, {'metadata', 'prices'})
        columns = [r['name'] for r in self.db.execute('PRAGMA table_info(prices)')]
        self.assertEqual(columns, ['date', 'price', 'metadata_id'])
        with self.assertRaises(sqlite3.IntegrityError), self.db:
            self.db.execute("INSERT INTO prices VALUES ('2024-01-01',80,-1)")

    def test_shared_reference_bounds_revision_and_atomic_failure(self):
        record(self.db, 'yahoo-brent', '2024-01-02', '2024-01-31', [
            ('2024-01-31', 90, None), ('2024-01-02', 80, None)])
        record(self.db, 'yahoo-brent', '2024-01-02', '2024-01-02', [('2024-01-02', 81, None)])
        rows = self.db.execute("SELECT * FROM metadata WHERE series_id='yahoo-brent'").fetchall()
        self.assertEqual(len(rows), 2)
        for row in rows:
            self.assertEqual((row['start_date'], row['end_date']), ('2024-01-02', '2024-01-31'))
            self.assertEqual([tuple(p) for p in self.db.execute(
                'SELECT date,price FROM prices WHERE metadata_id=? ORDER BY date', (row['id'],))],
                [('2024-01-02', 81), ('2024-01-31', 90)])
        with self.assertRaises(sqlite3.IntegrityError):
            record(self.db, 'yahoo-brent', '2023-01-01', '2025-01-01', [
                ('2023-01-01', 1, None), ('2025-01-01', None, None)])
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM prices').fetchone()[0], 4)
        record(self.db, 'yahoo-brent', '', '', [], error='Échec réseau')
        after = self.db.execute("SELECT * FROM metadata WHERE series_id='yahoo-brent'").fetchall()
        self.assertEqual([(r['start_date'], r['end_date']) for r in after],
                         [(r['start_date'], r['end_date']) for r in rows])
        self.assertTrue(all(r['last_error'] == 'Échec réseau' for r in after))

    def test_register_empty_benchmark_and_idempotent_initialization(self):
        register_series(self.db, self.external('gasoil-ice'))
        initialize(self.db)
        rows = self.db.execute("SELECT * FROM metadata WHERE benchmark_id='gasoil-ice'").fetchall()
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(r['series_id'] == 'csv-test' for r in rows))
        record(self.db, 'csv-test', '2024-01-02', '2024-01-02', [('2024-01-02', 80, None)])
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM prices').fetchone()[0], 2)
        with self.assertRaises(DataError):
            register_series(self.db, self.external('gasoil-ice'))
        self.assertEqual(len(selected(self.db, ['csv-test'])), 1)

    def test_register_invalid_metadata_is_atomic(self):
        invalid = [[], {}, self.external('unknown'), {**self.external(), 'provider': 'yahoo'}]
        for source in invalid:
            with self.subTest(source=source), self.assertRaises(DataError):
                register_series(self.db, source)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM metadata').fetchone()[0], 20)

    def test_init_catalog_coverage_and_prices_csv(self):
        self.assertEqual(json.loads(self.command('init')[1])['routes'], 20)
        code, output, _ = self.command('catalog', '--format', 'csv')
        self.assertEqual(code, 0)
        self.assertEqual(len(list(csv.DictReader(io.StringIO(output)))), 20)
        record(self.db, 'yahoo-brent', '2024-01-02', '2024-01-02', [('2024-01-02', 80, None)])
        coverage = json.loads(self.command('coverage')[1])
        brent = [r for r in coverage if r['series_id'] == 'yahoo-brent']
        self.assertEqual(len(brent), 2)
        self.assertTrue(all(r['observations'] == 1 and r['start_date'] == '2024-01-02' for r in brent))
        for family, zone in [('Crude Oil (Brut)', 'Europe / Afrique'), ('Gasoline (Essence)', 'Reste du Monde')]:
            code, output, _ = self.command('prices', '--family', family, '--zone', zone,
                                          '--start', '2024-01-01', '--end', '2024-01-31', '--format', 'csv')
            self.assertEqual(code, 0)
            self.assertEqual(float(list(csv.DictReader(io.StringIO(output)))[0]['price']), 80)

    @patch('oilgas.cli.fetch_yahoo', return_value=b'raw')
    @patch('oilgas.cli.parse_yahoo')
    def test_fetch_once_per_series_and_update_window(self, parse, fetch):
        parse.return_value = ([('2024-01-10', 80, None)], [])
        code, output, _ = self.command('fetch', '--series', 'yahoo-brent', 'yahoo-brent',
                                      '--start', '2024-01-01', '--end', '2024-01-31')
        self.assertEqual(code, 0)
        self.assertEqual(len(json.loads(output)), 1)
        self.assertEqual(fetch.call_count, 1)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM prices').fetchone()[0], 2)
        parse.return_value = ([], [])
        fetch.reset_mock()
        code, _, _ = self.command('update', '--series', 'yahoo-brent')
        self.assertEqual(code, 1)  # Réponses vides, conservant les observations existantes.
        self.assertEqual(fetch.call_args_list[0].args[2], date(2024, 1, 1))
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM prices').fetchone()[0], 2)

    @patch('oilgas.cli.fetch_yahoo', return_value=b'raw')
    @patch('oilgas.cli.parse_yahoo')
    def test_fetch_year_chunks_and_partial_status(self, parse, fetch):
        parse.side_effect = [([('2023-12-29', 80, None)], ['Bornes manquantes']),
                             ([('2024-01-02', 81, None)], [])]
        code, output, _ = self.command('fetch', '--series', 'yahoo-brent',
                                      '--start', '2023-12-29', '--end', '2024-01-02')
        self.assertEqual(code, 0)
        self.assertEqual([r['status'] for r in json.loads(output)], ['partial', 'ok'])
        self.assertEqual([(c.args[2], c.args[3]) for c in fetch.call_args_list],
                         [(date(2023, 12, 29), date(2023, 12, 31)), (date(2024, 1, 1), date(2024, 1, 2))])

    @patch('oilgas.cli.fetch_yahoo')
    def test_invalid_fetch_and_protected_yahoo_import(self, fetch):
        self.assertEqual(self.command('fetch', '--series', 'unknown')[0], 1)
        self.assertEqual(self.command('fetch', '--series', 'yahoo-brent', '--start', '2024-02-01', '--end', '2024-01-01')[0], 1)
        self.assertEqual(self.command('fetch', '--series', 'yahoo-brent', '--end', str(date.today()))[0], 1)
        self.assertEqual(self.command('import-csv', '--series', 'yahoo-brent', '--file', 'unused.csv')[0], 1)
        fetch.assert_not_called()
