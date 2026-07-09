# Demand-to-MVP Radar

Demand-to-MVP Radar - локальный инструмент для отбора маленьких AI/MVP-идей по реальным сигналам спроса.

Статус: active live product. Текущий фокус - качество первого VPS weekly report, evidence-backed рекомендации и source trust. Roadmap: `docs/PROJECT_PLAN.md`.

Reference integration: `docs/entropy_core_gensyn_integration.md`.

Проект должен помочь соло-разработчику быстрее понять, какие идеи стоит строить, какие лучше отклонить, а какие нужно отложить до появления более сильных доказательств.

## Цель

Собрать разрозненные сигналы спроса из текстовых источников, привести их к единому виду, найти похожие паттерны, оценить возможности по понятным правилам и выдать еженедельный короткий список one-function MVP-кандидатов с источниками, цитатами и рекомендацией:

- build
- reject
- revisit

Система остается advisory-only: она не принимает коммерческие решения, не создает продукты, не публикует отчеты наружу и не запускает outreach без человека.

## Главная гипотеза

Если регулярно собирать и нормализовать рыночные сигналы из Telegram-экспортов, поисковых снимков, store listings, Reddit/X-сниппетов, конкурентных страниц и личных заметок, то можно быстрее находить decision-grade MVP-возможности, чем при ручном чтении и рассуждении по памяти.

## Что хотим проверить

1. Можно ли за один weekly run получить top 5 возможностей, которые реально опираются на источники, а не выглядят как LLM-бред или generic brainstorming.
2. Может ли оператор принять build / reject / revisit решение по каждому кандидату меньше чем за 15 минут.
3. Появляются ли хотя бы 3 decision-grade возможности в неделю при доступных источниках.
4. Достаточно ли text-only RAG для доказуемых кратких MVP-briefs без мультимодального поиска.
5. Помогает ли deterministic scoring лучше сравнивать идеи между неделями, чем ручные заметки.
6. Работает ли `insufficient_evidence` как честный стоп-сигнал, когда источников мало, они устарели или не подтверждают спрос.
7. Можно ли сохранить decision memory: не возвращаться к слабым уже отклоненным идеям и вовремя пересматривать promising идеи.

## Что будет на выходе MVP

MVP должен запускаться как CLI-first Python batch workflow и формировать Markdown-отчет с ранжированными возможностями.

Каждый opportunity brief должен содержать:

- короткое описание боли и аудитории
- текущий workaround
- evidence snippets и ссылки на источники
- competitor / alternative notes
- one-function MVP scope
- acquisition angle
- deterministic score components
- риски и confidence note
- рекомендацию build / reject / revisit

## Что не проверяем в v1

- гарантированный revenue potential
- TAM и финансовое прогнозирование
- полностью автоматический выбор продукта
- high-scale scraping
- браузерную автоматизацию
- публичную публикацию отчетов
- автоматическое создание репозиториев или продуктовых ассетов
- автономный outreach

## Архитектурная идея

v1 - локальный batch pipeline:

```text
source ingest -> normalize -> store -> retrieve -> cluster -> score -> synthesize -> report
```

Детерминированный код отвечает за ingestion, storage, dedupe, retrieval gates, scoring, thresholds и report assembly.

LLM используется только ограниченно:

- извлечь смысловые поля из messy text
- синтезировать brief по уже собранным evidence packets

Все claims в brief должны быть привязаны к источникам. Если evidence недостаточно, система должна возвращать `insufficient_evidence`, а не додумывать рекомендацию.

## Текущий статус

Phase 1-19 завершены и прошли review без stop-ship findings. Planned task list complete; private beta and hosted/SaaS remain blocked until four real or properly backfilled solo evidence runs prove repeated personal value, useful human decisions, source value, backup verification, and support burden. Cross-repo KIR hardening for Telegram Research Agent seeds is implemented: Knowledge Thread provenance is preserved on import, and Telegram-seeded build-like recommendations require KIR source atoms, source URLs, and decision-grade external corroboration.

Текущая focused verification для weekly Radar/KIR surfaces:

- `.venv/bin/python -m pytest tests/test_mvp_of_week.py tests/test_mvp_report_quality.py`
- `.venv/bin/python -m pytest tests/test_mvp_of_week.py tests/test_mvp_report_quality.py tests/test_telegram_research_bridge.py`

Реализовано:

- Python package skeleton, editable install metadata и CLI entrypoint `demand-mvp-radar`
- `health --json` с database/report/corpus/index-age статусом
- Pydantic configuration defaults and `DMR_` env overrides
- SQLite schema and repositories for evidence, decisions, tool audit events, retrieval chunks, and reports metadata paths
- Tool-Use v1 schema catalog, executor validation, permission boundary, and audit persistence
- Telegram export adapter with quarantine handling
- bounded URL snapshot, SERP snapshot, and store metadata fixture readers
- text-only retrieval ingestion/query, `insufficient_evidence`, and RAG eval baselines
- deterministic clustering, scoring, recommendation thresholds, and decision-memory suppression
- fake-provider LLM extraction validation
- Markdown report rendering and atomic report writes
- fixture-backed weekly pipeline command with LLM budget guard
- final RAG and Tool-Use evaluation rows
- operator workflow contract and source catalog configuration
- sanitized `telegram-research-agent` bridge with preserved Knowledge Thread provenance fields (`source_kind`, `source_urls`, `knowledge_thread_slug`, `knowledge_thread_title`, `knowledge_thread_status`, `knowledge_atom_types`, `source_atom_ids`)
- redacted operator notes importer with note-only build guard
- local GitHub repository snapshot importer and `read_github_repo_snapshot` tool audit schema
- `import-sources` command for owned-source imports without weekly report generation
- source trust/freshness scoring controls and source-type evidence caps
- live-like retrieval evaluation fixtures with freshness and source-diversity metrics
- evidence delta reports for new, duplicate, stale, quarantined, skipped, and changed evidence
- decision-grade opportunity dossier schemas and Markdown/HTML renderers
- missing-evidence analysis and `review` command decision recording
- MVP experiment pack model, Markdown renderer, and deterministic outcome feedback
- operator runbook, local systemd scheduled-run templates, and scheduled-run health reporting
- backup/recovery guide and four-run production readiness review gate
- fixture-first public, credentialed, and community live source connectors with source health output
- source value reporting and local-only review cockpit helpers
- private beta onboarding guide and hosted/SaaS decision ADR
- solo open-source research protocol and four-run evidence ledger
- portfolio-fit taxonomy, public-safe showcase opportunity report, and Lead Response SLA handoff pack
- solo evidence readiness review that keeps private beta and hosted/SaaS blocked
- first VPS weekly artifact review, report-quality eval metrics, deterministic source-trust/repeated-signal records, and Telegram channel intelligence bridge policy
- deterministic Telegram digest-to-Radar seed adapter and first true local `mvp-of-week` report with no-count ledger status
- GitHub Actions workflow for install, ruff check, format check, and pytest

Пример локального запуска:

```bash
demand-mvp-radar run --fixture tests/fixtures/weekly_run
demand-mvp-radar import-sources --fixture tests/fixtures/source_mix
demand-mvp-radar mvp-of-week \
  --telegram-export ../telegram-research-agent/data/output/opportunity_seeds/2026-W22.json \
  --source-config config/mvp_weekly_sources.json
demand-mvp-radar digest-to-seeds \
  --digest ../telegram-research-agent/data/output/digests/2026-W14.json \
  --output data/phase19/2026-W14-radar-seeds.json
demand-mvp-radar lead-sla-report --input tests/fixtures/lead_sla/open_proxy_leads.csv --output reports/private/lead_sla_open_proxy_report.md --sla-minutes 5 --hash-lead-id
demand-mvp-radar health --json
```

`mvp-of-week` treats Telegram exports as seed evidence, then optionally runs
the configured source collection before synthesis. The weekly artifact is a
Candidate Dossier with canonical `Status`, `Decision`, `Confidence`, and
`Next action` fields, plus matching JSON `dossier_status` values for the
overall result and selected candidate. It also exposes a machine-readable
selected-candidate `source_mix` / `selected_source_mix` object with readiness,
selected external evidence, run-level external evidence, missing credentials,
Reddit API status, and GitHub evidence role. It is a separate opportunity
artifact, not a technical upgrade brief for existing repos.

The MVP recommendation is gated by source mix, KIR provenance, and operator fit:

- Telegram-only ideas cannot become `focused_experiment`; they stay
  `revisit_with_evidence_gap` / `needs_more_evidence` until public external
  evidence confirms the same pain.
- Telegram Research Agent Knowledge Thread seeds must preserve KIR provenance
  and pass the KIR gate before any `build` or `focused_experiment`
  recommendation is allowed.
- The selected-candidate source mix exposes `kir_source_kind`,
  `kir_thread_slug`, `kir_thread_status`, `kir_source_atom_count`,
  `kir_source_url_count`, `kir_gate_status`, and `kir_gate_reasons` when KIR
  gating is relevant.
- Runtime LLM Markdown cannot override deterministic gates. If synthesis claims
  a build/focused experiment while source mix fails, the rendered Decision Gate,
  Build-Worthy section, and JSON result are rewritten to the gated
  recommendation.
- Recommendation strings are mapped to reader-facing dossier status values:
  `build`, `focused_experiment`, `investigate`, or `reject`. Existing-project
  context is always rendered as `investigate` with explicit copy telling the
  operator to apply the signal to an existing repo/backlog instead of treating
  it as a new standalone MVP.
- Strong recommendations need at least two non-Telegram evidence items from at
  least two independent external source types.
- Weekly reports expose Decision Gate, Source Trust And Repeated Signals,
  Build-Worthy Recommendations, and Interesting Signals sections so repeated
  source noise is visible before build-like recommendations.
- Candidate Dossiers expose a compact Source Mix card near the top. The card
  labels the run as `telegram_only`, `externally_corroborated`, or
  `credential_limited`, and separates live Reddit API evidence from
  SERP-indexed Reddit pages.
- `tests/test_mvp_report_quality.py` locks the Candidate Dossier contract:
  canonical top block, source-mix card, missing evidence, kill criteria,
  existing-project context, and no contradictory build-ready claims when source
  gates fail.
- `config/operator_fit_profile.md` keeps the weekly idea close to the operator's
  Python/LLM workflow, evaluation, guardrail, knowledge-memory, research, and
  rollout strengths.
- `config/mvp_weekly_sources.json` is the production weekly source mix:
  RSS/HN, GitHub public search, Stack Exchange, SERP, YouTube, Product Hunt,
  and Reddit. Missing credentials are reported as `source_errors`; enabled
  weekly sources should not be silently skipped.
- `config/live_sources.env.example` lists the optional/required live-source
  secrets for the VPS env file.
- `docs/MVP_WEEKLY_LIVE_SOURCES.md` is the operator-facing contract for the
  full weekly source bundle, required credentials, and source-mix gates.
- `docs/RADAR_VALIDATION_EVIDENCE.md` is the RVE contract for
  `validation_queries`, `matched_external_evidence`,
  `decision_context.external_research_context`,
  `missing_evidence_by_category`, and `validation_adapter_status`. Context-only
  market records and unmatched external results never satisfy gates.

`mvp-of-week` now renders a planning-only `Validation Query Pack` and a matched
`Matched External Evidence` section for the selected candidate. Query planning
and matching are deterministic. The Search/SERP, Reddit/forum, and
competitor/workaround crawler validation boundaries support live, `cache_only`,
and `dry_run` modes; missing live credentials surface as `credential_limited`,
rate limits surface as `rate_limited`, and neither state fails the weekly run.
Candidate source gates count only matched decision-grade external evidence;
unmatched, adjacent-pain, or irrelevant/hype external results remain visible as
`decision_context.external_research_context` or negative matched evidence.

Runtime LLM synthesis is opt-in through env:

- `DMR_LLM_PROVIDER=anthropic`
- `DMR_LLM_API_KEY` or inherited `LLM_API_KEY`
- `DMR_LLM_MODEL_MVP_WEEKLY=claude-opus-4-7`

Without an enabled provider the command writes a deterministic fallback report.

## Режим разработки

Разработка идет nonstop по оркестраторному loop: задача, review, фиксы при необходимости, state update, следующая задача.

Граница фазы не является паузой. После завершения задач фазы нужно пройти Strategy review, Deep review, Archive, Doc update и Phase report, затем сразу вернуться в Step 0 и продолжить следующую фазу.

Остановка допустима только при явном blocker, нерешенном P0, rate/provider limit, полном завершении проекта или human approval boundary.

## Основные документы

- `docs/spec.md` - продуктовая спецификация
- `docs/ARCHITECTURE.md` - архитектура и границы v1
- `docs/tasks.md` - implementation task graph
- `docs/CODEX_PROMPT.md` - текущее состояние и правила выполнения
- `docs/LIVE_SOURCE_PRODUCTION_ROADMAP.md` - roadmap до версии, которая сама собирает данные из live-источников
- `docs/MVP_WEEKLY_LIVE_SOURCES.md` - weekly MVP live-source contract, credentials, and gates
- `docs/SOURCE_CATALOG.md` - каталог источников, trust tiers и access strategy
- `docs/DEMAND_SOURCE_MAP.md` - карта мест, где искать боль и спрос внутри источников
- `docs/retrieval_eval.md` - принципы оценки RAG
- `docs/tool_eval.md` - принципы оценки tool-use
