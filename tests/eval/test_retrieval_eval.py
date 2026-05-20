from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIVE_CORPUS = ROOT / "tests" / "fixtures" / "retrieval_live_like_corpus.json"
LIVE_QUERIES = ROOT / "tests" / "fixtures" / "retrieval_live_like_queries.json"


def test_ingestion_baseline_row_has_required_fields() -> None:
    content = (ROOT / "docs" / "retrieval_eval.md").read_text()
    expected = (
        r"\| 2026-05-19 \| T09 \| corpus-t09-v1 \| "
        r"`python scripts/eval_retrieval.py --fixture "
        r"tests/fixtures/retrieval_corpus.json, run 2026-05-19` \| "
        r"n/a \| n/a \| n/a \| n/a \| n/a \| "
        r"chunk_count=3; index_schema_version=retrieval-index-v1; "
        r"embedding_model=local-hash-embedding-v1 \|"
    )

    assert re.search(expected, content)


def test_query_eval_row_has_required_metrics() -> None:
    content = (ROOT / "docs" / "retrieval_eval.md").read_text()
    expected = (
        r"\| 2026-05-19 \| T10 \| corpus-t10-v1 \| "
        r"`python scripts/eval_retrieval.py --fixture "
        r"tests/fixtures/retrieval_queries.json, run 2026-05-19` \| "
        r"1.00 \| 1.00 \| 1.00 \| 1.00 \| "
        r"\d+ms \| "
        r"query_count=4; index_schema_version=retrieval-index-v1; "
        r"embedding_model=local-hash-embedding-v1 \|"
    )

    assert re.search(expected, content)


def test_final_retrieval_baseline_contains_required_metrics() -> None:
    content = (ROOT / "docs" / "retrieval_eval.md").read_text()
    expected = (
        r"\| 2026-05-19 \| T18 \| corpus-t10-v1 \| "
        r"`python scripts/eval_retrieval.py --fixture "
        r"tests/fixtures/retrieval_queries.json, run 2026-05-19` \| "
        r"1.00 \| 1.00 \| 1.00 \| 1.00 \| "
        r"\d+ms \| "
        r"final_baseline=true; query_count=4; "
        r"index_schema_version=retrieval-index-v1; "
        r"embedding_model=local-hash-embedding-v1 \|"
    )

    assert re.search(expected, content)


def test_live_like_eval_fixture_has_required_source_coverage() -> None:
    corpus = json.loads(LIVE_CORPUS.read_text())
    queries = json.loads(LIVE_QUERIES.read_text())

    source_types = {item["source_type"] for item in corpus["evidence"]}

    assert len(source_types) >= 5
    assert len(queries["queries"]) >= 10
    assert {
        "telegram_research_agent",
        "operator_note",
        "github_repo",
        "serp",
        "hacker_news",
    } <= source_types


def test_live_like_eval_reports_extended_metrics() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/eval_retrieval.py",
            "--fixture",
            str(LIVE_QUERIES),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    result = json.loads(completed.stdout)

    assert result["query_count"] == 10
    assert result["hit@3"] == 1.0
    assert result["citation_precision"] == 1.0
    assert result["no_answer_accuracy"] == 1.0
    assert result["answer_faithfulness"] == 1.0
    assert result["freshness_compliance"] == 1.0
    assert result["source_diversity"] == 1.0


def test_retrieval_eval_records_regression_cause() -> None:
    content = (ROOT / "docs" / "retrieval_eval.md").read_text()

    assert "code-change-induced" in content
    assert "corpus-change-induced" in content
