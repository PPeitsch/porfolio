import sys
from unittest.mock import patch

import pytest
from jinja2 import TemplateError


def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.data == b"OK"


def test_selector_route(client):
    """Test that the main selector page loads successfully."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"Select Your Experience" in response.data


@pytest.mark.parametrize(
    "view_name",
    ["cli", "recruiter", "visual"],
)
def test_get_view_partial_routes_success(client, view_name):
    """Test that valid view partials load successfully."""
    response = client.get(f"/view/{view_name}")
    assert response.status_code == 200
    if view_name == "cli":
        assert b'id="cli-window"' in response.data
    elif view_name == "recruiter":
        assert b'id="chat-window"' in response.data
    elif view_name == "visual":
        assert b'id="project-grid"' in response.data


def test_get_view_partial_route_not_found(client):
    """Test that an invalid view partial returns a 404."""
    response = client.get("/view/nonexistentview")
    assert response.status_code == 404
    assert b'Error: View "nonexistentview" not found.' in response.data


@patch("app.shell.routes.render_template")
def test_get_view_partial_template_error(mock_render_template, client):
    """Test the error handler for template rendering exceptions."""
    mock_render_template.side_effect = TemplateError("Jinja2 render failed")
    response = client.get("/view/cli")
    assert response.status_code == 500
    assert b"Error rendering view template" in response.data


def test_create_app_no_config_file(monkeypatch):
    """
    Test that the app factory handles a missing config.py by falling back
    to a default secret key.
    """
    # Temporarily remove the 'config' module from sys.modules to force ImportError
    monkeypatch.setitem(sys.modules, "config", None)

    # We need to reload the app factory module to trigger the import error
    from importlib import reload

    from app import shell

    reload(shell)
    from app.shell import create_app

    app = create_app()
    assert app.config["SECRET_KEY"] == "default-fallback-key-error"

    # Clean up by restoring the module if necessary for other tests,
    # though pytest usually isolates this.
    reload(shell)


@pytest.mark.parametrize(
    "configured, expected",
    [("catppuccin", "catppuccin"), ("gruvbox", "gruvbox"), ("neon", "catppuccin")],
)
def test_selector_default_theme(app, client, configured, expected):
    """The page starts in DEFAULT_THEME, or catppuccin if it is unknown."""
    saved = app.config.get("DEFAULT_THEME")
    app.config["DEFAULT_THEME"] = configured
    try:
        html = client.get("/").get_data(as_text=True)
    finally:
        app.config["DEFAULT_THEME"] = saved
    assert f'window.DEFAULT_THEME = "{expected}";' in html
