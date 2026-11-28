# ADR — SMS release safety boundary and controlled modularity (2026-11-27)

Status: CANDIDATE on Draft PR #56. Never read this ADR as live production / owner-outcome acceptance.

## CAOS intent and root causes
User outcome is the complete Social Media Studio: contextual creative work, media production, identity, audience growth, business work and owner-selected deliverables. User decisions, prohibitions, aspect variants, permissions and requested scope outrank resource catalogues. The 2026-11-27 complete-source audit isolated F01/F02/F03: an artifact release path allowed configuration and CLI parameters to disable rights/technical QA, and an artifact-only verdict was too easy to misread as whole-demand or publication acceptance.

Competing hypotheses:
- "Delete legacy and rewrite everything": contradicted by the functioning one-ledger scheduler, typed routes, SHA-bound artifacts, audio stream QA and 546 baseline tests. Rejected.
- "Add LangGraph/Temporal/agents as a second controller": introduces duplicated state and does not provide a creative-quality oracle. Rejected.
- "Only write another workflow instruction": cannot protect the actual `release_check` call path. Rejected.
- "Protect one business rule behind a pure typed port while retaining the existing engine": selected conditionally, with negative tests and exact-head CI.

## Architecture selected
**Modular monolith + bounded contexts + ports/adapters + explicitly registered internal executors + incremental branch-by-abstraction.**

- Owner-demand authority: the current brief and append-only revisions; CAOS remains a separate read-only cognition governor, not another local scheduler.
- Application facade: the single `StudioEngine`; existing SQLite transaction/event/lease/graph guarantees continue.
- Domain: pure `domain/release_policy.py` returns immutable `ReleaseGuards` from actual artifact type and policy, independent of provider/CLI/tool.
- Adapters: the existing 17 domain adapters and 6 local production operations remain explicit, reviewed and dispatch-gated. A capability catalogue is *discovery metadata*, not a grant to load untrusted code or to publish. New providers require explicit contracts, permissions, availability, cost controls and tests; no auto-discovery of arbitrary Python entry points.
- Product oracle: single-artifact release remains artifact scoped. It is explicitly **not** entire owner-demand acceptance, creative quality verification or external publication authority. Real overall and per-variant review remains an OPEN architectural task.

Alternatives reviewed:
1. Big-bang rewrite / microservices — high migration and multiple-authority risk with no observed scale need.
2. An unconstrained plugin manager / auto-import of packages — not justified by current six trusted local operations and creates arbitrary code execution and permission risks.
3. Hard-coded permanent video pipeline — conflicts with independent text, images, business and direct-session tasks.
4. Retain the current modular monolith but strengthen boundary invariants — best fit to current evidence.

Sources studied:
- Alistair Cockburn, Hexagonal Architecture (2005): https://alistair.cockburn.us/hexagonal-architecture
- Martin Fowler, Bounded Context: https://martinfowler.com/bliki/BoundedContext.html
- Martin Fowler, Branch by Abstraction: https://martinfowler.com/bliki/BranchByAbstraction.html
- Python Packaging User Guide, Creating and Discovering Plugins: https://packaging.python.org/en/latest/guides/creating-and-discovering-plugins/
- pluggy stable docs: https://pluggy.readthedocs.io/en/stable/

## This structural slice
- Enforce rights state at every artifact `release_check` regardless of API parameter or old brief relaxation.
- Require media lineage rights evidence when any media is in a release lineage; cannot disable by policy.
- Require exact video technical QA whenever the actual artifact is video; explicit policy `false` is a failing downgrade, not an exemption.
- Reject ambiguous boolean policy types.
- Remove `--allow-unknown-rights` from active CLI.
- Return `acceptance_scope=INDIVIDUAL_ARTIFACT_ONLY`, `whole_demand_accepted=false`, `external_publication_authorized=false` to prevent status conflation.
- Record domain module ownership in the existing subsystem topology, without another control plane.

## Not changed and anti-deletion rules
Do not delete historical counterexamples, project source, rights evidence, tests or actively imported `legacy` domain algorithms based on folder names. Delete obsolete executable bypasses and duplicate authority only after dependency proof. No script is authorized to erase user assets or retrospectively revise signed receipts. No release implies an external post, owner approval, creative acceptance or completed growth/commercial outcome.

## Falsifiers and gates
- A released video without exact technical QA, a released media asset without rights evidence or a caller bypass of unknown rights falsifies this design.
- All previous positive doc/image/video fixtures and the full CI/system/topology/standalone CLI suite must remain green; failing tests must be investigated, never suppressed.
- Need further separate acceptance for F03–F17, current provider integrations, CAOS native activation and real multi-business owner outcomes.
- Rollback: revert this self-contained commit on the Draft integration branch. Do not mutate main, the user's runtime workspace or historical evidence.
