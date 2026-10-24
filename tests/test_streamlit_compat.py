"""Guard against deprecated Streamlit UI arguments without importing the app."""
import ast
from pathlib import Path


def test_streamlit_renderers_do_not_use_deprecated_width_argument():
    script = Path(__file__).resolve().parents[1] / "app.py"
    tree = ast.parse(script.read_text(encoding="utf-8"))
    checked = 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        if not isinstance(fn, ast.Attribute) or not isinstance(fn.value, ast.Name):
            continue
        if fn.value.id != "st" or fn.attr not in {"plotly_chart", "dataframe"}:
            continue
        names = {keyword.arg for keyword in node.keywords}
        assert "use_container_width" not in names
        assert "width" in names
        checked += 1
    assert checked >= 2
