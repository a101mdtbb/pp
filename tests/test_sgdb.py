"""Tests para la lógica de búsqueda de carátulas en SteamGridDB."""
import json
from unittest.mock import patch

import gtk_launcher as gl


class _FakeResp:
    def __init__(self, payload):
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def read(self):
        return self._payload


def _autocomplete(results):
    data = {"success": True, "data": results}
    return _FakeResp(json.dumps(data).encode())


def test_search_sgdb_exact_match_redead2():
    # "Red Dead Redemption 2" debe mapear a "Red Dead Redemption II"
    results = [
        {"id": 111, "name": "Red Dead Redemption II", "types": ["steam"]},
        {"id": 222, "name": "Red Dead Redemption", "types": ["steam"]},
    ]
    with patch("urllib.request.urlopen", return_value=_autocomplete(results)):
        gid = gl.search_sgdb("Red Dead Redemption 2", "fakekey")
    assert gid == 111


def test_search_sgdb_number_consistency():
    # "Far Cry 5" no debe confundirse con "Far Cry"
    results = [
        {"id": 1, "name": "Far Cry", "types": ["steam"]},
        {"id": 5, "name": "Far Cry 5", "types": ["steam"]},
    ]
    with patch("urllib.request.urlopen", return_value=_autocomplete(results)):
        gid = gl.search_sgdb("Far Cry 5", "fakekey")
    assert gid == 5


def test_search_sgdb_single_result():
    results = [{"id": 9, "name": "Juego Raro", "types": ["steam"]}]
    with patch("urllib.request.urlopen", return_value=_autocomplete(results)):
        gid = gl.search_sgdb("Cualquiera", "fakekey")
    assert gid == 9


def test_search_sgdb_no_reliable_match():
    # Sin coincidencia fiable -> None (mejor que una equivocada)
    results = [
        {"id": 2, "name": "Resident Evil 2", "types": ["steam"]},
        {"id": 3, "name": "Resident Evil 3", "types": ["steam"]},
    ]
    with patch("urllib.request.urlopen", return_value=_autocomplete(results)):
        gid = gl.search_sgdb("Resident Evil 4", "fakekey")
    assert gid is None


def test_search_sgdb_no_key():
    assert gl.search_sgdb("Cualquiera", "") is None
