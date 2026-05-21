# ADR: Hosted/SaaS Decision

Date: 2026-05-21
Status: Proposed gate, default decision is local-first

## Context

Demand-to-MVP Radar is currently a local-first personal decision system. The product now supports source collection, health, source value reporting, local review, and private beta onboarding. Hosted SaaS work would add major operational, privacy, support, and compliance obligations.

## Options

### Option A - Local-Only

Keep the product as a single-operator local tool. Users own their SQLite database, source configs, credentials, reports, backups, and schedules.

### Option B - Team Self-Hosted

Package the local workflow for a small team to run on its own infrastructure. The team owns deployment, credentials, backups, access control, and source approvals.

### Option C - Hosted SaaS

Operate a multi-tenant hosted service with managed accounts, hosted source collection, stored customer credentials, shared infrastructure, billing, and support.

## Decision

Remain local-first until the evidence gates below are satisfied. Team self-hosted may be reconsidered before hosted SaaS if private beta teams repeatedly ask for shared operation but can still own infrastructure and credentials. Hosted SaaS work is blocked by default.

## Evidence Required Before Hosted Work

Hosted work cannot start until there is documented evidence for all of the following:

- Personal readiness: the four-run readiness review is green and local operation produces repeated useful decisions.
- Private beta usage: beta users complete onboarding and produce repeated useful decisions without maintainer-held data.
- Source value: source value reports show which sources improve decisions and which sources should be disabled or demoted.
- Support burden: onboarding, scheduling, source failures, restore, and review support are manageable.
- Credential risk: credential handling, rotation, redaction, and source approval risks are understood.
- Willingness-to-pay: beta users show explicit willingness to pay for hosted operation rather than local-only use.

## Hosted-Only Prerequisites

Hosted SaaS requires these capabilities before implementation begins:

- authentication
- tenant isolation
- encrypted secrets
- billing
- audit logs
- abuse controls
- data deletion

## Consequences

Local-only keeps privacy and implementation scope manageable. Team self-hosted may reduce support centralization but still needs deployment docs. Hosted SaaS can only be considered after the evidence gates are met and the hosted-only prerequisites are planned as first-class product work.
