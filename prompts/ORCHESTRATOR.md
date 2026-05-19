# Demand-to-MVP Radar — Local Orchestrator Entry

This project does not use the upstream Claude-wrapped orchestrator template.

Active orchestrator prompt:

- `docs/prompts/ORCHESTRATOR.md`

Run the active prompt directly in the current Codex session.

Rules:

- Do not use Claude Code as an outer orchestration layer.
- Do not call `codex exec` from inside Codex.
- Keep orchestration, implementation, review, consolidation, and doc updates in the current Codex session.
