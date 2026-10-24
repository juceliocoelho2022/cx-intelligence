"""Static safeguards for public synthetic-only deployment configuration."""
from pathlib import Path


def test_public_demo_declares_safe_source_and_no_remote_database():
    source = Path(__file__).resolve().parents[1] / "app.py"
    code = source.read_text(encoding="utf-8")
    assert 'PUBLIC_DEMO = os.getenv("CX_PUBLIC_DEMO"' in code
    assert "Esta instância pública não recebe eventos" in code
    assert "a fonte Kaggle não está hospedada aqui" in code


def test_deploy_guide_has_no_database_secret_configuration():
    guide = (Path(__file__).resolve().parents[1] / "docs" / "PUBLIC_DEMO.md").read_text(encoding="utf-8")
    assert "CX_DATA_SOURCE=csv" in guide
    assert "CX_PUBLIC_DEMO=true" in guide
    assert "0.0.0.0" in guide
    assert "DATABASE_URL=" not in guide
