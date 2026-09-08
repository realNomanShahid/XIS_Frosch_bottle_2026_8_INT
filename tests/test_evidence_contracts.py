"""Evidence / docs layout contracts (supports A12-style checks).


"""
from __future__ import annotations

from pathlib import Path

import pytest

REQUIRED_DOCS = [
    "README.md",
    "camerasetup.md",
    "optimization.md",
    "results.md",
    "results_saving.md",
]

REQUIRED_ARTIFACTS = [
    "DEC-FROSCH-0001.md",
    "DEC-FROSCH-0002.md",
    "EXC-NONE.md",
    "PRJ-FROSCH-DS-INV-v1.md",
    "PRJ-FROSCH-DSV-v1.md",
    "PRJ-FROSCH-EVAL-v1.md",
    "PRJ-FROSCH-FBA-001.md",
    "PRJ-FROSCH-MPR-v1.md",
    "PRJ-FROSCH-MVR-v1.md",
    "PRJ-FROSCH-QA-001.md",
    "PRJ-FROSCH-RCA-001.md",
    "PRJ-FROSCH-REL-v0.md",
    "PRJ-FROSCH-RUN-DET-0001.md",
    "PRJ-FROSCH-RUN-SEG-0001.md",
    "PRJ-FROSCH-SCHEMA-v1.md",
    "PRJ-FROSCH-SOAK-001.md",
    "TASK-INTER-54-OBJ-v1.md",
    "TASK-INTER-54-QS.md",
    "TASK-INTER-54-RE-1.md",
]


def test_docs_present(repo_root: Path):
    docs = repo_root / "docs" / "mdFiles"
    assert docs.is_dir(), "docs/mdFiles/ missing - has the docs layout moved again?"
    for name in REQUIRED_DOCS:
        assert (docs / name).is_file(), f"Missing docs/mdFiles/{name}"


def test_artifacts_present(repo_root: Path):
    artifacts = repo_root / "docs" / "artifacts"
    assert artifacts.is_dir(), "docs/artifacts/ missing"
    for name in REQUIRED_ARTIFACTS:
        assert (artifacts / name).is_file(), f"Missing docs/artifacts/{name}"


def test_root_readme_exists(repo_root: Path):
    assert (repo_root / "README.md").is_file()


def test_requirements_exists(repo_root: Path):
    assert (repo_root / "requirements.txt").is_file()


def test_requirements_lock_is_not_empty(repo_root: Path):
    """A lockfile that pins nothing isn't a lockfile (handbook S5.1.2)."""
    lock = repo_root / "requirements.lock"
    if not lock.is_file():
        pytest.skip("requirements.lock not present yet")
    assert lock.stat().st_size > 0, (
        "requirements.lock exists but is empty - it needs to be generated "
        "from a real environment (pip freeze / pip-compile), not committed "
        "as a placeholder."
    )


def test_gitignore_exists(repo_root: Path):
    assert (repo_root / ".gitignore").is_file()


def test_results_sample_layout_optional(repo_root: Path):
    """If results/ exists, capacity folders should hold csv/json pairs."""
    results = repo_root / "results"
    if not results.is_dir():
        pytest.skip("results/ not present yet")
    csvs = list(results.rglob("bottles_data.csv"))
    # Optional: project may only create results after a run
    if not csvs:
        pytest.skip("no bottles_data.csv under results/ yet")
    for csv_path in csvs:
        json_path = csv_path.with_name("bottles_data.json")
        assert json_path.is_file(), f"CSV without JSON: {csv_path}"