# ADR — Bind operation ownership to actual implementation sources

- Date: 2026-11-28
- Status: Accepted for PR #56 candidate; exact-head CI and independent review required before merge.
- Scope: Social Media Studio only. CAOS source, Skills and PRs remain read-only and unchanged.

## Context

The current topology audit verifies that every Python source file has one subsystem owner, that every registered domain adapter and production operation appears exactly once in the subsystem catalog, and that the retired controller is not re-entered.
It did not verify the relationship between a registered operation's semantic owner and the code that actually implements it. This left two distinct risks:

1. A domain adapter can be implemented in one subsystem's module while its operation is assigned to another subsystem without an explicit bridge contract.
2. All six production operations are registered through the central `production.handlers` dispatcher, but the registry did not identify the exact domain implementation delegated to by each wrapper.

A green topology audit therefore proved source-file ownership and operation-name coverage, not complete operation-to-implementation ownership.

## Source evidence

At the pre-change PR #56 head `2341f700f2a36772a48a826ffb8ed8bf707510ac`:
- `subsystems.py` compared adapter and production-operation name sets, but did not join `DomainAdapterSpec.handler_ref` to the owning subsystem.
- `test_subsystem_topology.py` checked module ownership, operation counts and duplicate ownership, but not handler-to-operation ownership.
- Four adapters cross a subsystem boundary:
  - `episode_intent_validate`: business implementation → motion operation owner.
  - `shot_contract_materialize` and `shot_contract_validate`: editorial implementation → motion operation owner.
  - `shot_route`: motion implementation → provider-routing operation owner.
- These are plausible, source-supported bridges. Moving them based only on filenames would risk changing semantic ownership. The defect is the missing explicit bridge contract, not proof that the current assignments are wrong.
- The six production wrappers are centralized in `production.handlers`; their delegated implementation modules are owned by the corresponding domain subsystems.

## Decision

Reuse the existing subsystem catalog, domain-adapter registry and production-executor registry. Do not add a second router, subsystem registry, project database or controller.

1. A domain adapter's registered handler module is its implementation owner. If that differs from its semantic operation owner in the subsystem catalog, require one exact `cross_subsystem_adapter_bindings` record with both owners, boundary type and rationale. Missing, stale, duplicate or mismatched bridge records fail the topology audit.
2. A production executor records both its central dispatcher reference and its exact `module:symbol` implementation reference. The dispatcher must remain owned by `execution_and_owner_scope`; the implementation module must be owned by the subsystem that owns the operation. The symbol itself must resolve against the tracked source AST, including class methods.
3. The topology report exposes these bindings so tests and future audits can inspect them.
4. The new metadata does not authorize an effect, provider call, candidate promotion, release or publication. Existing effect gates remain authoritative.

## Alternatives considered

- Move all cross-boundary handlers into the semantic owner module: rejected for now because the source shows legitimate EditorialPlan→ShotContract, Business Program→Episode and Motion→Provider boundaries; moving code before establishing the contract would conflate semantic ownership with file placement.
- Reassign operation owners to match handler module names: rejected because this would make file location the authority and could misclassify the actual domain responsibility.
- Add another operation registry or subsystem controller: rejected because the existing catalog and registries already contain the necessary identities; the missing element is a verifiable join.
- Keep the current audit unchanged: rejected because operation ownership can drift while the topology audit remains green.

## Validation and limits

The candidate change adds explicit bridge records for the four observed cross-subsystem adapters, exact implementation references for all six production operations, static module-and-symbol resolution, owner-binding checks, and adversarial tests for missing bridges, unresolved symbols and incorrect production ownership.
CI success proves repository regression only. It does not prove creative quality, provider account permissions, native SMS Skill selection, independent review, publication or commercial outcomes. The trusted high-assurance reviewer registry remains empty. PR #56 remains Draft and unmerged until the separate acceptance gates are satisfied.

## Rollback

Revert the atomic operation-ownership commit on the PR branch. No `main` change, user project data, production artifact, CAOS source or IPOS canon is modified.
