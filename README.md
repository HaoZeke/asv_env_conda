# asv_env_conda

Drop-in ASV backend for `environment_type = "conda"` (host **conda CLI**).

Core ASV ships only `virtualenv` and `existing`. This package is the
provider for `conda` — there is no in-tree `asv.plugins.conda`.

> Not a Rust/maturin backend. For crate-backed conda-ecosystem creates use
> `asv_env_rattler`. For joint conda+PyPI prefer `asv_env_pixi`.

## Drop-in setup

```bash
# conda on PATH, or set CONDA_EXE / ASV_CONDA_EXE to a real binary
pip install asv
pip install "git+https://github.com/HaoZeke/asv_env_conda.git"
```

```json
{
  "environment_type": "conda",
  "conda_channels": ["conda-forge"],
  "pythons": ["3.12"]
}
```

No conf `plugins` list required when the entry point is installed.

## Capabilities / matrix meaning

| Flag | Value |
|------|-------|
| `matrix_install_mode` | `post` (env create, often followed by env update) |
| `supports_joint_pypi_conda_solve` | `False` |
| `project_install_prefers_no_deps` | `False` |

Classic conda installs conda packages first and pip packages second; the
second call can ignore first-call pins (ASV #1542 / #1543). Prefer
rattler/pixi when matrix constraints must hold across ecosystems.

## Discovery

```toml
[project.entry-points."asv.environment_backends"]
conda = "asv_env_conda:Conda"
```

## Tests

```bash
pip install -e ".[test]"
pytest -q
```
