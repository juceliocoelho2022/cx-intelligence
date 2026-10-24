"""v1.5 Streamlit mobile acceptance: targets, session actions, real exports."""
import json
import os
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

BASE_URL = os.getenv("CX_SMOKE_URL", "http://127.0.0.1:8501")


def check_v15_mobile():
    Path("artifacts").mkdir(exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="chrome", headless=True,
                                      args=["--no-sandbox"])
        page = browser.new_page(viewport={"width": 390, "height": 844},
                                device_scale_factor=2, is_mobile=True,
                                has_touch=True, accept_downloads=True)
        page.set_default_timeout(45000)
        errors = []
        page.on("pageerror", lambda err: errors.append(str(err)))
        try:
            page.goto(BASE_URL, wait_until="domcontentloaded", timeout=90000)
            expect(page.get_by_text("4.000", exact=True).first).to_be_visible(timeout=100000)
            tab = page.get_by_role("tab", name="🎯 Metas v1.5")
            tab.scroll_into_view_if_needed()
            tab.click()
            expect(page.get_by_text("Metas de CX e Plano de Ação — v1.5 (beta)")).to_be_visible()
            expect(page.get_by_text("Meta ilustrativa de CSAT (%)")).to_be_visible()
            expect(page.get_by_text("Plano de ação demonstrativo")).to_be_visible()
            expect(page.get_by_text("Nenhuma ação proposta ainda.")).to_be_visible()
            page.get_by_role("textbox", name="Ação proposta (até 120 caracteres)").fill(
                "Investigar fricção no atendimento Pix")
            page.get_by_role("textbox", name="Hipótese a investigar (até 400 caracteres)").fill(
                "Conferir jornadas e dúvidas recorrentes do processo ilustrativo.")
            page.get_by_role("button", name="Adicionar ação ilustrativa").click()
            expect(page.get_by_text("1 ação(ões) fictícia(s) registrada(s) apenas nesta sessão.")).to_be_visible(timeout=45000)
            expect(page.get_by_text("Investigar fricção no atendimento Pix").first).to_be_visible()
            with page.expect_download(timeout=45000) as json_event:
                page.get_by_role("button", name="Exportar plano (.json)").click()
            json_file = json_event.value
            json_path = Path("artifacts/v15_plan.json")
            json_file.save_as(json_path)
            content = json.loads(json_path.read_text(encoding="utf-8"))
            assert json_file.suggested_filename == "cx_metas_v15_sintetico.json"
            assert content["source"] == "synthetic_primary_only"
            assert content["persistence"] == "session_only"
            assert content["actions"][0]["id"] == "A0001"
            assert content["actions"][0]["status"] == "Planejada"
            assert len(content["goals"]) == 3
            with page.expect_download(timeout=45000) as md_event:
                page.get_by_role("button", name="Exportar plano (.md)").click()
            md_file = md_event.value
            md_path = Path("artifacts/v15_plan.md")
            md_file.save_as(md_path)
            md_text = md_path.read_text(encoding="utf-8")
            assert md_file.suggested_filename == "cx_metas_v15_sintetico.md"
            assert "Metas ilustrativas" in md_text
            assert "Investigar fricção no atendimento Pix" in md_text
            assert "apenas na sessão" in md_text
            assert page.locator('[data-testid="stException"]').count() == 0
            assert not errors, "JavaScript page errors: " + str(errors)
            print("PASS: v1.5 mobile 390x844; goal cards, action creation, and JSON+Markdown real downloads.")
        except Exception:
            page.screenshot(path="artifacts/cx_v15_mobile_failure.png",
                            full_page=False)
            raise
        finally:
            browser.close()


if __name__ == "__main__":
    check_v15_mobile()
