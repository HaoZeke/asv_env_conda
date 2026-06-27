# asv_env_conda

ASV environment backend plugin for `environment_type = "conda"`.

## Install (HaoZeke / editable)

```bash
pip install "git+https://github.com/HaoZeke/asv_env_conda.git"
# or clone and: pip install -e .
```

## Configure

```json
{
  "environment_type": "conda",
  "plugins": ["asv_env_conda"]
}
```

Core ASV ships **virtualenv** only. Plugins use the shared `asv_env_*` naming so they are easy to find and load via the `plugins` list (and optional `asv.plugins` entry points when ASV grows auto-discovery).
