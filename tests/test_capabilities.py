# Licensed under a 3-clause BSD style license - see LICENSE.rst
from asv_env_conda import Conda


def test_capability_attrs():
    assert Conda.matrix_install_mode == 'post'
    assert Conda.requires_host_tool == 'conda'

