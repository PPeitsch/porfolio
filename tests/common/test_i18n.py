import json
from unittest.mock import MagicMock, patch

import pytest

from app.common.i18n import (
    LANG_COOKIE,
    UI_DEFAULTS,
    _ui_overrides,
    fill,
    get_locale,
    is_localized,
    localize,
    t,
)
from app.common.llm_services import ChatResponse
from tests.helpers import generate_test_token


@pytest.fixture()
def languages(app):
    """Sets LANGUAGES / DEFAULT_LANGUAGE for one test and restores them."""
    saved = (app.config.get("LANGUAGES"), app.config.get("DEFAULT_LANGUAGE"))

    def configure(langs, default=None):
        app.config["LANGUAGES"] = langs
        app.config["DEFAULT_LANGUAGE"] = default or langs[0]

    configure(["en", "es"])
    yield configure
    app.config["LANGUAGES"], app.config["DEFAULT_LANGUAGE"] = saved


# --- localize / is_localized ---


def test_localize_picks_the_requested_language(app, languages):
    with app.app_context():
        assert localize({"en": "Hello", "es": "Hola"}, "es") == "Hola"
        assert localize({"en": "Hello", "es": "Hola"}, "en") == "Hello"


def test_localize_falls_back_to_default_then_first(app, languages):
    languages(["en", "es", "pt"], default="es")
    with app.app_context():
        assert localize({"en": "Hello", "es": "Hola"}, "pt") == "Hola"
        assert localize({"en": "Hello"}, "es") == "Hello"


def test_localize_walks_nested_data(app, languages):
    data = {
        "name": "Alex",
        "title": {"en": "Developer", "es": "Desarrollador"},
        "manual": {"en": ["NAME"], "es": ["NOMBRE"]},
        "items": [{"description": {"en": "One", "es": "Uno"}}],
        "social_links": {"github": "https://github.com/x"},
    }
    with app.app_context():
        result = localize(data, "es")
    assert result == {
        "name": "Alex",
        "title": "Desarrollador",
        "manual": ["NOMBRE"],
        "items": [{"description": "Uno"}],
        "social_links": {"github": "https://github.com/x"},
    }


@pytest.mark.parametrize(
    "value, expected",
    [
        ({"en": "a", "es": "b"}, True),
        ({"pt": "a"}, True),  # a language the app knows by name
        ({"id": "p1", "title": "x"}, False),
        ({"gh": "https://github.com/x"}, False),  # two letters, not a language
        ({}, False),
        ("text", False),
    ],
)
def test_is_localized(app, languages, value, expected):
    with app.app_context():
        assert is_localized(value) is expected


def test_fill_leaves_other_braces_alone():
    assert fill("{a} and {b}", a=1) == "1 and {b}"


def test_ui_overrides_skip_missing_languages(app, languages):
    ui = {"chat": {"thinking": {"es": "Pensando..."}, "brand": "Plain"}}
    with app.app_context():
        assert _ui_overrides(ui, "en") == {"chat.brand": "Plain"}
        assert _ui_overrides(ui, "es") == {
            "chat.thinking": "Pensando...",
            "chat.brand": "Plain",
        }


def test_t_outside_app_context_uses_defaults():
    assert t("visual.heading") == UI_DEFAULTS["visual.heading"]


# --- Language of a request ---


@pytest.mark.parametrize(
    "headers, cookie, expected",
    [
        ({}, None, "en"),
        ({"Accept-Language": "es-AR,es;q=0.9,en;q=0.5"}, None, "es"),
        ({"Accept-Language": "fr-FR"}, None, "en"),
        ({"Accept-Language": "es"}, "en", "en"),  # the switcher wins
        ({}, "xx", "en"),  # unknown cookie value is ignored
    ],
)
def test_get_locale(app, languages, headers, cookie, expected):
    if cookie:
        headers = {**headers, "Cookie": f"{LANG_COOKIE}={cookie}"}
    with app.test_request_context("/", headers=headers):
        assert get_locale() == expected


def test_set_language_route(client, languages):
    response = client.get("/lang/es")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")
    assert f"{LANG_COOKIE}=es" in response.headers["Set-Cookie"]
    assert client.get("/lang/xx").status_code == 404


# --- Views ---


def test_selector_in_spanish(client, languages):
    response = client.get("/", headers={"Accept-Language": "es"})
    html = response.get_data(as_text=True)

    assert '<html lang="es">' in html
    assert "¿Cómo te gustaría recorrer mi portfolio?" in html
    # The switcher offers the next language, and the scripts get the texts.
    assert 'href="/lang/en"' in html
    assert '"visual.heading": "Proyectos"' in html


def test_selector_in_english_by_default(client, languages):
    html = client.get("/").get_data(as_text=True)

    assert '<html lang="en">' in html
    assert UI_DEFAULTS["selector.subtitle"] in html
    assert 'href="/lang/es"' in html


def test_no_switcher_with_one_language(client, languages):
    languages(["en"])
    html = client.get("/").get_data(as_text=True)

    assert "dock-language" not in html


def test_view_partial_in_spanish(client, languages):
    client.set_cookie(LANG_COOKIE, "es")
    html = client.get("/view/visual").get_data(as_text=True)

    assert ">Proyectos</h2>" in html


def test_example_data_in_spanish(client, languages):
    client.set_cookie(LANG_COOKIE, "es")
    projects = client.get("/visual/api/projects").get_json()

    assert projects[0]["title"] == "Portfolio en terminal"


def test_cli_output_in_spanish(client, app, languages):
    client.set_cookie(LANG_COOKIE, "es")
    headers = {"Authorization": f"Bearer {generate_test_token(app)}"}

    skills = client.get("/cli/api/command/skills", headers=headers).get_json()
    help_ = client.get("/cli/api/command/help", headers=headers).get_json()
    whoami = client.get("/cli/api/command/whoami", headers=headers).get_json()

    assert skills["output"][0] == "[INFO] Habilidades técnicas:"
    assert help_["output"][0] == "[INFO] Comandos del portfolio:"
    assert "Desarrollador Python" in "\n".join(whoami["output"])


def test_chat_tells_the_model_the_visitor_language(client, app, languages):
    service = MagicMock()
    service.get_chat_response.return_value = ChatResponse(content="Hola")
    client.set_cookie(LANG_COOKIE, "es")
    headers = {
        "Authorization": f"Bearer {generate_test_token(app)}",
        "Content-Type": "application/json",
    }

    with patch("app.view_recruiter.routes.get_llm_service", return_value=service):
        client.post(
            "/recruiter/api/chat",
            headers=headers,
            data=json.dumps({"message": "Hola"}),
        )

    system_prompt = service.get_chat_response.call_args.kwargs["system_prompt"]
    assert "browsing the site in Español" in system_prompt
