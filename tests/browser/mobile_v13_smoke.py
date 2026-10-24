"""Headless Chrome mobile viewport smoke test for the v1.3 Streamlit app.

Run against a local Streamlit server started by CI. Unlike static CSS checks,
this exercises rendered UI at smartphone width (390 x 844 CSS pixels).
"""
import os
import re
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

BASE_URL = os.environ.get("CX_SMOKE_URL", "http://127.0.0.1:8501")


def check_mobile_dashboard():
    Path("artifacts").mkdir(exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            channel="chrome", headless=True, args=["--no-sandbox"]
        )
        context = browser.new_context(
            viewport={"width": 390, "height": 844},
            device_scale_factor=2,
            is_mobile=True,
            has_touch=True,
        )
        page = context.new_page()
        page.set_default_timeout(50_000)
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        try:
            page.goto(BASE_URL, wait_until="domcontentloaded", timeout=90_000)
            expect(page.get_by_text("CX Intelligence", exact=True)).to_be_visible()
            expect(page.get_by_text("4.000", exact=True).first).to_be_visible()
            assert page.evaluate("window.innerWidth") == 390, "Viewport not 390 px"
            sidebar = page.get_by_test_id("stSidebar")
            # Streamlit 1.65 exposes aria-expanded; later versions may expose
            # data-collapsed instead. Both mean the narrow viewport starts closed.
            assert (sidebar.get_attribute("aria-expanded") == "false"
                    or sidebar.get_attribute("data-collapsed") == "true"), (
                "Mobile sidebar should start collapsed"
            )
            tab = page.get_by_role("tab", name=re.compile(r"Analytics v1\.3"))
            tab.scroll_into_view_if_needed()
            tab.click()
            expect(page.get_by_text(
                "Analytics avançado — comparação, incerteza e recontato"
            )).to_be_visible()
            for heading in (
                "1. Evolução semanal de CX",
                "2. Benchmark descritivo entre segmentos",
                "3. Recontato encontrado no histórico sintético — janela de 30 dias",
            ):
                expect(page.get_by_text(heading, exact=True)).to_be_visible()
            expect(page.get_by_text("Elegíveis (30 dias completos)")).to_be_visible()

            # Confirm the responsive style is applied to real rendered Plotly charts.
            modebars = page.locator('[data-testid="stPlotlyChart"] .modebar')
            expect(modebars.first).to_be_attached()
            for i in range(min(modebars.count(), 5)):
                displayed = modebars.nth(i).evaluate(
                    "(element) => getComputedStyle(element).display"
                )
                assert displayed == "none", f"Plotly toolbar visible on mobile: {displayed}"

            # Interactive switch: Segment benchmark by topic, then channel.
            group = page.get_by_test_id("stRadioGroup")
            assunto = page.get_by_role("radio", name="Assunto")
            group.get_by_text("Assunto", exact=True).click()
            expect(assunto).to_be_checked()
            canal = page.get_by_role("radio", name="Canal")
            group.get_by_text("Canal", exact=True).click()
            expect(canal).to_be_checked()
            assert page.locator('[data-testid="stException"]').count() == 0
            assert not errors, f"Browser JS errors: {errors}"
            print("PASS: v1.3 Analytics mobile viewport 390x844; 3 sections, real Plotly toolbar hidden, dimension switch.")
        except Exception:
            page.screenshot(path="artifacts/cx_v13_mobile_failure.png", full_page=False)
            raise
        finally:
            browser.close()


if __name__ == "__main__":
    check_mobile_dashboard()
