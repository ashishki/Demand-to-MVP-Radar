# Pathway Live Intelligence Context

Status: active implementation roadmap
Last updated: 2026-06-12

## Decision

Demand-to-MVP Radar should consume Telegram Research Agent live source
intelligence as optional context, not as decision-grade external evidence.

The artifact may be produced by a Pathway sidecar or a deterministic fallback
builder over the same append-only source event stream. Radar must not care which
runtime generated it. Radar only requires a bounded JSON contract.

## Contract

Input:

```text
--live-intelligence /path/to/live_source_intelligence/YYYY-WNN.json
```

Allowed use:

- add a Candidate Dossier context section;
- expose snapshot freshness, event counts, top channels, demand surfaces, and
  repeated-claim candidates in JSON;
- guide the next experiment wording and missing-evidence hints.

Disallowed use:

- increase external evidence count;
- mark `readiness=externally_corroborated`;
- satisfy Reddit/GitHub/SERP/Product Hunt/YouTube/Stack Exchange source gates;
- turn a Telegram-only candidate into `focused_experiment` or `build`.

## Tasks

### PTH-RADAR-1 - Read Live Intelligence Snapshot

Status: implemented.

Acceptance:

- CLI accepts `--live-intelligence PATH`.
- `run_mvp_of_week(...)` loads and validates the JSON when supplied.
- Markdown includes `## Live Source Intelligence` for supplied context.
- JSON payload and `source_counts` include the live context summary.
- Existing source-mix gate tests keep passing.

Implemented in `demand_mvp_radar.cli` and `demand_mvp_radar.mvp_weekly`.
The snapshot is exposed in Markdown/JSON and `source_counts` as context only.

### PTH-RADAR-2 - Optional Future Pathway Retrieval

Status: future.

Acceptance:

- If a Pathway service is later exposed over HTTP, add a collector that produces
  the same JSON contract.
- Do not add the service as a required runtime dependency for weekly Radar.
