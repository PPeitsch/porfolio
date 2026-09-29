import pytest

from app.common.utils import _get_data_filepath, get_welcome_message
from app.shell import create_app


@pytest.fixture()
def content_dir(tmp_path):
    """A content directory with its own CV, texts, projects and one image."""
    (tmp_path / "cv.yaml").write_text("name: Test Owner\n", encoding="utf-8")
    (tmp_path / "text_config.yaml").write_text(
        'recruiter:\n  welcome: "Hi, I am the assistant of {name}."\n'
        'cli:\n  welcome: "Welcome to the shell of {name}."\n',
        encoding="utf-8",
    )
    (tmp_path / "projects.yaml").write_text(
        "- id: one\n  title: One\n  image: one.png\n"
        "- id: two\n  title: Two\n  image: legacy.png\n",
        encoding="utf-8",
    )
    (tmp_path / "images").mkdir()
    (tmp_path / "images" / "one.png").write_bytes(b"\x89PNG fake")
    return tmp_path


@pytest.fixture()
def content_app(content_dir):
    app = create_app("testing")
    app.config.update(TESTING=True, DATA_DIR=str(content_dir))
    return app


def test_data_filepath_uses_configured_dir(content_app, content_dir):
    with content_app.app_context():
        assert _get_data_filepath("cv.yaml") == str(content_dir / "cv.yaml")


def test_welcome_message_fills_in_the_name(content_app):
    with content_app.test_request_context():
        assert get_welcome_message("recruiter") == (
            "Hi, I am the assistant of Test Owner."
        )
        assert get_welcome_message("unknown") == ""


@pytest.mark.parametrize(
    "view, text",
    [
        ("recruiter", "Hi, I am the assistant of Test Owner."),
        ("cli", "Welcome to the shell of Test Owner."),
    ],
)
def test_view_partial_carries_the_welcome(content_app, view, text):
    response = content_app.test_client().get(f"/view/{view}")
    assert f'data-welcome="{text}"' in response.get_data(as_text=True)


def test_content_image_is_served(content_app):
    response = content_app.test_client().get("/content/images/one.png")
    assert response.status_code == 200
    assert response.data == b"\x89PNG fake"


@pytest.mark.parametrize("path", ["missing.png", "../cv.yaml"])
def test_content_image_rejects_missing_or_outside_files(content_app, path):
    response = content_app.test_client().get(f"/content/images/{path}")
    assert response.status_code == 404


def test_visual_prefers_content_images_and_falls_back(content_app):
    projects = content_app.test_client().get("/visual/api/projects").get_json()
    urls = {p["id"]: p["image_url"] for p in projects}
    assert urls["one"] == "/content/images/one.png"
    assert urls["two"] == "/shell-static/images/projects/legacy.png"
