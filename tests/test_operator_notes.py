from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from demand_mvp_radar.models import EvidenceRecord, OpportunityCandidate
from demand_mvp_radar.scoring import ScoringConfig, score_opportunity
from demand_mvp_radar.sources.operator_notes import (
    REDACTED_NOTE_REFERENCE,
    OperatorNotesAdapter,
)

FIXTURE = Path(__file__).parent / "fixtures" / "operator_notes" / "private_signal.md"


def test_markdown_operator_notes_import_as_evidence() -> None:
    result = OperatorNotesAdapter().import_file(FIXTURE, run_id="run-notes-001")

    assert len(result.evidence) == 1
    note = result.evidence[0]
    assert note.source_type == "operator_note"
    assert note.source_id == "operator-note-001"
    assert note.captured_at.isoformat() == "2026-05-18T09:30:00+00:00"
    assert note.title == "Inbox triage pain"
    assert note.normalized_text == (
        "I keep seeing small teams lose track of customer follow-ups after founder "
        "calls. The pain is strongest when notes live across chat, inbox, and task tools."
    )
    assert note.content_hash


def test_operator_notes_alone_do_not_justify_build() -> None:
    notes = (
        _evidence("operator-note-001", "operator_note"),
        _evidence("operator-note-002", "operator_note"),
    )
    candidate = _candidate("operator-note-001", "operator-note-002")

    score = score_opportunity(
        candidate,
        notes,
        config=ScoringConfig(build_threshold=50, minimum_evidence_count=2),
        as_of=datetime(2026, 5, 20, tzinfo=UTC),
    )

    assert score.total_score >= 50
    assert score.recommendation == "revisit"
    assert "operator notes require corroborating non-note source" in score.threshold_reasons


def test_private_note_paths_are_redacted(tmp_path) -> None:
    private_path = tmp_path / "private" / "notes" / "personal_signal.md"
    private_path.parent.mkdir(parents=True)
    private_path.write_text(FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")

    result = OperatorNotesAdapter().import_file(private_path, run_id="run-notes-001")
    note = result.evidence[0]
    serialized = note.model_dump_json()

    assert note.source_url == REDACTED_NOTE_REFERENCE
    assert str(private_path) not in serialized
    assert "personal_signal.md" not in serialized


def _candidate(*source_evidence_ids: str) -> OpportunityCandidate:
    return OpportunityCandidate(
        opportunity_id="opp_operator_note_fixture",
        normalized_pain="follow-up tracking",
        target_audience="small teams",
        workflow="follow_up",
        acquisition_channel="search",
        source_evidence_ids=tuple(source_evidence_ids),
        candidate_title="Founder Call Follow-Up Tracker",
    )


def _evidence(source_id: str, source_type: str) -> EvidenceRecord:
    return EvidenceRecord(
        run_id="run-notes-001",
        source_type=source_type,
        source_id=source_id,
        source_url=REDACTED_NOTE_REFERENCE,
        captured_at=datetime(2026, 5, 18, 12, 0, tzinfo=UTC),
        title="Inbox triage pain",
        snippet="Small teams lose track of customer follow-ups after founder calls.",
        normalized_text="Small teams lose track of customer follow-ups after founder calls.",
        content_hash=f"hash-{source_id}",
        source_fingerprint=f"{source_type}:{source_id}:hash-{source_id}",
    )
