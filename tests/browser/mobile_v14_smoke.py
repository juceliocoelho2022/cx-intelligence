"""Streamlit v1.4 BI acceptance in an actual 390 px mobile Chrome viewport."""
import os
import re
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

BASE_URL = os.getenv("CX_SMOKE_URL", "http://127.0.0.1:8501")


def check_bi_mobile():
    Path("artifacts").mkdir(exist_ok=True)
    with sync_playwright() as browser_engine:
        browser = browser_engine.chromium.launch(channel="chrome", headless=True,
                                                 args=["--no-sandbox"])
        page = browser.new_page(viewport={"width": 390, "height": 844},
                                device_scale_factor=2, is_mobile=True, has_touch=True)
        page.set_default_timeout(60_000)
        js_errors = []
        page.on("pageerror", lambda err: js_errors.append(str(err)))
        try:
            page.goto(BASE_URL, wait_until="domcontentloaded", timeout=90_000)
            expect(page.get_by_text("4.000", exact=True).first).to_be_visible()
            assert page.evaluate("window.innerWidth") == 390
            tab = page.get_by_role("tab", name=re.compile(r"BI v1\.4"))
            tab.scroll_into_view_if_needed()
            tab.click()
            expect(page.get_by_text("Business Intelligence — Relatório Executivo Comparativo")).to_be_visible()
            expect(page.get_by_text("Comparar os últimos")).to_be_visible()
            expect(page.get_by_text("Segmentar por")).to_be_visible()
            expect(page.get_by_text("Comparação entre segmentos")).to_be_visible()
            expect(page.get_by_text("Relatório executivo pronto para compartilhar")).to_be_visible()
            expect(page.get_by_text("Relatório comparativo (.md)")).to_be_visible()
            expect(page.get_by_text("Relatório para impressão (.html)")).to_be_visible()
            assert page.locator('[data-testid="stException"]').count() == 0
            assert not js_errors, f"Erros de JavaScript: {js_errors}"
            modebars = page.locator('[data-testid="stPlotlyChart"] .modebar')
            if modebars.count():
                assert modebars.first.evaluate(
                    "node => getComputedStyle(node).display"
                ) == "none", "A barra Plotly cobre o gráfico no celular"
            print("PASS: v1.4 BI mobile 390x844; controls, comparison, executive HTML/Markdown exports.")
        except Exception:
            page.screenshot(path="artifacts/cx_v14_mobile_failure.png", full_page=False)
            raise
        finally:
            browser.close()


if __name__ == "__main__":
    check_bi_mobile()
