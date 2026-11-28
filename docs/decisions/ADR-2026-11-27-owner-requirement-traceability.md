# ADR — Explicit owner requirement trace across actual deliverable variants (2026-11-27)

Status: Candidate on SMS Draft PR #56.

## CAOS root cause
The owner's full goal includes global, deliverable-scoped, and variant-specific constraints (e.g. no news narration for a pet clip; no duplication between title, description and cover; independent 3:4 and 16:9 results). A successful artifact hash, production task, file shape, or reviewer receipt is not a proof of each original source clause. The existing brief/demand contract already preserves source references, clauses and revisions; creating a second approval database or controller would introduce competing authority.

Chosen: pure requirement-trace projection using the *current brief* and its existing typed deliverables and demand clauses. It binds every declared variant to the exact candidate IDs and SHA observations, all applicable global/local clauses, quality criteria already owned by `domain.assurance.CRITERIA`, explicit acceptance/prohibitions and remaining unresolved questions. A scope mismatch or missing variant fails closed. Its source-of-truth SHA256 changes on every meaningful brief edit, invalidating cached external assumptions.

## Limits and independent acceptance
The source declaration is not authenticated solely by being in JSON. A trace does not verify footage understanding, writing style, original source fidelity, aesthetics, user consent, independent review, IPOS rights, audience effect or publishing authority. Every relevant criterion stays PENDING; no human/owner PASS is invented. Future authorized execution adapters and professional reviewers must produce separate inspectable proof tied to these clauses and exact artifact versions before whole-demand completion can be asserted.

The trace is exposed only through the existing explicit, read-only `inspect-outcome` facade. No extra scheduler, project ledger, permanent stage or default task plan. Full exact-head integration tests, topology and historical scope isolation must pass before branch integration.
