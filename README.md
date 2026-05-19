# Demand-to-MVP Radar

Demand-to-MVP Radar - локальный инструмент для отбора маленьких AI/MVP-идей по реальным сигналам спроса.

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

Проект находится в Phase 1: foundation. Код приложения еще не реализован. Подготовлены governance docs, task graph, RAG/reference guidance и Codex-only workflow.

Первый implementation task: `T01: Project Skeleton`.

## Основные документы

- `docs/spec.md` - продуктовая спецификация
- `docs/ARCHITECTURE.md` - архитектура и границы v1
- `docs/tasks.md` - implementation task graph
- `docs/CODEX_PROMPT.md` - текущее состояние и правила выполнения
- `docs/retrieval_eval.md` - принципы оценки RAG
- `docs/tool_eval.md` - принципы оценки tool-use
