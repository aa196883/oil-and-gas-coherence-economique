import contextlib
from datetime import date
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import eia_prices as app


class PricesTests(unittest.TestCase):
    def page(self, rows, total=None):
        return {'response': {'data': rows, 'total': str(len(rows) if total is None else total)}}

    def row(self, day, value):
        return {'period': day, 'value': value, 'series': 'RWTC', 'units': '$/BBL'}

    def test_calendar_leap_year_and_pagination(self):
        pages = [self.page([self.row('2024-02-28', '-2')], 3),
                 self.page([self.row('2024-02-29', 'NaN'), self.row('2024-03-02', '12.5')], 3)]
        offsets = []
        def get_page(session, url, params):
            offsets.append(params['offset'])
            return pages.pop(0)
        with patch.object(app, 'request_page', side_effect=get_page):
            item = app.fetch_series(Mock(), 'secret', 'wti', date(2024, 2, 28), date(2024, 3, 2))
        self.assertEqual(offsets, [0, 1])
        self.assertEqual([p['value'] for p in item['observations']], [-2, None, None, 12.5])
        self.assertEqual(item['observation_count'], 2)
        self.assertNotIn('secret', json.dumps(item))

    def test_empty_page_before_total_is_error(self):
        with patch.object(app, 'request_page', return_value=self.page([], 1)):
            with self.assertRaises(app.EIAError):
                app.fetch_series(Mock(), 'secret', 'wti', date(2024, 1, 1), date(2024, 1, 2))

    def test_auth_error_no_secret(self):
        session = Mock()
        session.get.return_value.status_code = 403
        session.get.return_value.text = 'secret'
        with self.assertRaises(app.EIAError) as error:
            app.request_page(session, 'url', {'api_key': 'secret'})
        self.assertNotIn('secret', str(error.exception))
        self.assertIn('EIA_API_KEY', str(error.exception))

    def test_retry(self):
        session = Mock()
        session.get.side_effect = [app.requests.Timeout('secret'), Mock(status_code=200, json=lambda: self.page([]))]
        with patch.object(app.time, 'sleep'):
            self.assertEqual(app.request_page(session, 'url', {}), self.page([]))

    def test_exports_weekend_anchor_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            args = ['--anchor', '2024-01-14', '--days', '2', '--series', 'wti', '--output-dir', directory]
            with patch.object(app, 'load_dotenv'), patch.dict(app.os.environ, {'EIA_API_KEY': 'secret'}), \
                 patch.object(app, 'request_page', return_value=self.page([self.row('2024-01-12', '70'), self.row('2024-01-16', '72')])), \
                 contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(app.main(args), 0)
                self.assertEqual(app.main(args), 0)
            files = list(Path(directory).glob('*.json'))
            self.assertEqual(len(files), 2)
            doc = json.loads(files[0].read_text())
            self.assertEqual(len(doc['series'][0]['observations']), 5)
            self.assertIsNone(doc['series'][0]['observations'][2]['value'])
            self.assertNotIn('secret', files[0].read_text())
            for path in Path(directory).glob('*.png'):
                self.assertEqual(path.read_bytes()[:8], b'\x89PNG\r\n\x1a\n')

    def test_empty_single_day_exports_and_failure_status(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(app, 'load_dotenv'), \
             patch.dict(app.os.environ, {'EIA_API_KEY': 'secret'}), \
             patch.object(app, 'request_page', return_value=self.page([])), \
             contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(app.main(['--anchor', '2024-01-14', '--days', '0', '--series', 'wti', '--output-dir', directory]), 1)
            self.assertEqual(len(list(Path(directory).glob('*.png'))), 1)


if __name__ == '__main__':
    unittest.main()
