# Implementation Reference Map

Last updated: 2026-05-19

## Purpose

This document maps the RAG implementation patterns in `ashishki/Dream_Motif_Interpreter` to the planned Demand-to-MVP Radar RAG layer. It is a retrieval aid for implementers, not canonical architecture. Canonical rules remain in `docs/ARCHITECTURE.md`, `docs/IMPLEMENTATION_CONTRACT.md`, `docs/spec.md`, and `docs/tasks.md`.

Reference repository:

- https://github.com/ashishki/Dream_Motif_Interpreter

## Rule of Use

Use the reference for:

- source connector and normalized document boundary shape
- staged ingestion pipeline before embeddings
- ingestion/query module separation
- token-aware chunking tests
- typed embedding error handling and observability
- `insufficient_evidence` behavior
- retrieval evaluation dataset/history structure
- regression slices for exact recall, stale corpus, and false-positive suppression
- external research trust-boundary language

Do not copy directly:

- dream-domain models, prompts, routes, or motif semantics
- PostgreSQL/pgvector as a v1 requirement
- Redis/background worker topology
- Telegram bot interaction model
- dream-specific parser profiles or Russian-language query expansion terms
- private archive assumptions

## File-to-Target Map

| Reference file | Useful pattern | Demand-to-MVP target |
|----------------|----------------|----------------------|
| `app/retrieval/types.py` | `SourceDocumentRef`, `FetchedSourceDocument`, `NormalizedDocument`, connector protocols, shared embedding client | `demand_mvp_radar/sources/base.py`, `demand_mvp_radar/models.py`, `demand_mvp_radar/retrieval/embeddings.py` |
| `app/retrieval/ingestion.py` | canonical pipeline: fetch -> normalize -> parse -> validate -> chunk -> embed -> index; duplicate content hash skip; token-aware chunking | `demand_mvp_radar/retrieval/ingestion.py`, `demand_mvp_radar/retrieval/chunking.py`, T09 |
| `app/retrieval/query.py` | separate query service, `InsufficientEvidence`, evidence fragments, hybrid lexical/vector idea, probe merge/dedupe | `demand_mvp_radar/retrieval/query.py`, `demand_mvp_radar/retrieval/index.py`, T10 |
| `scripts/eval.py` | markdown-driven eval dataset, history parsing, metrics calculation, eval source/date enforcement | `scripts/eval_retrieval.py`, `docs/retrieval_eval.md`, T09/T10/T18 |
| `docs/retrieval_eval.md` | separation of retrieval quality and answer quality; regression datasets; eval validity rule | `docs/retrieval_eval.md` |
| `tests/unit/test_rag_ingestion.py` | tests for module separation, token counting, embedding errors, duplicate skips | `tests/test_retrieval.py`, `tests/eval/test_retrieval_eval.py` |
| `tests/unit/test_rag_query.py` | tests for query module separation, empty query insufficient evidence, fragment coercion, exact recall helpers | `tests/test_retrieval_query.py` |
| `tests/unit/test_retrieval_eval.py` | tests that eval docs cover query types and have valid history rows | `tests/eval/test_retrieval_eval.py` |
| `tests/unit/test_source_connectors.py` | connector discovery separated from parsing, provenance preservation | `tests/test_sources.py`, T07 |
| `tests/unit/test_normalized_document.py` | normalized document required fields and side-effect-free normalization | `tests/test_sources.py`, `tests/test_retrieval.py` |
| `docs/RESEARCH_AUGMENTATION.md`, `docs/adr/ADR-009-research-trust-boundary.md` | external research outputs are low-trust, source-linked, timestamped, and vocabulary-limited | future source trust policy and opportunity-brief risk language |

## Reference Decisions to Port

1. Source adapters return source documents. They do not parse domain objects and do not start embeddings.
2. Normalization is a side-effect-free boundary with required provenance fields.
3. Embeddings run only after source validation and duplicate handling.
4. Ingestion code must not import query code; query code must not import ingestion code.
5. Query responses must distinguish evidence-backed results from `insufficient_evidence`.
6. Retrieval evaluation must have `Eval Source`, `Date`, and corpus/schema version in every completed row.
7. Regression datasets should capture real operator failures as named slices instead of hiding them in generic unit tests.
8. External web/search evidence is lower trust than first-party corpus evidence and must be labeled accordingly.

## Suggested Implementation Order

1. Read current task in `docs/tasks.md`.
2. Read the matching row in this map.
3. Inspect only the reference file(s) listed for that task.
4. Port the pattern, not the dream-domain code.
5. Preserve Demand-to-MVP architecture choices: local-first v1, SQLite, text-only retrieval, source provenance, and deterministic scoring.
