"""Tests para la caché de carátulas (descarta covers rotos y usa etag)."""
import os
import tempfile

import gtk_launcher as gl


def test_get_cached_cover_ignores_tiny_files(monkeypatch):
    d = tempfile.mkdtemp()
    monkeypatch.setattr(gl, "COVERS_DIR", d)
    # archivo < 1 KB -> no se considera carátula válida
    with open(os.path.join(d, "Game.jpg"), "wb") as f:
        f.write(b"\xff\xd8\xff" + b"\x00" * 100)
    assert gl.get_cached_cover("Game") is None
    # archivo >= 1 KB -> válido
    with open(os.path.join(d, "Game.jpg"), "wb") as f:
        f.write(b"\xff\xd8\xff" + b"\x00" * 5000)
    assert gl.get_cached_cover("Game") is not None


def test_cover_etag_is_deterministic():
    a = gl._cover_etag("https://x/y.jpg")
    b = gl._cover_etag("https://x/y.jpg")
    c = gl._cover_etag("https://x/z.jpg")
    assert a == b
    assert a != c
