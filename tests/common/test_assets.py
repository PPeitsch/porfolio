import os
import re

from app.common.assets import file_version


def test_static_urls_carry_the_file_version(client):
    """The selector's CSS and JS links, and the views' ones, are versioned."""
    html = client.get("/").get_data(as_text=True)
    for path in (
        "/shell-static/css/style.css",
        "/shell-static/js/selector.js",
        "/visual/static/css/visual.css",
        "/cli/static/js/terminal.js",
    ):
        assert re.search(re.escape(path) + r"\?v=[0-9a-f]{10}", html), path


def test_version_changes_with_the_file(tmp_path):
    asset = tmp_path / "app.css"
    asset.write_text("body { color: red; }")
    first = file_version(str(asset))
    asset.write_text("body { color: blue; }")
    os.utime(asset, ns=(1, 1))  # A new mtime, as an edit or a deploy gives
    assert first and file_version(str(asset)) not in (None, first)
    assert file_version(str(tmp_path / "missing.css")) is None


def test_versioned_responses_are_cached_for_long(client):
    html = client.get("/").get_data(as_text=True)
    url = re.search(r"/shell-static/css/style\.css\?v=[0-9a-f]{10}", html).group(0)
    cache = client.get(url).headers["Cache-Control"]
    assert "max-age=31536000" in cache and "immutable" in cache
    # Without the version, browsers keep revalidating as before.
    plain = client.get("/shell-static/css/style.css").headers.get("Cache-Control", "")
    assert "immutable" not in plain


def test_only_static_endpoints_are_versioned(app):
    """Other endpoints, an explicit version and unknown files are left alone."""
    with app.test_request_context():
        from flask import url_for

        assert "v=" not in url_for("shell.selector")
        assert "v=" not in url_for("shell.static", filename="css/missing.css")
        assert url_for("shell.static", filename="css/style.css", v="x").endswith("?v=x")
        assert "v=" not in url_for("health_check")
        # Has a filename but is not a static folder
        assert "v=" not in url_for("shell.content_image", filename="a.png")


def test_unknown_blueprint_has_no_static_folder(app):
    from app.common.assets import _static_folder

    assert _static_folder(app, "nope.static") is None
    assert _static_folder(app, "shell.selector") is None
    assert _static_folder(app, "static") == app.static_folder
