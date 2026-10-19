"""Parcours desktop et captures : python -m tests.browser_checks."""
from datetime import date, timedelta
from pathlib import Path
import tempfile
import threading

from playwright.sync_api import sync_playwright, expect
from werkzeug.serving import make_server

from oilgas.store import connect, initialize, record
from oilgas.web import create_app


def main():
    output = Path('artifacts/ui')
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / 'browser.sqlite'
        db = connect(path)
        initialize(db)
        deltas = [.04, .08, .12, .03, -.05, -.12, -.22, -.14, -.07, .02, .06, .15, .19, .11, -.03, -.09, -.16, -.08, .04, .1, .07]
        observations = [(str(date(2024, 1, 2)+timedelta(days=i)), 100/(1+d), None) for i,d in enumerate(deltas)]
        record(db, 'yahoo-brent', observations[0][0], observations[-1][0], observations)
        record(db, 'yahoo-ttf', '2024-01-02', '2024-01-03', [('2024-01-02', 50, None), ('2024-01-03', 60, None)])
        db.close()
        server = make_server('127.0.0.1', 5003, create_app(path))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page(viewport={'width':1440, 'height':1000}, locale='fr-FR')
                errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.goto('http://127.0.0.1:5003')
                expect(page.locator('#fx-field')).to_be_hidden()
                page.screenshot(path=str(output / '01-initial.png'), full_page=True)
                page.get_by_label('Prix à comparer').fill('733')
                page.locator('#start').fill('2024-01-01')
                page.locator('#end').fill('2024-01-31')
                page.get_by_role('button', name='Calculer les deltas').click()
                expect(page.locator('.delta-bar')).to_have_count(21)
                expect(page.locator('.reference')).to_contain_text('ICE Brent')
                page.screenshot(path=str(output / '02-deltas.png'), full_page=True)
                page.locator('.delta-bar').first.hover()
                expect(page.locator('#chart-tooltip')).to_be_visible()
                page.locator('summary').click()
                expect(page.locator('tbody tr')).to_have_count(21)
                page.screenshot(path=str(output / '03-observations.png'), full_page=True)
                page.locator('#family').select_option('GNL (LNG)')
                page.locator('#zone').select_option('Europe')
                expect(page.locator('#fx-field')).to_be_visible()
                expect(page.locator('.delta-bar')).to_have_count(0)
                page.get_by_label('Prix à comparer').fill('800')
                page.get_by_role('button', name='Calculer les deltas').click()
                expect(page.locator('.fx-applied')).to_contain_text('1,12')
                expect(page.locator('.fx-applied')).to_contain_text('valeur par défaut')
                page.screenshot(path=str(output / '04-ttf.png'), full_page=True)
                page.locator('#eur_usd').fill('1,10')
                page.get_by_role('button', name='Calculer les deltas').click()
                expect(page.locator('.fx-applied')).to_contain_text('1,10')
                page.locator('#eur_usd').fill('0')
                page.get_by_role('button', name='Calculer les deltas').click()
                expect(page.get_by_role('alert')).to_be_visible()
                expect(page.locator('.delta-bar')).to_have_count(0)
                page.screenshot(path=str(output / '05-error.png'), full_page=True)
                page.locator('#family').select_option('Crude Oil (Brut)')
                page.locator('#zone').select_option('Orient')
                expect(page.locator('#coverage')).to_contain_text('Aucune donnée')
                page.get_by_role('button', name='Calculer les deltas').click()
                expect(page.get_by_role('alert')).to_contain_text('Aucun prix')
                page.set_viewport_size({'width':1280, 'height':900})
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                assert not errors, errors
                browser.close()
        finally:
            server.shutdown()
            thread.join()
            server.server_close()
    print(f'Parcours Playwright réussis. Captures : {output.resolve()}')


if __name__ == '__main__':
    main()
