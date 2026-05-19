# Retrieval Evaluation

Project: Demand-to-MVP Radar
Profile: RAG
Retrieval mode: text-only
Index schema version: retrieval-index-v1
Status: initialized before implementation

---

## Evaluation Purpose

Retrieval quality determines whether opportunity briefs are evidence-backed or speculative. This artifact tracks corpus versions, retrieval metrics, answer quality, insufficient-evidence behavior, and regressions separately from unit tests.

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
| citation_precision | Share of cited packets that support the candidate claim. | 0.80 after baseline |
| no_answer_accuracy | Share of unsupported queries that return `insufficient_evidence`. | 0.90 after baseline |
| answer_faithfulness | Share of synthesized claims supported by retrieved evidence. | 0.85 after baseline |
| retrieval_ms | Query-time retrieval latency over fixture set. | record baseline, no target before T10 |

---

## Evaluation History

| Date | Task | Corpus Version | Eval Source | hit@3 | citation_precision | no_answer_accuracy | answer_faithfulness | retrieval_ms | Notes |
|------|------|----------------|-------------|-------|--------------------|--------------------|---------------------|--------------|-------|
| 2026-05-19 | bootstrap | n/a | not yet run - dataset initialized before implementation | n/a | n/a | n/a | n/a | n/a | Baseline will be established by T09/T10. |

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
