import contextlib
from datetime import date
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import Mock, patch
from oilgas.store import connect, initialize, record
from oilgas.sources import DataError, parse_yahoo, parse_csv, fetch_yahoo
from oilgas.cli import collect, main, coverage


class OilGasTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / 'test.sqlite'
        self.db = connect(self.path)
        initialize(self.db)
        self.series = dict(self.db.execute("SELECT * FROM series WHERE id='yahoo-wti'").fetchone())
        self.day = date(2020, 4, 20)

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def raw(self, prices=None):
        return json.dumps({'chart': {'error': None, 'result': [{
            'meta': {'symbol': 'CL=F', 'exchangeTimezoneName': 'America/New_York',
                     'currency': 'USD', 'exchangeName': 'NYM', 'shortName': 'WTI'},
            'timestamp': [1587398400, 1587484800, 1587571200],
            'indicators': {'quote': [{'close': [-37.63, None, 0] if prices is None else prices}],
                           'adjclose': [{'adjclose': [999, 999, 999]}]}}]}}).encode()

    def test_catalog_and_idempotent_init(self):
        initialize(self.db)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM routes').fetchone()[0], 20)
        self.assertEqual(len(coverage(self.db)), 18)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM routes WHERE benchmark_id='brent'").fetchone()[0], 2)

    def test_native_negative_zero_missing_and_no_adjusted(self):
        rows, warnings = parse_yahoo(self.raw(), self.series, self.day, date(2020,4,22))
        self.assertEqual([r[1] for r in rows], [-37.63, 0])
        self.assertTrue(warnings)
        self.assertTrue(all(r[2] is None for r in rows))

    def test_revision_idempotence_and_provenance(self):
        for price in [12,12,13]:
            record(self.db, 'yahoo-wti', self.day, self.day, [(str(self.day),price,None)])
        row = self.db.execute('SELECT * FROM prices').fetchone()
        self.assertEqual(row['price'],13)
        self.assertEqual(row['ingestion_id'],3)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM prices').fetchone()[0],1)

    def test_transaction_rolls_back(self):
        with self.assertRaises(sqlite3.IntegrityError):
            record(self.db, 'yahoo-wti', self.day, self.day, [(str(self.day),None,None)])
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM ingestions').fetchone()[0],0)

    def test_invalid_prices_metadata_and_lengths(self):
        for raw in [self.raw([1]), self.raw([1,float('inf'),3]), self.raw().replace(b'"USD"',b'"EUR"'), b'{}']:
            with self.assertRaises(DataError):
                parse_yahoo(raw,self.series,self.day,date(2020,4,22))

    def test_csv_atomic_validation(self):
        for raw in [b'date,price\n2020-01-01,1\n2020-01-02,NaN', b'date,price\n2020-01-01,1\n2020-01-01,2', b'date,price\n']:
            with self.assertRaises(DataError):
                parse_csv(raw)
        self.assertEqual(parse_csv(b'date,price,contract\n2020-01-01,-1,CLF20')[0],('2020-01-01',-1,'CLF20'))

    @patch('oilgas.sources.time.sleep')
    def test_http_retries_and_nonretryable(self, sleep):
        session=Mock()
        session.get.side_effect=[Mock(status_code=429),Mock(status_code=503),Mock(status_code=200,content=b'ok')]
        self.assertEqual(fetch_yahoo(session,'CL=F',self.day,self.day),b'ok')
        self.assertEqual(session.get.call_count,3)
        session.get.side_effect=None
        session.get.return_value=Mock(status_code=404)
        with self.assertRaises(DataError):
            fetch_yahoo(session,'CL=F',self.day,self.day)

    @patch('oilgas.cli.fetch_yahoo')
    def test_invalid_response_archived_and_no_price_written(self, fetch):
        fetch.return_value=b'invalid JSON'
        result=collect(self.db,self.series,self.day,self.day,Path(self.tmp.name)/'raw',Mock())
        self.assertEqual(result['status'],'error')
        row=self.db.execute('SELECT * FROM ingestions').fetchone()
        self.assertTrue(Path(row['raw_path']).exists())
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM prices').fetchone()[0],0)

    def test_query_alternative_includes_provenance(self):
        record(self.db,'yahoo-brent',self.day,self.day,[(str(self.day),25,None)])
        output=io.StringIO()
        with contextlib.redirect_stdout(output):
            code=main(['--db',str(self.path),'prices','--family','Crude Oil (Brut)','--zone','Europe / Afrique','--start',str(self.day),'--end',str(self.day)])
        self.assertEqual(code,0)
        row=json.loads(output.getvalue())[0]
        self.assertEqual(row['qualification'],'alternative')
        self.assertEqual(row['native_unit'],'USD/BBL')
        self.assertIn('retrieved_at',row)

    def test_external_csv_workflow_and_invalid_import(self):
        metadata = {k: v for k, v in self.series.items() if k != 'enabled'}
        metadata.update(id='manual-wti', provider='external-csv', price_field='settlement')
        spec = Path(self.tmp.name) / 'series.json'
        spec.write_text(json.dumps(metadata))
        prices = Path(self.tmp.name) / 'prices.csv'
        prices.write_text('date,price,contract\n2020-04-20,-37.63,CLK20\n')
        base = ['--db', str(self.path)]
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(base + ['register-series','--file',str(spec)]),0)
            for _ in range(2):
                self.assertEqual(main(base + ['import-csv','--series','manual-wti','--file',str(prices)]),0)
            prices.write_text('date,price\n2020-04-20,999\n2020-04-21,NaN\n')
            self.assertEqual(main(base + ['import-csv','--series','manual-wti','--file',str(prices)]),1)
        rows = self.db.execute("SELECT * FROM prices WHERE series_id='manual-wti'").fetchall()
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['price'],-37.63)
        self.assertEqual(rows[0]['contract'],'CLK20')

    def test_exchange_local_date(self):
        doc = json.loads(self.raw())
        result = doc['chart']['result'][0]
        # 2020-04-21 00:00 UTC is still 2020-04-20 in New York.
        result['timestamp'] = [1587427200]
        result['indicators']['quote'][0]['close'] = [-37.63]
        rows, _ = parse_yahoo(json.dumps(doc).encode(),self.series,self.day,self.day)
        self.assertEqual(rows[0][0],'2020-04-20')

    def test_missing_route_price_is_explicit(self):
        with contextlib.redirect_stderr(io.StringIO()) as output:
            code=main(['--db',str(self.path),'prices','--family','Crude Oil (Brut)','--zone','Orient','--start',str(self.day),'--end',str(self.day)])
        self.assertEqual(code,1)
        self.assertIn('Aucun prix',output.getvalue())


if __name__ == '__main__':
    unittest.main()
