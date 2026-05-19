from __future__ import annotations

import argparse
import json
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path

from demand_mvp_radar.models import EvidenceRecord
from demand_mvp_radar.retrieval.ingestion import build_corpus
from demand_mvp_radar.retrieval.query import query_evidence
from demand_mvp_radar.storage.db import connect_database
from demand_mvp_radar.storage.migrations import create_schema
from demand_mvp_radar.storage.repositories import EvidenceRepository


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--database", default=":memory:")
    parser.add_argument("--corpus-version")
    args = parser.parse_args()

    payload = json.loads(Path(args.fixture).read_text())
    corpus_version = args.corpus_version or str(payload.get("corpus_version", "corpus-t09-v1"))
    if args.database == ":memory:":
        with tempfile.TemporaryDirectory() as temp_dir:
            result = _run_eval(
                Path(temp_dir) / "retrieval_eval.sqlite3",
                payload,
                corpus_version=corpus_version,
            )
    else:
        result = _run_eval(Path(args.database), payload, corpus_version=corpus_version)
    result["date"] = datetime.now(UTC).date().isoformat()
    print(json.dumps(result, sort_keys=True))
    return 0


def _run_eval(database_path: Path, payload: dict[str, object], *, corpus_version: str) -> dict[str, object]:
    connection = connect_database(database_path)
    create_schema(connection)

    rows = _write_evidence(connection, payload)
    result = build_corpus(connection, rows, corpus_version=corpus_version)
    if "queries" not in payload:
        return result

    result.update(_run_query_eval(connection, payload, corpus_version=corpus_version))
    return result


def _write_evidence(
    connection,
    payload: dict[str, object],
) -> list[tuple[int, EvidenceRecord]]:
    repository = EvidenceRepository(connection)
    rows: list[tuple[int, EvidenceRecord]] = []
    for item in payload["evidence"]:
        evidence = EvidenceRecord(
            run_id=str(payload["run_id"]),
            source_type=str(item["source_type"]),
            source_id=str(item["source_id"]),
            source_url=item.get("source_url"),
            captured_at=datetime.fromisoformat(str(item["captured_at"])),
            title=str(item["title"]),
            snippet=str(item["snippet"]),
            normalized_text=str(item["normalized_text"]),
            content_hash=str(item["content_hash"]),
            source_fingerprint=str(item["source_fingerprint"]),
        )
        evidence_id = repository.write(evidence)
        rows.append((evidence_id, evidence))
    return rows


def _run_query_eval(
    connection,
    payload: dict[str, object],
    *,
    corpus_version: str,
) -> dict[str, object]:
    queries = payload["queries"]
    hit_count = 0
    answerable_count = 0
    precision_scores: list[float] = []
    no_answer_correct = 0
    no_answer_count = 0
    faithfulness_scores: list[float] = []

    started = time.perf_counter()
    for item in queries:
        expected_status = str(item["expected_status"])
        expected_urls = set(item.get("expected_source_urls", []))
        response = query_evidence(
            connection,
            str(item["query"]),
            corpus_version=corpus_version,
            min_independent_sources=int(item.get("min_independent_sources", 2)),
            top_k=int(item.get("top_k", 3)),
            max_age_days=int(item.get("max_age_days", 365)),
            as_of=datetime.fromisoformat(str(payload["as_of"])),
        )
        returned_urls = {packet.source_url for packet in response.evidence_packets[:3]}

        if expected_status == "ok":
            answerable_count += 1
            if expected_urls and expected_urls <= returned_urls:
                hit_count += 1
            if response.evidence_packets:
                supporting = [
                    packet.source_url in expected_urls for packet in response.evidence_packets
                ]
                precision_scores.append(sum(supporting) / len(supporting))
                faithfulness_scores.append(1.0 if all(supporting) else 0.0)
            else:
                precision_scores.append(0.0)
                faithfulness_scores.append(0.0)
        else:
            no_answer_count += 1
            if response.status == "insufficient_evidence":
                no_answer_correct += 1

    elapsed_ms = int((time.perf_counter() - started) * 1000)
    return {
        "query_count": len(queries),
        "hit@3": _ratio(hit_count, answerable_count),
        "citation_precision": _average(precision_scores),
        "no_answer_accuracy": _ratio(no_answer_correct, no_answer_count),
        "answer_faithfulness": _average(faithfulness_scores),
        "retrieval_ms": elapsed_ms,
    }


def _ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 2)


def _average(values: list[float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 2)


if __name__ == "__main__":
    raise SystemExit(main())
