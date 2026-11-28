# ADR — Scoped implicit decision continuity across dependent stages

Date: 2026-11-27  
Status: CANDIDATE_IMPLEMENTED_IN_CONVERSATIONAL_CONTRACT__FRESH_CHAT_VALIDATION_OPEN  
Scope: Social Media Studio direct-session continuity. No new database, scheduler, project state, permission or publication authority.

## Problem

Historical self-media work shows that owners do not always say “approved” before moving to the next dependent task. A copy-to-cover transition can establish that some upstream copy or creative direction is now the working baseline. A binary explicit-selected / not-selected model loses that state and causes the assistant to reopen already-settled decisions or ask the owner to repeat them.

However, moving to a next task does not mean every upstream field, final artifact or publication outcome has been approved.

## Alternatives

1. Require explicit approval tokens at every transition — rejected: adds unnecessary owner burden and discards ordinary conversational decision signals.
2. Treat any downstream request as blanket approval of the whole prior package — rejected: over-infers, can erase unresolved requirements and confuses working selection with final acceptance.
3. Add a global approval database or extend the StudioEngine project decision ledger to transient chats — rejected: duplicates authority; the existing engine's immutable decisions are bound to durable project/task/input snapshots and should remain so.
4. **Selected:** infer a scoped conversational state, `IMPLICITLY_LOCKED_FOR_DEPENDENT_STAGE`, for only the upstream decision atoms required by the actual next task. Store material private evidence in the existing owner casebook; keep the public Skill contract generic.

## Rule

- Identify the exact downstream task and real dependency.
- Preserve the exact upstream item/version and source message.
- Lock only the smallest required decision atoms.
- Record confidence and leave unrelated fields open.
- Do not infer owner acceptance, final artifact acceptance, rights clearance, publication or performance.
- A later correction supersedes only affected atoms and dependent artifacts.
- If the next task is exploratory, multiple candidates remain, or dependency is weak, retain `CANDIDATE` / `UNRESOLVED` and use a reversible working baseline where possible.

## Existing architecture boundary

- `STUDIO_ENTRY.md` and the conversational SMS Skill carry this rule.
- The private Library stores owner-specific decision evidence and episodes.
- `StudioEngine.record_decision` remains project-scoped and immutable; it is not a global conversational approval oracle.
- Existing typed deliverable contracts and independent outcome assurance remain separate.
- No runtime schema or new module is introduced.

## Falsifiers and acceptance

The rule is wrong or too broad if it locks an upstream atom that the next task did not depend on, treats an exploratory request as approval, loses a later correction, or reports a generated asset as accepted merely because the owner advanced. A fresh independent task must demonstrate correct inheritance, no duplicate copy, preserved open states and lower preventable owner rework. Native Skill selection and actual fresh-chat behavior remain NOT_TESTED until first-party traces/outcomes exist.
