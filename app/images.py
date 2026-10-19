"""Images for node definitions.

Pictures are stored as files in data/images/, named after a hash of their content (so
adding the same picture twice stores it once), and referenced from a definition with
ordinary Markdown: `![caption](/images/<name>)`. Flask routes serve them back and accept
uploads (from the file picker and from pasting a screenshot).
"""

from __future__ import annotations

import base64
import hashlib
import re
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

from .storage import DATA_DIR

IMAGES_DIR = DATA_DIR / "images"
MAX_BYTES = 10 * 1024 * 1024  # 10 MB per picture

# Only formats recognised by their first bytes are accepted. SVG is left out on purpose:
# it can contain scripts.
_SIGNATURES = [
    (b"\x89PNG\r\n\x1a\n", ".png"),
    (b"\xff\xd8\xff", ".jpg"),
    (b"GIF87a", ".gif"),
    (b"GIF89a", ".gif"),
]


def detect_extension(data: bytes) -> str | None:
    for signature, ext in _SIGNATURES:
        if data.startswith(signature):
            return ext
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    return None


def save_image(data: bytes, images_dir: Path | None = None) -> str:
    """Store a picture and return its file name. Raises ValueError if it is not acceptable."""
    if not data:
        raise ValueError("The file is empty.")
    if len(data) > MAX_BYTES:
        raise ValueError(f"The image is larger than {MAX_BYTES // (1024 * 1024)} MB.")
    ext = detect_extension(data)
    if ext is None:
        raise ValueError("Only PNG, JPEG, GIF and WebP images are supported.")
    images_dir = images_dir or IMAGES_DIR
    images_dir.mkdir(parents=True, exist_ok=True)
    name = hashlib.sha256(data).hexdigest()[:16] + ext
    path = images_dir / name
    if not path.exists():
        path.write_bytes(data)
    return name


def decode_data_url(contents: str) -> bytes:
    """Bytes from a `data:<type>;base64,<payload>` string, as produced by dcc.Upload."""
    try:
        return base64.b64decode(contents.split(",", 1)[1], validate=True)
    except (IndexError, ValueError) as err:
        raise ValueError("Could not read the uploaded file.") from err


def markdown_for(name: str, caption: str = "") -> str:
    caption = re.sub(r"[\[\]\r\n]", " ", caption).strip()
    return f"![{caption}](/images/{name})"


def append_markdown(text: str, addition: str) -> str:
    """Add a block at the end of `text`, separated by one blank line, ending with a newline."""
    if not text:
        return addition + "\n"
    blank_lines_needed = max(0, 2 - (len(text) - len(text.rstrip("\n"))))
    return text + "\n" * blank_lines_needed + addition + "\n"


def register_routes(server: Flask, images_dir: Path | None = None) -> None:
    """Add `GET /images/<name>` and `POST /upload-image` to the Dash app's Flask server."""

    def directory() -> Path:
        return images_dir or IMAGES_DIR

    @server.get("/images/<path:name>")
    def serve_image(name: str):
        return send_from_directory(directory(), name)

    @server.post("/upload-image")
    def upload_image():
        data = request.get_data(cache=False)
        try:
            name = save_image(data, directory())
        except ValueError as err:
            return jsonify(error=str(err)), 400
        return jsonify(name=name, url=f"/images/{name}")
