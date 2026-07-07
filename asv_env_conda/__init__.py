# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""ASV ``environment_type="conda"`` backend (conda CLI).

Core ASV does not ship this backend in-tree; this package is the provider.

Discovery: entry point group ``asv.environment_backends``, name ``conda``.
"""

import contextlib
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from packaging.version import Version

from asv import environment, util
from asv.console import log

WIN = os.name == "nt"

util.new_multiprocessing_lock("conda_lock")


def _conda_lock():
    return util.get_multiprocessing_lock("conda_lock")


@contextlib.contextmanager
def _dummy_lock():
    yield


def _candidate_conda_bins():
    """Yield candidate conda executable paths (env, PATH, common prefixes)."""
    seen = set()
    for key in ("CONDA_EXE", "ASV_CONDA_EXE"):
        val = os.environ.get(key)
        if val and val not in seen:
            seen.add(val)
            yield val
    which = shutil.which("conda")
    if which and which not in seen:
        seen.add(which)
        yield which
    # Common installs (Miniforge/Miniconda/Anaconda)
    home = Path.home()
    for rel in (
        "miniforge3/bin/conda",
        "mambaforge/bin/conda",
        "miniconda3/bin/conda",
        "anaconda3/bin/conda",
        "opt/conda/bin/conda",
    ):
        p = home / rel
        if p.is_file():
            s = str(p)
            if s not in seen:
                seen.add(s)
                yield s


def _conda_works(conda: str) -> bool:
    """Return True if *conda* runs ``--version`` successfully."""
    try:
        r = subprocess.run(
            [conda, "--version"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if r.returncode != 0:
            return False
        out = (r.stdout or "") + (r.stderr or "")
        return bool(re.search(r"conda\s+\d", out, re.I) or re.search(r"\d+\.\d+", out))
    except (OSError, subprocess.TimeoutExpired):
        return False


def _find_conda():
    """
    Find a *working* conda executable.

    Raises
    ------
    OSError
        If no working conda is found (broken stubs on PATH are skipped).
    """
    tried = []
    for cand in _candidate_conda_bins():
        tried.append(cand)
        if os.path.isfile(cand) and os.access(cand, os.X_OK) and _conda_works(cand):
            return cand
    raise OSError(
        "No working conda executable found (set CONDA_EXE or ASV_CONDA_EXE to a "
        f"real conda, not a broken stub). Tried: {tried or ['(none)']}"
    )


class Conda(environment.Environment):
    """Manage an environment using the conda CLI."""

    tool_name = "conda"
    _matches_cache = {}

    def __init__(self, conf, python, requirements, tagged_env_vars):
        self._python = python
        self._requirements = requirements
        self._conda_channels = list(conf.conda_channels or [])
        if "conda-forge" not in self._conda_channels:
            self._conda_channels += ["conda-forge"]
        self._conda_environment_file = conf.conda_environment_file

        if conf.conda_environment_file == "IGNORE":
            log.debug("Skipping environment file due to conda_environment_file set to IGNORE")
            self._conda_environment_file = None
        elif not conf.conda_environment_file:
            if Path("environment.yml").exists():
                log.debug("Using environment.yml")
                self._conda_environment_file = "environment.yml"

        # Fail early if conda is missing/broken
        try:
            self._conda_bin = _find_conda()
        except OSError as err:
            raise environment.EnvironmentUnavailable(str(err)) from err

        super().__init__(conf, python, requirements, tagged_env_vars)

    @classmethod
    def matches(cls, python):
        if python not in cls._matches_cache:
            cls._matches_cache[python] = cls._matches(python)
        return cls._matches_cache[python]

    @classmethod
    def _matches(cls, python):
        if not re.match(r"^[0-9].*$", python):
            return False
        try:
            conda = _find_conda()
        except OSError:
            return False
        try:
            with _conda_lock():
                return util.search_channels(conda, "python", python)
        except (util.ProcessError, OSError, Exception):
            # If channel search fails, still allow when conda works (offline etc.)
            return True

    def _setup(self):
        log.info(f"Creating conda environment for {self.name}")

        conda_args, pip_args = self._get_requirements()
        env = dict(os.environ)
        env.update(self.build_env_vars)
        conda_args = [util.replace_cpython_version(arg, self._python) for arg in conda_args]

        if not self._conda_environment_file:
            conda_args = [f"python={self._python}", "wheel", "pip"] + conda_args

        env_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".yml")
        try:
            env_file.write(f"name: {self.name}\nchannels:\n")
            env_file.writelines(f"   - {ch}\n" for ch in self._conda_channels)
            if conda_args or pip_args:
                env_file.write("dependencies:\n")
            if conda_args:
                env_file.writelines(f"   - {s}\n" for s in conda_args)
            if pip_args:
                env_file.write("   - pip:\n")
                env_file.writelines(f"      - {s}\n" for s in pip_args)
            env_file.close()
            try:
                env_file_name = self._conda_environment_file or env_file.name

                ver_out = self._run_conda(["--version"], env=env)
                conda_version = re.search(r"\d+(\.\d+)+", ver_out)[0]
                log.info(f"conda version: {conda_version}")
                if Version(conda_version) >= Version("24.3.0"):
                    self._run_conda(
                        ["env", "create", "-f", env_file_name, "-p", self._path, "--yes"],
                        env=env,
                    )
                else:
                    self._run_conda(
                        ["env", "create", "-f", env_file_name, "-p", self._path, "--force"],
                        env=env,
                    )

                if self._conda_environment_file and (conda_args or pip_args):
                    env_file_name = env_file.name
                    self._run_conda(
                        ["env", "update", "-f", env_file_name, "-p", self._path], env=env
                    )
            except Exception:
                if env_file_name != env_file.name:
                    log.info(
                        "conda env create/update failed: "
                        f"in {self._path} with file {env_file_name}"
                    )
                elif os.path.isfile(env_file_name):
                    with open(env_file_name, "r") as f:
                        text = f.read()
                    log.info(f"conda env create/update failed: in {self._path} with:\n{text}")
                raise
        finally:
            os.unlink(env_file.name)
        if pip_args:
            for declaration in pip_args:
                parsed_declaration = util.ParsedPipDeclaration(declaration)
                pip_call = util.construct_pip_call(self._run_pip, parsed_declaration)
                pip_call()

    def _get_requirements(self):
        conda_args = []
        pip_args = []
        for key, val in {**self._requirements, **self._base_requirements}.items():
            if key.startswith("pip+"):
                pip_args.append(f"{key[4:]} {val}")
            else:
                if val:
                    conda_args.append(f"{key}={val}")
                else:
                    conda_args.append(key)
        return conda_args, pip_args

    def _run_conda(self, args, env=None):
        try:
            conda = getattr(self, "_conda_bin", None) or _find_conda()
        except OSError as e:
            raise util.UserError(str(e))
        with _conda_lock():
            return util.check_output([conda] + args, timeout=self._install_timeout, env=env)

    def run(self, args, **kwargs):
        log.debug(f"Running '{' '.join(args)}' in {self.name}")
        return self.run_executable("python", args, **kwargs)

    def run_executable(self, executable, args, **kwargs):
        if executable == "conda":
            executable = getattr(self, "_conda_bin", None) or _find_conda()
            lock = _conda_lock
        else:
            lock = _dummy_lock
        kwargs["env"] = dict(kwargs.pop("env", os.environ), PYTHONNOUSERSITE="True")
        with lock():
            return super().run_executable(executable, args, **kwargs)

    def _run_pip(self, args, **kwargs):
        return self.run_executable("python", ["-m", "pip"] + list(args), **kwargs)


__all__ = ["Conda", "_conda_lock", "_find_conda", "_conda_works"]
