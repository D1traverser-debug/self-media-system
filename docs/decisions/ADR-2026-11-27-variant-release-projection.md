# ADR 2026-11-27 — Whole-demand variant release projection

Status: CANDIDATE on Draft PR #56. A necessary but not sufficient owner-outcome boundary.

## Root cause and counterexamples
SMS can accept the individual digest-verified artifact while the user requested a caption, cover variants and platform package. No number of artifact PASS reviews means every declared deliverable is present. Existing status already projects candidates without a second ledger, but had no visible distinction between one released artifact and all variants being technically admitted.

Selected design: **a pure derived variant projection** from the existing current task/output/sha acceptance records; no second acceptance DB, approval flag, workflow engine or forced media pipeline. Bounded contexts: artifact release is a QA responsibility, owner outcome is a separate independent judgment.

Counterexamples:
- 3:4 cover accepted but 16:9 still CURRENT: whole demand incomplete.
- Two cover variants accepted but caption missing: whole demand incomplete.
- All declared artifacts ACCEPTED: this shows only per-artifact release coverage, not quality, emotional effectiveness, final owner approval or posting permission.
- No declared variants: cannot vacuously pass.
- Duplicate variant identity: fail closed.

## Interfaces and re-entry
The existing `StudioEngine._deliverable_progress_in_tx` supplies current normalized variants, verified exact file bytes and status, then calls pure `domain.outcome_assurance.variant_release_coverage`. `status`, `resume`, worker continuation and work cycle use the *same* derived projection and guidance. Candidacy, artifact-level release coverage, independent owner-outcome review and platform publication remain separate.

This operation never writes an ACCEPTED event, unlocks provider operations, asserts a human review happened or overrides a user request. No different criteria are imposed on short copy vs images vs film; each typed deliverable and its variants are required. Untyped historical projects retain explicit non-evaluation.

## Acceptance
Full exact-head CI, previous typed durable admission, cross-content, topology and standalone smoke must pass. Artifact progress projection must remain consistent across resume, status and worker cycle. F03 remains *partially addressed* until actual source-qualified owner acceptance evidence exists; this change does not fabricate it.
