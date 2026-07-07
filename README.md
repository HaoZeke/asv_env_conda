# asv_env_conda

ASV environment backend for `environment_type = "conda"` (conda CLI).

Core ASV (extract design) ships only **virtualenv** and **existing**.
This package is the **provider** for `conda` — there is no in-tree
`asv.plugins.conda`.

## Discovery

```toml
[project.entry-points."asv.environment_backends"]
conda = "asv_env_conda:Conda"
```

```bash
pip install "git+https://github.com/HaoZeke/asv_env_conda.git"
```

```json
{ "environment_type": "conda" }
```

Install into the host environment that runs ASV. Conf `plugins` is optional
when entry points are registered.

## Tests

```bash
pip install -e ".[test]"
pytest -q
```
