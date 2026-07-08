# Licensed under a 3-clause BSD style license - see LICENSE.rst
import asv_env_conda
from asv_env_conda import Conda, _conda_works, _find_conda


def test_tool_name():
    assert Conda.tool_name == "conda"
    assert asv_env_conda.Conda is Conda


def test_matches_does_not_crash_without_conda(monkeypatch):
    def _boom():
        raise OSError("no conda")

    monkeypatch.setattr(asv_env_conda, "_find_conda", _boom)
    Conda._matches_cache.clear()
    assert Conda.matches("3.12") is False


def test_conda_works_rejects_missing(tmp_path):
    assert _conda_works(str(tmp_path / "nope")) is False


def test_entry_point_metadata():
    from importlib.metadata import entry_points

    eps = entry_points()
    try:
        group = list(eps.select(group="asv.environment_backends"))
    except AttributeError:
        group = list(eps.get("asv.environment_backends", []))
    names = {ep.name: ep.value for ep in group if ep.name == "conda"}
    assert "conda" in names
    assert "asv_env_conda" in names["conda"]

