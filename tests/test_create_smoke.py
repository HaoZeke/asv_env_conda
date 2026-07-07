# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os
import tempfile
from pathlib import Path

import pytest

from asv.config import Config
from asv import environment as envmod
from asv_env_conda import Conda, _find_conda


@pytest.fixture
def conf(tmp_path):
    c = Config()
    c.env_dir = str(tmp_path / "env")
    c.project = "smoke"
    c.repo = str(tmp_path / "repo")
    c.repo_subdir = ""
    c.install_timeout = 900.0
    c.default_benchmark_timeout = 60.0
    c.conda_channels = ["conda-forge"]
    c.conda_environment_file = "IGNORE"
    c.matrix = {}
    return c


def test_create_conda_has_python(conf):
    try:
        _find_conda()
    except OSError:
        pytest.skip("no working conda CLI")
    os.chdir(tempfile.mkdtemp())
    # Prefer 3.12 for wider channel support
    try:
        env = Conda(conf, "3.12", {}, {})
    except envmod.EnvironmentUnavailable as e:
        pytest.skip(str(e))
    Path(env._path).mkdir(parents=True, exist_ok=True)
    env._setup()
    py_path = Path(env.find_executable("python"))
    assert py_path.exists()
    out = env.run_executable("python", ["-c", "print(5+5)"])
    assert "10" in out
