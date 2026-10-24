"""One-off LIVE Render export acceptance. Never part of the local Python CI suite.

Use a fresh browser profile on retry when a transient frontend chunk fetch
fails. Only report success once both downloaded files are saved and inspected.
"""
import os
import time
import traceback
from pathlib import Path

from playwright.sync_api import sync_playwright, expect

BASE = os.getenv("CX_SMOKE_URL", "https://cx-intelligence-demo.onrender.com/")
OUT = Path("artifacts")
OUT.mkdir(exist_ok=True)


def attempt(playwright, number):
    browser = playwright.chromium.launch(channel="chrome", headless=True,
                                         args=["--no-sandbox"])
    context = browser.new_context(viewport={"width": 390, "height": 844},
                                  device_scale_factor=2, is_mobile=True,
                                  has_touch=True, accept_downloads=True)
    page = context.new_page()
    page.set_default_timeout(45000)
    js_errors = []
    failed_requests = []
    page.on("pageerror", lambda err: js_errors.append(str(err)))
    page.on("requestfailed", lambda req: failed_requests.append(
        req.url + ": " + str(req.failure)))
    try:
        page.goto(BASE, wait_until="domcontentloaded", timeout=90000)
        expect(page.get_by_text("4.000", exact=True).first).to_be_visible(timeout=75000)
        tab = page.get_by_role("tab", name="📑 BI v1.4")
        tab.scroll_into_view_if_needed()
        tab.click()
        expect(page.get_by_text("Business Intelligence — Relatório Executivo Comparativo")).to_be_visible(timeout=45000)
        assert not page.get_by_text("Failed to fetch dynamically imported module").count(), "Streamlit frontend JS chunk failed"
        with page.expect_download(timeout=50000) as md_event:
            page.get_by_role("button", name="⬇ Relatório comparativo (.md)").click()
        md = md_event.value
        md_path = OUT / "public_bi_v14.md"
        md.save_as(md_path)
        assert md.suggested_filename == "cx_bi_v14_sintetico.md"
        md_body = md_path.read_text(encoding="utf-8")
        assert "Dados: 100% sintéticos" in md_body
        assert "Indicadores comparativos" in md_body
        with page.expect_download(timeout=50000) as html_event:
            page.get_by_role("button", name="⬇ Relatório para impressão (.html)").click()
        html = html_event.value
        html_path = OUT / "public_bi_v14.html"
        html.save_as(html_path)
        assert html.suggested_filename == "cx_bi_v14_sintetico.html"
        html_body = html_path.read_text(encoding="utf-8")
        assert html_body.lstrip().startswith("<!DOCTYPE html>")
        assert "Período atual" in html_body and "Dados 100% sintéticos" in html_body
        assert page.locator('[data-testid="stException"]').count() == 0
        assert not js_errors, "JS errors: " + str(js_errors[:4])
        print(f"PASS: Render PUBLIC URL downloaded and inspected Markdown ({len(md_body)} chars) and HTML ({len(html_body)} chars).")
        return True
    except Exception:
        print(f"ATTEMPT {number}: FAILED")
        print(traceback.format_exc(limit=3))
        print("Failed HTTP requests (sample):", failed_requests[:20])
        print("Browser JS errors (sample):", js_errors[:20])
        page.screenshot(path=str(OUT / f"public_bi_v14_failure_{number}.png"),
                        full_page=False)
        return False
    finally:
        context.close()
        browser.close()


if __name__ == "__main__":
    with sync_playwright() as engine:
        if not attempt(engine, 1):
            print("Retrying with new Chrome profile after brief cooldown.")
            time.sleep(12)
            if not attempt(engine, 2):
                raise SystemExit("FAIL: actual public Render downloads not verified after retries.")
