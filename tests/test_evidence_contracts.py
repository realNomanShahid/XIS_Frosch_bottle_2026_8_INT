"""Evidence / docs layout contracts (supports A12-style checks)."""
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


def test_docs_present(repo_root: Path):
    docs = repo_root / "docs"
    assert docs.is_dir()
    for name in REQUIRED_DOCS:
        assert (docs / name).is_file(), f"Missing docs/{name}"


def test_root_readme_exists(repo_root: Path):
    assert (repo_root / "README.md").is_file()


def test_requirements_exists(repo_root: Path):
    assert (repo_root / "requirements.txt").is_file()


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