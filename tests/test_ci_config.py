from __future__ import annotations

import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text()


def test_ci_workflow_has_required_steps() -> None:
    workflow = read_text(".github/workflows/ci.yml")

    assert 'python-version: "3.12"' in workflow
    assert re.search(r"name:\s+Install dependencies", workflow)
    assert re.search(r"name:\s+Ruff check", workflow)
    assert re.search(r"name:\s+Ruff format check", workflow)
    assert re.search(r"name:\s+Pytest", workflow)
    assert "ruff check demand_mvp_radar/ tests/" in workflow
    assert "ruff format --check demand_mvp_radar/ tests/" in workflow
    assert "python -m pytest tests/ -q" in workflow


def test_dev_requirements_include_test_and_lint_tools() -> None:
    requirements = read_text("requirements-dev.txt").splitlines()
    package_names = {
        re.split(r"[<>=!~]", requirement, maxsplit=1)[0]
        for requirement in requirements
        if requirement and not requirement.startswith("-")
    }

    assert "-r requirements.txt" in requirements
    assert {"pytest", "ruff"} <= package_names


def test_ruff_config_targets_project_paths() -> None:
    pyproject = tomllib.loads(read_text("pyproject.toml"))
    ruff = pyproject["tool"]["ruff"]

    assert "demand_mvp_radar" in ruff["src"]
    assert "tests" in ruff["src"]
    assert "demand_mvp_radar/**/*.py" in ruff["include"]
    assert "tests/**/*.py" in ruff["include"]
