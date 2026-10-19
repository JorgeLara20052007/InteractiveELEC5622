import base64

import pytest
from flask import Flask

from app import images

PNG = b"\x89PNG\r\n\x1a\n" + b"fake-png-body"
JPG = b"\xff\xd8\xff\xe0" + b"fake-jpg-body"
GIF = b"GIF89a" + b"fake-gif-body"
WEBP = b"RIFF\x00\x00\x00\x00WEBP" + b"fake-webp-body"


@pytest.mark.parametrize(
    "data, ext", [(PNG, ".png"), (JPG, ".jpg"), (GIF, ".gif"), (WEBP, ".webp"), (b"hello", None), (b"<svg/>", None)]
)
def test_detect_extension(data, ext):
    assert images.detect_extension(data) == ext


def test_save_image_names_the_file_after_its_content(tmp_path):
    name = images.save_image(PNG, tmp_path)
    assert name.endswith(".png")
    assert (tmp_path / name).read_bytes() == PNG
    assert images.save_image(PNG, tmp_path) == name  # same picture -> same file
    assert len(list(tmp_path.iterdir())) == 1


def test_save_image_rejects_bad_input(tmp_path, monkeypatch):
    with pytest.raises(ValueError, match="empty"):
        images.save_image(b"", tmp_path)
    with pytest.raises(ValueError, match="Only PNG"):
        images.save_image(b"<svg onload=alert(1)/>", tmp_path)
    monkeypatch.setattr(images, "MAX_BYTES", 10)
    with pytest.raises(ValueError, match="larger"):
        images.save_image(PNG, tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_decode_data_url():
    url = "data:image/png;base64," + base64.b64encode(PNG).decode()
    assert images.decode_data_url(url) == PNG
    with pytest.raises(ValueError):
        images.decode_data_url("not a data url")


def test_markdown_for_strips_brackets_from_the_caption():
    assert images.markdown_for("a.png", "Body [planes]\n") == "![Body  planes](/images/a.png)"


@pytest.fixture
def client(tmp_path):
    server = Flask(__name__)
    images.register_routes(server, tmp_path)
    return server.test_client(), tmp_path


def test_upload_then_fetch(client):
    http, _ = client
    reply = http.post("/upload-image", data=PNG, content_type="image/png")
    assert reply.status_code == 200
    url = reply.get_json()["url"]
    assert url.startswith("/images/") and url.endswith(".png")
    assert http.get(url).data == PNG


def test_upload_rejects_non_images(client):
    http, tmp_path = client
    reply = http.post("/upload-image", data=b"not an image", content_type="text/plain")
    assert reply.status_code == 400
    assert "error" in reply.get_json()
    assert list(tmp_path.iterdir()) == []


def test_serving_cannot_escape_the_images_folder(client):
    http, tmp_path = client
    (tmp_path.parent / "secret.txt").write_text("secret")
    assert http.get("/images/../secret.txt").status_code == 404
    assert http.get("/images/..%2Fsecret.txt").status_code == 404


@pytest.mark.parametrize(
    "text, expected",
    [
        ("", "![a](/images/x.png)\n"),
        ("hello", "hello\n\n![a](/images/x.png)\n"),
        ("hello\n", "hello\n\n![a](/images/x.png)\n"),
        ("hello\n\n", "hello\n\n![a](/images/x.png)\n"),
    ],
)
def test_append_markdown_leaves_exactly_one_blank_line(text, expected):
    assert images.append_markdown(text, "![a](/images/x.png)") == expected
