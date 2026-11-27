# ADR 2026-11-27 — Declarative method applicability at the shared demand boundary

Status: CANDIDATE on SMS Draft PR #56. This is a semantic admission contract, not proof that a human or model understood the source.

## User outcome and CAOS root-cause loop
The user requires content-specific professional selection and repeatedly rejects forcing current-affairs news narration/satire onto gameplay, pet footage, ordinary entertainment, and creator captions. Audit F04 found a provable boundary leak: exact method profiles carried human-readable applies_to/avoid_when but common intake and durable task admission checked only deliverable type and identity mode.

Hypotheses: replacing the creative prompt cannot enforce tool/task admission; a special video controller would duplicate authority; a universal genre classifier would invent ungrounded context and impose needless work. The supported root cause is missing executable method-specific applicability at the *existing* shared demand route. Selected: optional declarative preconditions within the existing demand operation contract, with both direct and durable paths using the same `demand_applies`. No new registry, ledger, scheduler, agent or mandatory content classifier.

## Rule and its limits
The narrowly scoped `news_satire_packaging` route now requires:
- `constraints.source_content_class = NEWS_CURRENT_AFFAIRS`;
- `constraints.editorial_treatment = SATIRE`;
- at least one explicit source reference.

Missing declarations or contradictory class intent remove this route from *candidate methods* and reject explicit incorrect selection in durable task admission. This does not block ordinary `short_form_copy`, general gameplay and pet publishing, or non-news material. A declared genre and source reference are not independent authentication, fact-checking, present-day news relevance, source rights, semantic comprehension, or owner acceptance. Real semantic verification remains a separate CAOS and professional review requirement. If the user explicitly changes the task, revise the owner brief and invalidation through the existing event history.

## Architecture
An optional typed `semantic_preconditions` field is added to the current per-demand operation registry, validated fail-closed by `capability_lookup`, interpreted by one pure shared predicate; no hardcoded news-only branch in the common orchestration system. This is modular-monolith Open/Closed design: adding a new reviewed demand method can declare bounded eligibility in the registry without authoring a second controller. Arbitrary runtime Python code and plugin auto-loading remain forbidden.

## Counterexamples and acceptance
Negative replays: unclassified short text, gameplay, pets, fiction, unsigned treatment, absent source, and direct/durable route-selection bypass. Positive replay: the declared, sourced news satire is only *eligible*, and still does not claim factual verification or executor availability. Malformed/partial admission contracts must be rejected. Full exact-head CI/system audit/topology/independent CLI smoke remains mandatory before merge. Keep evidence history. Rollback this commit if previously legitimate news satire requests cannot be represented by the typed declaration without artificial tasks.
