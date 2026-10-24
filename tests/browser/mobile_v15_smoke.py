"""v1.5 Streamlit mobile acceptance: targets, session actions, real exports."""
import json
import os
import re
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
            expect(page.get_by_text("Metas de CX e Plano de Ação — v1.5.0")).to_be_visible(timeout=110000)
            expect(page.get_by_text("Meta ilustrativa de CSAT (%)")).to_be_visible()
            expect(page.get_by_text("Plano de ação demonstrativo")).to_be_visible()
            expect(page.get_by_text("Nenhuma ação proposta ainda.")).to_be_visible()
            def full_script_runs():
                # CI-only diagnostic lives outside the goal fragment. Any
                # full-app rerun increments it; fragment-only actions do not.
                locator = page.get_by_text(re.compile(r"v1\\.6 full app runs: \\d+"))
                content = locator.text_content(timeout=30000)
                assert content is not None
                return int(re.search(r"\\d+", content.split(":")[-1]).group())
            script_runs_before_actions = full_script_runs()
            title_box = page.get_by_role(
                "textbox", name="Ação proposta (obrigatório; até 120 caracteres)")
            hypothesis_box = page.get_by_role(
                "textbox", name="Hipótese a investigar (obrigatório; até 400 caracteres)")
            title_box.fill("Investigar fricção no atendimento Pix")
            # Reproduce the reported mistake: empty hypothesis must show a useful
            # error without discarding the title the user already typed.
            page.get_by_role("button", name="Adicionar ação ilustrativa").click()
            expect(page.get_by_text(
                "Não foi possível adicionar: Hipótese de investigação: campo obrigatório.",
                exact=False)).to_be_visible(timeout=45000)
            expect(title_box).to_have_value("Investigar fricção no atendimento Pix")
            hypothesis_box.fill(
                "Conferir jornadas e dúvidas recorrentes do processo ilustrativo.")
            page.get_by_role("button", name="Adicionar ação ilustrativa").click()
            expect(page.get_by_text("1 ação(ões) fictícia(s) registrada(s) apenas nesta sessão.")).to_be_visible(timeout=45000)
            # Streamlit virtualizes dataframe cells on mobile; validate title via downloaded JSON.
            with page.expect_download(timeout=45000) as json_event:
                page.get_by_role("button", name="Exportar plano (.json)").click()
            json_file = json_event.value
            json_path = Path("artifacts/v15_plan.json")
            json_file.save_as(json_path)
            content = json.loads(json_path.read_text(encoding="utf-8"))
            assert json_file.suggested_filename == "cx_metas_v15_sintetico.json"
            assert content["source"] == "synthetic_primary_only"
            assert content["schema_version"] == "1.5.0"
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
            # Confirm that the action state survives rerender in this session
            # and that the audit events are exported, without external side effects.
            page.get_by_role("button", name="Atualizar estado fictício").click()
            expect(page.get_by_text(
                "Estados simulados: 0 planejada(s), 1 em andamento, 0 concluída(s)."
            )).to_be_visible(timeout=45000)
            # Only export after state has been observed on the rerendered page.
            with page.expect_download(timeout=45000) as updated_event:
                page.get_by_role("button", name="Exportar plano (.json)").click()
            updated_file = updated_event.value
            updated_path = Path("artifacts/v15_plan_in_progress.json")
            updated_file.save_as(updated_path)
            updated_payload = json.loads(updated_path.read_text(encoding="utf-8"))
            assert updated_payload["actions"][0]["status"] == "Em andamento"
            assert [event["status"] for event in updated_payload["actions"][0]["events"]] == [
                "Planejada", "Em andamento"
            ]
            # Edit the restored action's description without losing its identity
            # or its separate status event history.
            page.get_by_text("✏️ Corrigir título ou hipótese de uma ação", exact=True).click()
            page.get_by_role("textbox", name="Título corrigido (até 120 caracteres)").fill(
                "Investigar dificuldades na jornada Pix")
            page.get_by_role("button", name="Salvar correção da ação").click()
            expect(page.get_by_text(
                "Revisões de texto registradas: A0001: Investigar dificuldades na jornada Pix"
            )).to_be_visible(timeout=45000)
            with page.expect_download(timeout=45000) as edited_event:
                page.get_by_role("button", name="Exportar plano (.json)").click()
            edited_file = edited_event.value
            edited_path = Path("artifacts/v15_edited_plan.json")
            edited_file.save_as(edited_path)
            edited_plan = json.loads(edited_path.read_text(encoding="utf-8"))
            assert edited_plan["actions"][0]["id"] == "A0001"
            assert edited_plan["actions"][0]["title"] == "Investigar dificuldades na jornada Pix"
            assert edited_plan["actions"][0]["status"] == "Em andamento"
            assert [e["status"] for e in edited_plan["actions"][0]["events"]] == [
                "Planejada", "Em andamento"]
            assert edited_plan["actions"][0]["edits"][0]["old_title"] == (
                "Investigar fricção no atendimento Pix")
            # Import an earlier export to demonstrate session-only recovery.
            page.get_by_text("📥 Restaurar plano de ação exportado (.json)", exact=True).click()
            # Streamlit assigns the aria label to a dropzone section, not to
            # its actual HTML file input; Playwright needs input[type=file].
            page.locator('[data-testid="stFileUploader"] input[type="file"]').set_input_files(
                str(json_path))
            page.get_by_role("button", name="Restaurar ações nesta sessão").click()
            expect(page.get_by_text("1 ação(ões) restaurada(s) na sessão.", exact=False)).to_be_visible(timeout=45000)
            with page.expect_download(timeout=45000) as restored_event:
                page.get_by_role("button", name="Exportar plano (.json)").click()
            restored_path = Path("artifacts/v15_restored_plan.json")
            restored_event.value.save_as(restored_path)
            restored_plan = json.loads(restored_path.read_text(encoding="utf-8"))
            assert restored_plan["actions"][0]["id"] == "A0001"
            assert restored_plan["actions"][0]["status"] == "Planejada"
            assert restored_plan["actions"][0]["title"] == "Investigar fricção no atendimento Pix"
            assert full_script_runs() == script_runs_before_actions, (
                "Action creation, editing, status changes and restore must rerun "
                "only the v1.6 goals fragment, not the full analytics dashboard."
            )
            assert page.locator('[data-testid="stException"]').count() == 0
            assert not errors, "JavaScript page errors: " + str(errors)
            print("PASS: v1.5 mobile 390x844; action creation, state changes, edit revisions, import recovery and real JSON/Markdown downloads.")
        except Exception:
            page.screenshot(path="artifacts/cx_v15_mobile_failure.png",
                            full_page=False)
            raise
        finally:
            browser.close()


if __name__ == "__main__":
    check_v15_mobile()
