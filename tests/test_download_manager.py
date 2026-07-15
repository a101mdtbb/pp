"""Tests para download_manager: validación de descargas y utilidades."""
import os
import tempfile

import download_manager as dm


def _write(path, data):
    with open(path, "wb") as f:
        f.write(data)


def test_is_valid_download_rejects_html_error_page():
    d = tempfile.mkdtemp()
    p = os.path.join(d, "game.bin")
    _write(p, b"<!DOCTYPE html><html><body>404 Not Found</body></html>")
    assert dm._is_valid_download(p) is False


def test_is_valid_download_rejects_small_file():
    d = tempfile.mkdtemp()
    p = os.path.join(d, "tiny.bin")
    _write(p, b"MZ" + b"\x00" * 10)  # firma de exe pero < 1 KB
    assert dm._is_valid_download(p) is False


def test_is_valid_download_accepts_zip():
    d = tempfile.mkdtemp()
    p = os.path.join(d, "game.zip")
    _write(p, b"PK\x03\x04" + b"\x00" * 5000)
    assert dm._is_valid_download(p) is True


def test_is_valid_download_accepts_exe():
    d = tempfile.mkdtemp()
    p = os.path.join(d, "game.exe")
    _write(p, b"MZ" + b"\x00" * 5000)
    assert dm._is_valid_download(p) is True


def test_is_valid_download_rejects_missing():
    assert dm._is_valid_download("/ruta/inexistente.bin") is False


def test_sanitize_filename_removes_illegal_chars():
    assert dm._sanitize_filename('a/b:c*?') == "a_b_c__"
    assert " " not in dm._sanitize_filename("con espacios")
    assert dm._sanitize_filename("") == "download"


def test_extract_direct_link_unknown_host_is_browser():
    res = dm.extract_direct_link("https://example.com/game")
    assert res.get("needs_browser") is True
    assert res.get("url") == "https://example.com/game"
