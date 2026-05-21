from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_CORPUS = ROOT / "tests" / "fixtures" / "retrieval_live_public_corpus.json"
PUBLIC_QUERIES = ROOT / "tests" / "fixtures" / "retrieval_live_public_queries.json"


def test_live_public_eval_fixture_covers_required_sources() -> None:
    corpus = json.loads(PUBLIC_CORPUS.read_text(encoding="utf-8"))
    queries = json.loads(PUBLIC_QUERIES.read_text(encoding="utf-8"))

    source_types = {item["source_type"] for item in corpus["evidence"]}

    assert len(queries["queries"]) >= 10
    assert {"hacker_news", "stack_exchange", "rss", "github_public"} <= source_types
    assert set(corpus["public_source_types"]) == {
        "hacker_news",
        "stack_exchange",
        "rss",
        "github_public",
    }


def test_live_public_eval_reports_required_metrics() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/eval_retrieval.py",
            "--fixture",
            str(PUBLIC_QUERIES),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    result = json.loads(completed.stdout)

    assert result["corpus_version"] == "corpus-t47-public-live-v1"
    assert result["query_count"] == 10
    assert result["hit@3"] == 1.0
    assert result["citation_precision"] == 1.0
    assert result["no_answer_accuracy"] == 1.0
    assert result["answer_faithfulness"] == 1.0
    assert result["freshness_compliance"] == 1.0
    assert result["source_diversity"] == 1.0
    assert result["public_source_coverage"] == 1.0


def test_live_public_eval_updates_retrieval_docs() -> None:
    content = (ROOT / "docs" / "retrieval_eval.md").read_text(encoding="utf-8")

    assert "T47" in content
    assert "corpus-t47-public-live-v1" in content
    assert "public_source_coverage=1.00" in content
    assert "Hacker News, Stack Exchange, RSS, and GitHub public" in content
    assert "Public source coverage below 1.00" in content
