"""Versioned URLs for the static files.

Every url_for() of a static file (the app's or a blueprint's) gets ?v=<hash of
the file>, so a changed file has a new URL and browsers stop using the copy
they cached. Responses to a versioned URL can then be cached for a year.
"""

import hashlib
import os
from functools import lru_cache
from typing import Any, Dict, Optional

from flask import Flask, Response, request

VERSION_ARG = "v"
VERSIONED_MAX_AGE = 365 * 24 * 3600


@lru_cache(maxsize=256)
def _hash_file(path: str, mtime_ns: int, size: int) -> str:
    """Short hash of a file's contents; mtime and size make the cache key."""
    digest = hashlib.md5(usedforsecurity=False)
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()[:10]


def file_version(path: str) -> Optional[str]:
    """The version of a file for its URL, or None if it does not exist."""
    try:
        stat = os.stat(path)
    except OSError:
        return None
    return _hash_file(path, stat.st_mtime_ns, stat.st_size)


def _static_folder(app: Flask, endpoint: str) -> Optional[str]:
    if endpoint == "static":
        return app.static_folder
    if not endpoint.endswith(".static"):
        return None
    blueprint = app.blueprints.get(endpoint.rsplit(".", 1)[0])
    return blueprint.static_folder if blueprint else None


def init_asset_versioning(app: Flask) -> None:
    """Adds ?v= to static URLs and caches the versioned responses."""

    @app.url_defaults
    def add_version(endpoint: str, values: Dict[str, Any]) -> None:
        filename = values.get("filename")
        if not filename or VERSION_ARG in values:
            return
        folder = _static_folder(app, endpoint)
        if not folder:
            return
        version = file_version(os.path.join(folder, filename))
        if version:
            values[VERSION_ARG] = version

    @app.after_request
    def cache_versioned(response: Response) -> Response:
        endpoint = request.endpoint or ""
        if (
            VERSION_ARG in request.args
            and response.status_code == 200
            and _static_folder(app, endpoint)
        ):
            response.cache_control.public = True
            response.cache_control.max_age = VERSIONED_MAX_AGE
            response.cache_control.immutable = True
        return response
