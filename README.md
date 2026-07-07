# asv_env_conda

ASV environment backend for `environment_type = "conda"` (conda **CLI** / shell).

## Stage-1 discovery

Preferred entry point group:

```toml
[project.entry-points."asv.environment_backends"]
conda = "asv_env_conda:Conda"
```

Install this package into the **host** environment that runs ASV (Python ≥ 3.10).

```bash
pip install "git+https://github.com/HaoZeke/asv_env_conda.git"
# or: pip install -e .
```

```json
{
  "environment_type": "conda"
}
```

Conf `plugins` is optional when entry points are registered:

```json
{
  "environment_type": "conda",
  "plugins": ["asv_env_conda"]
}
```

## Conflict with in-tree ASV

Current ASV (and the Stage-1 design branch) may **also** ship `asv.plugins.conda`
with `tool_name = "conda"`. Discovery prefers an **already registered**
in-tree subclass over entry points. While both are present, resolving
`environment_type=conda` uses the in-tree backend; this package is the
**extract / fallback** implementation for ASV builds that omit optional
in-tree env plugins.

Do not install two different third-party providers that both advertise
the same entry-point name under `asv.environment_backends` (fail-closed).

## Requirements

- `conda` on `PATH` (or `CONDA_EXE` set), as for classic ASV conda envs.
- Host ASV with `asv.envmgmt.discover` (Stage-1) or conf `plugins` import.

## Tests

```bash
pip install -e ".[test]"
pytest -q
```
