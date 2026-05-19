from __future__ import annotations

import importlib
import importlib.metadata
import json
import subprocess
import sys
import tomllib
from pathlib import Path

import demand_mvp_radar

ROOT = Path(__file__).resolve().parents[1]


def test_cli_help_exits_zero() -> None:
    console_script = Path(sys.executable).with_name("demand-mvp-radar")
    result = subprocess.run(
        [str(console_script), "--help"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "demand-mvp-radar" in result.stdout


def test_package_version_matches_pyproject() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())

    assert demand_mvp_radar.__version__ == pyproject["project"]["version"]
    assert importlib.metadata.version("demand-mvp-radar") == pyproject["project"]["version"]


def test_core_packages_import() -> None:
    packages = [
        "demand_mvp_radar.storage",
        "demand_mvp_radar.sources",
        "demand_mvp_radar.tools",
        "demand_mvp_radar.retrieval",
        "demand_mvp_radar.llm",
        "demand_mvp_radar.reports",
    ]

    for package in packages:
        importlib.import_module(package)


def test_pytest_discovers_smoke_suite() -> None:
    smoke_tests = [
        name for name, value in globals().items() if name.startswith("test_") and callable(value)
    ]

    assert len(smoke_tests) >= 3


def test_health_json_contains_required_keys() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "demand_mvp_radar.cli", "health", "--json"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert {"status", "database", "report_dir", "configured_sources"} <= payload.keys()
