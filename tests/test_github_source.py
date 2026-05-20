from __future__ import annotations

import json
from pathlib import Path

from demand_mvp_radar.sources.github_repo import (
    GitHubRepoSnapshotImporter,
    read_github_repo_snapshot,
    repository_identifier_hash,
)
from demand_mvp_radar.storage.db import connect_database
from demand_mvp_radar.storage.migrations import create_schema
from demand_mvp_radar.tools.executor import ToolExecutor

FIXTURE = Path(__file__).parent / "fixtures" / "github_repo"
REPOSITORY_IDENTIFIER = "owner/demand-signal-helper"


def test_local_repo_snapshot_imports_project_evidence() -> None:
    result = GitHubRepoSnapshotImporter().import_repository(
        FIXTURE,
        run_id="run-github-001",
        repository_identifier=REPOSITORY_IDENTIFIER,
    )

    assert len(result.evidence) == 4
    source_text = " ".join(record.normalized_text for record in result.evidence)
    titles = {record.title for record in result.evidence}

    assert "Demand Signal Helper" in titles
    assert "Need a simpler eval loop" in titles
    assert "Repository TODOs" in titles
    assert "Recent repository changes" in titles
    assert "prompt review process is too manual" in source_text
    assert all(record.source_type == "github_repo" for record in result.evidence)
    assert all(record.source_url.startswith("github_repo:") for record in result.evidence)


def test_local_repo_import_excludes_private_and_generated_paths() -> None:
    result = GitHubRepoSnapshotImporter().import_repository(
        FIXTURE,
        run_id="run-github-001",
        repository_identifier=REPOSITORY_IDENTIFIER,
    )
    serialized = " ".join(record.model_dump_json() for record in result.evidence)

    assert "PLACEHOLDER_VALUE" not in serialized
    assert "radar.sqlite3" not in serialized
    assert "do_not_import" not in serialized
    assert "private_report" not in serialized
    assert str(FIXTURE) not in serialized


def test_github_source_audit_redacts_private_paths(tmp_path) -> None:
    connection = connect_database(tmp_path / "radar.sqlite3")
    create_schema(connection)
    executor = ToolExecutor(
        {"read_github_repo_snapshot": read_github_repo_snapshot},
        connection=connection,
    )

    output = executor.execute(
        "read_github_repo_snapshot",
        {
            "run_id": "run-github-001",
            "repository_path": str(FIXTURE),
            "repository_identifier": REPOSITORY_IDENTIFIER,
        },
    )

    row = connection.execute(
        """
        SELECT run_id, tool_name, success, audit_fields
        FROM tool_audit_events
        WHERE tool_name = :tool_name
        """,
        {"tool_name": "read_github_repo_snapshot"},
    ).fetchone()
    audit_fields = json.loads(row["audit_fields"])

    assert output.source_count == 4
    assert output.error_count == 0
    assert row["run_id"] == "run-github-001"
    assert row["success"] == 1
    assert audit_fields == {
        "run_id": "run-github-001",
        "repository_id_hash": repository_identifier_hash(REPOSITORY_IDENTIFIER),
        "source_count": 4,
        "error_count": 0,
    }
    assert str(FIXTURE) not in row["audit_fields"]
    assert REPOSITORY_IDENTIFIER not in row["audit_fields"]
