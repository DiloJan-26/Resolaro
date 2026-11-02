from pathlib import Path

from resolaro.main import app


def test_declared_browser_paths_exist_in_openapi():
    paths = app.openapi()["paths"]
    assert set(paths) == {
        "/healthz", "/api/v1/me", "/api/v1/organizations/{organization_id}/context", "/api/v1/cases"
    }
    browser = (Path(__file__).resolve().parents[3] / "web" / "src" / "api.ts").read_text(encoding="utf-8")
    assert "get<Me>('/me'" in browser
    assert "`/organizations/${encodeURIComponent(id)}/context`" in browser
    assert "`/cases?organization_id=${encodeURIComponent(id)}`" in browser
    assert "get<Cases>" in browser
