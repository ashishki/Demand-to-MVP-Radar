from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OPERATOR_WORKFLOW = ROOT / "docs" / "OPERATOR_WORKFLOW.md"
OPERATOR_RUNBOOK = ROOT / "docs" / "OPERATOR_RUNBOOK.md"
BACKUP_RECOVERY = ROOT / "docs" / "BACKUP_RECOVERY.md"
PRODUCTION_READINESS_REVIEW = ROOT / "docs" / "audit" / "PRODUCTION_READINESS_REVIEW.md"
LIVE_SOURCE_PRODUCTION_ROADMAP = ROOT / "docs" / "LIVE_SOURCE_PRODUCTION_ROADMAP.md"
PRIVATE_BETA_ONBOARDING = ROOT / "docs" / "PRIVATE_BETA_ONBOARDING.md"
HOSTED_SAAS_ADR = ROOT / "docs" / "adr" / "ADR_HOSTED_SAAS_DECISION.md"
TASKS = ROOT / "docs" / "tasks.md"
CODEX_PROMPT = ROOT / "docs" / "CODEX_PROMPT.md"
AI_DEVELOPMENT_PACK = ROOT / "docs" / "AI_DEVELOPMENT_PACK.md"


def _operator_workflow_text() -> str:
    return OPERATOR_WORKFLOW.read_text(encoding="utf-8")


def _operator_runbook_text() -> str:
    return OPERATOR_RUNBOOK.read_text(encoding="utf-8")


def _backup_recovery_text() -> str:
    return BACKUP_RECOVERY.read_text(encoding="utf-8")


def _production_readiness_text() -> str:
    return PRODUCTION_READINESS_REVIEW.read_text(encoding="utf-8")


def _live_source_roadmap_text() -> str:
    return LIVE_SOURCE_PRODUCTION_ROADMAP.read_text(encoding="utf-8")


def _private_beta_onboarding_text() -> str:
    return PRIVATE_BETA_ONBOARDING.read_text(encoding="utf-8")


def _hosted_saas_adr_text() -> str:
    return HOSTED_SAAS_ADR.read_text(encoding="utf-8")


def _tasks_text() -> str:
    return TASKS.read_text(encoding="utf-8")


def _codex_prompt_text() -> str:
    return CODEX_PROMPT.read_text(encoding="utf-8")


def _ai_development_pack_text() -> str:
    return AI_DEVELOPMENT_PACK.read_text(encoding="utf-8")


def test_operator_workflow_contains_required_sections() -> None:
    content = _operator_workflow_text()

    for section in (
        "## Weekly Inputs",
        "## Weekly Outputs",
        "## Review Time Target",
        "## Decision Taxonomy",
    ):
        assert section in content

    assert "under 15 minutes" in content
    for decision in (
        "`build`",
        "`reject`",
        "`revisit`",
        "`needs_more_evidence`",
        "`already_exists`",
        "`not_my_icp`",
        "`too_hard_to_distribute`",
    ):
        assert decision in content


def test_operator_workflow_lists_failure_conditions() -> None:
    content = _operator_workflow_text()

    assert "## Adoption Failure Conditions" in content
    for condition in (
        "generic ideas",
        "without cited source support",
        "stale evidence",
        "recently rejected ideas",
        "more than 15 minutes",
    ):
        assert condition in content


def test_operator_workflow_defines_privacy_boundaries() -> None:
    content = _operator_workflow_text()

    assert "## Privacy Boundaries" in content
    for boundary in (
        "### Telegram Exports",
        "### Operator Notes",
        "### Credentials",
    ):
        assert boundary in content

    for required_phrase in (
        "raw exports",
        "Raw notes",
        "environment variables",
        "ignored local secrets files",
        "excluded from git",
    ):
        assert required_phrase in content


def test_operator_runbook_contains_required_sections() -> None:
    content = _operator_runbook_text()

    for section in (
        "## Weekly Run Steps",
        "## Review Steps",
        "## Source Failure Handling",
        "## Recovery Steps",
    ):
        assert section in content

    assert "demand-mvp-radar run" in content
    assert "demand-mvp-radar review" in content
    assert "quarantined" in content


def test_operator_runbook_documents_health_checks() -> None:
    content = _operator_runbook_text()

    for phrase in (
        "demand-mvp-radar health --json",
        "stale index warnings",
        "source errors",
        "budget_exceeded",
        "generated artifacts",
        "corpus_version",
        "index_age_days",
        "report_dir.status",
    ):
        assert phrase in content


def test_operator_runbook_documents_privacy_and_backup() -> None:
    content = _operator_runbook_text()

    for phrase in (
        "SQLite database files",
        "raw snapshots",
        "generated reports",
        "operator notes",
        "Telegram exports",
        "Never commit",
        "Back up",
        "environment variables",
    ):
        assert phrase in content


def test_backup_recovery_doc_contains_required_sections() -> None:
    content = _backup_recovery_text()

    for section in (
        "## Backup Targets",
        "## Restore Steps",
        "## Verification Commands",
        "## Failed-Run Recovery Checklist",
    ):
        assert section in content

    for phrase in (
        "SQLite database",
        "retrieval indexes",
        "generated reports",
        "raw snapshots",
        "demand-mvp-radar health --json",
        "PRAGMA integrity_check",
    ):
        assert phrase in content


def test_backup_recovery_doc_lists_git_ignored_private_artifacts() -> None:
    content = _backup_recovery_text()

    for phrase in (
        "Git-Ignored Private Artifacts",
        "SQLite database files",
        "retrieval indexes",
        "raw snapshots",
        "private source exports",
        "Telegram exports",
        "operator notes",
        "generated reports",
        "schedule.env",
        "API keys",
        "credentials",
        "quarantine files",
    ):
        assert phrase in content


def test_backup_recovery_doc_contains_failed_run_checklist() -> None:
    content = _backup_recovery_text()

    for phrase in (
        "run ID",
        "exit code",
        "$DMR_DATA_DIR/logs",
        "runs.status",
        "runs.source_counts",
        "runs.error_counts",
        "budget ceiling",
        "stale index",
        "same run ID",
        "new run ID",
    ):
        assert phrase in content


def test_production_readiness_review_contains_four_run_checklist() -> None:
    content = _production_readiness_text()

    assert "## Four-Run Evidence Checklist" in content
    assert "## Readiness Verdict" in content
    for run_label in ("Run 1", "Run 2", "Run 3", "Run 4"):
        assert run_label in content
    assert "Verdict: NOT READY" in content


def test_production_readiness_review_covers_operational_metrics() -> None:
    content = _production_readiness_text()

    for phrase in (
        "run success",
        "source failures",
        "retrieval metrics",
        "Decision count",
        "Cost",
        "Backup status",
        "Privacy checks",
        "runs.source_counts",
        "runs.error_counts",
        "budget_exceeded",
    ):
        assert phrase in content


def test_production_readiness_review_gates_beta_and_saas() -> None:
    content = _production_readiness_text()

    for phrase in (
        "Private beta: blocked",
        "SaaS or hosted product work: blocked",
        "Private beta remains blocked",
        "SaaS or hosted product work is blocked",
        "repeated personal value",
        "local-first personal decision system",
    ):
        assert phrase in content


def test_live_source_roadmap_defines_self_collecting_target() -> None:
    content = _live_source_roadmap_text()

    for phrase in (
        "self-collecting production version",
        "Exports and manual snapshots remain fallback modes",
        "Production Architecture",
        "Credential Strategy",
        "Connector Contract",
        "Source Waves",
    ):
        assert phrase in content


def test_live_source_roadmap_lists_required_connectors_and_credentials() -> None:
    content = _live_source_roadmap_text()

    for phrase in (
        "GitHub",
        "Hacker News",
        "Stack Exchange",
        "RSS",
        "SERP",
        "Reddit",
        "YouTube",
        "Product Hunt",
        "Discord",
        "Telegram",
        "X/Twitter",
        "GITHUB_TOKEN",
        "YOUTUBE_API_KEY",
        "SERPAPI_API_KEY",
    ):
        assert phrase in content


def test_live_source_roadmap_covers_ai_development_to_production() -> None:
    content = _live_source_roadmap_text()

    for phrase in (
        "AI Development Phases",
        "P1 - Connector SDK",
        "P2 - Public Connector Wave",
        "P4 - Credentialed Connector Wave",
        "P8 - Private Beta Package",
        "P9 - Hosted/SaaS Decision Gate",
        "Production Requirements",
        "Definition of Done for a Connector",
        "Backlog Seeds",
        "Hard Gates",
    ):
        assert phrase in content


def test_live_source_tasks_are_in_authoritative_task_graph() -> None:
    content = _tasks_text()

    for phrase in (
        "## Phase 11 - Live Source Connector Foundation",
        "## Phase 12 - Source Health and Public Corpus Evaluation",
        "## Phase 13 - Credentialed Source Wave",
        "## Phase 14 - Community Source Wave",
        "## Phase 15 - Source Value and Review UX",
        "## Phase 16 - Beta and Hosted Decision",
        "## T39: Live Source Connector Protocol",
        "## T41: collect-sources Command",
        "## T47: Live Public Corpus Retrieval Eval",
        "## T52: Discord Allowlisted Channel Connector",
        "## T57: Hosted/SaaS Decision ADR",
        "docs/LIVE_SOURCE_PRODUCTION_ROADMAP.md#connector-contract",
        "tests/test_live_source_connector.py::test_live_source_config_validates_required_fields",
    ):
        assert phrase in content


def test_codex_prompt_points_to_phase_19_complete_state() -> None:
    content = _codex_prompt_text()

    for phrase in (
        "Version: 2.1",
        "Status: active-production-observation",
        "Active task source: `docs/tasks.md`, Phase 19.",
        "T65 reviewed the first inspectable VPS weekly artifact",
        "docs/audit/FIRST_VPS_WEEKLY_REPORT_REVIEW.md",
        "docs/report_eval.md",
        "demand_mvp_radar/source_trust.py",
        "demand_mvp_radar/telegram_digest.py",
        "docs/handoffs/telegram_channel_intelligence_bridge.md",
        "T70 generated the first true Radar weekly artifact",
        "none - Phase 19 task graph complete.",
        "Telegram intelligence is a bridge to Entropy/Telegram Research work",
    ):
        assert phrase in content


def test_ai_development_pack_extends_loop_through_production_decision() -> None:
    content = _ai_development_pack_text()

    for phrase in (
        "T01-T57 are complete",
        "Current verified baseline after T57 is 184 passing tests",
        "Sequence F - Live Source Connector Foundation",
        "Sequence K - Beta and Hosted Decision",
        "`T39: Live Source Connector Protocol`",
        "`T57: Hosted/SaaS Decision ADR`",
        "Discord allowlisted channels",
        "X/Twitter",
    ):
        assert phrase in content


def test_private_beta_onboarding_contains_required_sections() -> None:
    content = _private_beta_onboarding_text()

    for phrase in (
        "## Setup",
        "## Source Selection",
        "## Credential Environment Variables",
        "## Local Scheduling",
        "## Backup",
        "## Privacy",
        "## Support Boundaries",
        "GITHUB_TOKEN",
        "SERPAPI_API_KEY",
        "YOUTUBE_API_KEY",
        "PRODUCT_HUNT_TOKEN",
        "DISCORD_BOT_TOKEN",
    ):
        assert phrase in content


def test_private_beta_onboarding_keeps_readiness_gate() -> None:
    content = _private_beta_onboarding_text()

    for phrase in (
        "four-run production readiness review",
        "at least three useful personal decisions",
        "Private beta remains blocked",
        "docs/audit/PRODUCTION_READINESS_REVIEW.md",
        "Source value reports",
    ):
        assert phrase in content


def test_private_beta_onboarding_defines_private_data_boundary() -> None:
    content = _private_beta_onboarding_text()

    for phrase in (
        "Never send maintainers",
        "raw exports",
        "SQLite databases",
        "generated private reports",
        "raw Discord or Telegram messages",
        "private notes",
        "API keys",
        "bot tokens",
        "OAuth refresh tokens",
        "channel IDs",
        "guild IDs",
        "unredacted source locators",
    ):
        assert phrase in content


def test_hosted_saas_adr_compares_required_options() -> None:
    content = _hosted_saas_adr_text()

    for phrase in (
        "Option A - Local-Only",
        "Option B - Team Self-Hosted",
        "Option C - Hosted SaaS",
        "Remain local-first",
        "Hosted SaaS work is blocked by default",
    ):
        assert phrase in content


def test_hosted_saas_adr_requires_beta_evidence() -> None:
    content = _hosted_saas_adr_text()

    for phrase in (
        "Personal readiness",
        "Private beta usage",
        "Source value",
        "Support burden",
        "Credential risk",
        "Willingness-to-pay",
        "Hosted work cannot start",
    ):
        assert phrase in content


def test_hosted_saas_adr_lists_hosted_prerequisites() -> None:
    content = _hosted_saas_adr_text()

    for phrase in (
        "authentication",
        "tenant isolation",
        "encrypted secrets",
        "billing",
        "audit logs",
        "abuse controls",
        "data deletion",
    ):
        assert phrase in content
