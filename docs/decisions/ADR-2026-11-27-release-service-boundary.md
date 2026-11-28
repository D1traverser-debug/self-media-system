# ADR 2026-11-27 — Extract artifact release application service by abstraction

Status: CANDIDATE on the SMS integration Draft PR #56.

## CAOS problem investigation
The current single `StudioEngine` is approximately 3,074 source lines and its `release_check` is 753 lines/53.6KB. It contains transactional artifact review, exact digest and source lineage, linked rights evidence, trusted review execution, media technical QA, and accepted/blocked audit events. A single monolithic class forces every release change and new domain tool to modify a mixed-control file, creating cross-domain regression risk.

Alternatives examined:
- Rewrite the engine / add a second runtime: rejected, duplicates project state and risks lost atomic leasing and audit history.
- Move release logic into local media provider or CLI: rejected, permits bypass from other entrypoints.
- Create a new approval database or status: rejected, secondary authority and stale outcomes.
- Extract the *existing* transaction as an application service, keeping engine's single SQLite connection and ledger: selected.

## Decisions
- `StudioEngine.release_check` keeps its exact signature and delegates to `application.release_service.ReleaseAssuranceService`.
- The service uses the existing engine persistence and event APIs. `BEGIN IMMEDIATE`, provenance, reviewer receipts, rights checks, video QA and final ACCEPTED/BLOCKED event are moved intact.
- Domain release invariants remain in independent pure `domain.release_policy`. No new registry, SQLite table, model provider, account publish action, permission claim or other scheduler.
- The release service is source-owned by the current `quality_and_assurance` bounded context in the existing topology catalog.
- Public acceptance remains an artifact-specific technical/review boundary, **not** creative quality, owner approval of all deliverables, global production readiness or publication authority.

## Regression and rollback
The current 550+ live tests and CI system audit, topology, installed standalone CLI, media/audio pipelines, event-transaction behavior, and historical isolation must continue passing on this exact new head. If behavior differs, re-open the abstraction seam and restore the original atomic transaction, preserving all source evidence. Review all changes through Draft PR #56; no mainline merge or user project migration. Next architectural work should address per-variant independent owner outcome review, provider contracts, and F08 trust boundaries rather than reconstruct another orchestrator.

Method references: Martin Fowler, Branch by Abstraction; Cockburn, Hexagonal Architecture; Fowler, Bounded Context.
