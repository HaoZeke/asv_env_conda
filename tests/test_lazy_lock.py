# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""Import must not allocate a multiprocessing semaphore."""


def test_import_does_not_require_precreated_lock():
    import importlib
    import asv_env_conda as m

    importlib.reload(m)
    # After reload, lock is lazy: module load should succeed even if lock
    # was never registered yet. Creating the lock happens on first use.
    assert m._lock_ready is False or m._lock_ready is True
    # First lock acquisition initializes
    with m._conda_lock():
        pass
    assert m._lock_ready is True


def test_module_source_no_import_time_new_lock():
    from pathlib import Path
    import asv_env_conda

    src = Path(asv_env_conda.__file__).read_text()
    # ban *module-level* util.new_multiprocessing_lock(...) (column 0).
    # Calls indented inside _ensure_conda_lock are the intended lazy path.
    for line in src.splitlines():
        if line.startswith("util.new_multiprocessing_lock"):
            raise AssertionError(f"import-time lock: {line!r}")
        if line.startswith("new_multiprocessing_lock"):
            raise AssertionError(f"import-time lock: {line!r}")
