"""Tests para utilidades puras del launcher."""
import gtk_launcher as gl


def test_safe_cover_name():
    assert gl._safe_cover_name("Red Dead Redemption 2") == "Red_Dead_Redemption_2"
    assert "/" not in gl._safe_cover_name("a/b")
    assert " " not in gl._safe_cover_name("con espacio")


def test_version_tuple():
    assert gl._version_tuple("8.1") == (8, 1)
    assert gl._version_tuple("8.1") < gl._version_tuple("8.2")
    assert gl._version_tuple("8.0") < gl._version_tuple("8.1")
    assert gl._version_tuple("8.1") == gl._version_tuple("8.1")
    assert gl._version_tuple("8.10") > gl._version_tuple("8.9")
