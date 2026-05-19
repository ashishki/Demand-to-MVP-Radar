# Retrieval Evaluation

Project: Demand-to-MVP Radar
Profile: RAG
Retrieval mode: text-only
Index schema version: retrieval-index-v1
Status: initialized before implementation

---

## Evaluation Purpose

Retrieval quality determines whether opportunity briefs are evidence-backed or speculative. This artifact tracks corpus versions, retrieval metrics, answer quality, insufficient-evidence behavior, and regressions separately from unit tests.

Reference note: `ashishki/Dream_Motif_Interpreter` is the implementation pattern reference for markdown-driven retrieval evaluation, eval-history parsing, and regression slices. Port the evaluation shape, not the dream-domain dataset or pgvector dependency.

---

## Evaluation Dataset

Initial dataset to be created during T09/T10:

| Query ID | Query | Expected Evidence | Expected Behavior |
|----------|-------|-------------------|-------------------|
| Q01 | Excel formula helper demand | Telegram/source snippets about spreadsheet formula pain | retrieve evidence |
| Q02 | prerender or SEO rendering pain | Source snippets about prerendering / bot rendering demand | retrieve evidence |
| Q03 | YouTube to podcast workflow | Source snippets about turning videos into audio/podcast output | retrieve evidence |
| Q04 | PDF converter demand | Source snippets about PDF conversion or document workflow | retrieve evidence |
| Q05 | 10000 steps experimentation framing | Source snippets about repeated experiments and distribution | retrieve evidence |
| Q06 | unsupported medical diagnosis automation | none in v1 corpus | insufficient_evidence |
| Q07 | acquisition channel for spreadsheet tools | competitor/source snippets with SEO or search intent | retrieve evidence |
| Q08 | rejected idea recurrence | prior decision fixture | retrieve evidence |
| Q09 | stale-only source candidate | stale fixture only | insufficient_evidence |
| Q10 | no source links candidate | fixture without source links | insufficient_evidence |

---

## Metrics

| Metric | Definition | Initial Target |
|--------|------------|----------------|
| hit@3 | Expected evidence appears in top 3 retrieved packets. | 0.80 after baseline |
| MRR | Mean reciprocal rank for expected evidence across answerable queries. | record baseline, then no regression above threshold |
| citation_precision | Share of cited packets that support the candidate claim. | 0.80 after baseline |
| no_answer_accuracy | Share of unsupported queries that return `insufficient_evidence`. | 0.90 after baseline |
| answer_faithfulness | Share of synthesized claims supported by retrieved evidence. | 0.85 after baseline |
| retrieval_ms | Query-time retrieval latency over fixture set. | record baseline, no target before T10 |

---

## Regression Dataset Policy

When the operator reports a bad search, weak recommendation, stale source, or false-positive evidence issue, add a named regression slice to this file before changing retrieval behavior. Each slice must include:

- query or candidate ID
- query text or candidate description
- expected relevant evidence or expected `insufficient_evidence`
- false-positive or false-negative rule
- evidence source fixture or corpus version
- eval command or test that verifies the regression

Initial slices to add during implementation:

| Slice | Trigger | Expected Coverage |
|-------|---------|-------------------|
| Exact recall | Operator says a known source phrase or product category was missed | lexical/exact path surfaces source-backed evidence even if vector score is weak |
| Stale source | Only old evidence supports a candidate | query returns `insufficient_evidence` or freshness warning |
| No source links | Candidate has plausible text but no inspectable source links | query returns `insufficient_evidence` |
| Rejected idea recurrence | Candidate resembles a recently rejected opportunity | retrieval surfaces decision history for suppression/scoring |
| Weak competitor evidence | Candidate has competitors but no demand signal | report marks risk instead of build recommendation |

---

## Evaluation History

| Date | Task | Corpus Version | Eval Source | hit@3 | citation_precision | no_answer_accuracy | answer_faithfulness | retrieval_ms | Notes |
|------|------|----------------|-------------|-------|--------------------|--------------------|---------------------|--------------|-------|
| 2026-05-19 | bootstrap | n/a | not yet run - dataset initialized before implementation | n/a | n/a | n/a | n/a | n/a | Baseline will be established by T09/T10. |
| 2026-05-19 | T09 | corpus-t09-v1 | `python scripts/eval_retrieval.py --fixture tests/fixtures/retrieval_corpus.json, run 2026-05-19` | n/a | n/a | n/a | n/a | n/a | chunk_count=3; index_schema_version=retrieval-index-v1; embedding_model=local-hash-embedding-v1 |
| 2026-05-19 | T10 | corpus-t10-v1 | `python scripts/eval_retrieval.py --fixture tests/fixtures/retrieval_queries.json, run 2026-05-19` | 1.00 | 1.00 | 1.00 | 1.00 | 2ms | query_count=4; index_schema_version=retrieval-index-v1; embedding_model=local-hash-embedding-v1 |
| 2026-05-19 | T18 | corpus-t10-v1 | `python scripts/eval_retrieval.py --fixture tests/fixtures/retrieval_queries.json, run 2026-05-19` | 1.00 | 1.00 | 1.00 | 1.00 | 2ms | final_baseline=true; query_count=4; index_schema_version=retrieval-index-v1; embedding_model=local-hash-embedding-v1 |

---

## Answer Quality Metrics

| Date | Task | Corpus Version | Eval Source | Faithfulness | Completeness | Relevance | Notes |
|------|------|----------------|-------------|--------------|--------------|-----------|-------|
| 2026-05-19 | bootstrap | n/a | not yet run - synthesis not implemented | n/a | n/a | n/a | Baseline will be established after retrieval and synthesis exist. |

---

## Regression Notes

None.

---

## Open Retrieval Findings

None.
