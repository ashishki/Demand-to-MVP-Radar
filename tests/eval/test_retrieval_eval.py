from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


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
