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
            # Render Free instances may cold-start and generate 4,000 tickets on first visit.\n            expect(page.get_by_text("4.000", exact=True).first).to_be_visible(timeout=110_000)
            assert page.evaluate("window.innerWidth") == 390
            tab = page.get_by_role("tab", name=re.compile(r"BI v1\.4"))
            tab.scroll_into_view_if_needed()
            tab.click()
            expect(page.get_by_text("Business Intelligence — Relatório Executivo Comparativo")).to_be_visible(timeout=45_000)
            expect(page.get_by_text("Comparar os últimos")).to_be_visible(timeout=45_000)
            expect(page.get_by_text("Segmentar por")).to_be_visible(timeout=45_000)
            expect(page.get_by_text("Comparação entre segmentos")).to_be_visible(timeout=45_000)
            expect(page.get_by_text("Relatório executivo pronto para compartilhar")).to_be_visible(timeout=45_000)
            expect(page.get_by_text("Relatório comparativo (.md)")).to_be_visible(timeout=45_000)
            expect(page.get_by_text("Relatório para impressão (.html)")).to_be_visible(timeout=45_000)
            # Verify downloads actually contain report bytes, not just buttons.
            with page.expect_download(timeout=40_000) as markdown_event:
                page.get_by_role("button", name=re.compile("Relatório comparativo")).click()
            markdown = markdown_event.value
            markdown_path = Path("artifacts/bi_v14_smoke.md")
            markdown.save_as(markdown_path)
            markdown_text = markdown_path.read_text(encoding="utf-8")
            assert markdown.suggested_filename == "cx_bi_v14_sintetico.md"
            assert "Dados: 100% sintéticos" in markdown_text
            assert "Indicadores comparativos" in markdown_text
            with page.expect_download(timeout=40_000) as html_event:
                page.get_by_role("button", name=re.compile("Relatório para impressão")).click()
            html = html_event.value
            html_path = Path("artifacts/bi_v14_smoke.html")
            html.save_as(html_path)
            html_text = html_path.read_text(encoding="utf-8")
            assert html.suggested_filename == "cx_bi_v14_sintetico.html"
            assert "<!DOCTYPE html>" in html_text
            assert "Período atual" in html_text
            assert "Dados 100% sintéticos" in html_text
            assert page.locator('[data-testid="stException"]').count() == 0
            assert not js_errors, f"Erros de JavaScript: {js_errors}"
            modebars = page.locator('[data-testid="stPlotlyChart"] .modebar')
            if modebars.count():
                assert modebars.first.evaluate(
                    "node => getComputedStyle(node).display"
                ) == "none", "A barra Plotly cobre o gráfico no celular"
            print("PASS: v1.4 BI mobile 390x844; real Markdown+HTML downloads with verified content.")
        except Exception:
            page.screenshot(path="artifacts/cx_v14_mobile_failure.png", full_page=False)
            raise
        finally:
            browser.close()


if __name__ == "__main__":
    check_bi_mobile()
