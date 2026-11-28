# ADR — CAOS parent resolution and private method portfolio discovery

Date: 2026-11-28  
Status: `IMPLEMENTED__FRESH_CHAT_VALIDATION_OPEN`  
Scope: Social Media Studio integration only. The CAOS repository, Skills and configuration are read-only and unchanged.

## Owner outcome

All owner-facing SMS conversations, material decisions, research, method selection, execution, recovery and acceptance must remain governed by the current CAOS parent Skill. Historical learning must be retrieved and applied across separate tasks without turning a one-off accepted output into a universal creative formula. The goal is lower preventable owner correction burden while maintaining or improving real deliverable quality.

## Directly observed evidence

1. The private Library already contained:
   - `/Social Media Studio/OWNER_PREFERENCE_PROFILE.md` (version 2);
   - `/Social Media Studio/CROSS_CHAT_EXPERIENCE_CASEBOOK.md` (version 5);
   - `/Social Media Studio/PROCESS_QUALITY_BASELINE.md` (version 1);
   - `/Social Media Studio/Methods/Cross-Project/INDEX.md`;
   - `/Social Media Studio/Methods/Cross-Project/CROSS_PROJECT_METHOD_TAXONOMY.md`;
   - `/Social Media Studio/Methods/Projects/` with 16 project-specific candidate cards.
2. The private owner profile explicitly separates current instructions, persistent scoped preferences, task-local decisions and inferred patterns. It says a one-off selected line/image/ratio/joke is not automatically a universal preference.
3. The existing SMS Skill and `STUDIO_ENTRY.md` discovered the owner profile, casebook and process baseline but did not point to the new private method index or project cards. Thus the method portfolio existed in storage but was not in the documented session retrieval path.
4. The existing Skill/entry already stated CAOS parent governance, but the entry did not give an explicit canonical CAOS source fallback or distinguish a source read from native Skill activation.
5. The current CAOS parent Skill requires original-source recovery, competing root-cause hypotheses, alternatives, falsifiers, independent outcomes and exact-head verification. The current SMS self-learning protocol requires project-local candidates, distinct independent replays, counterexamples, cross-task transfer, regression, rollback, owner-burden evidence, independent readback and CAOS acceptance before shared promotion.
6. The prior exact-head PR run `46046498127` on `4b444f555540411eaa1e93222c4e35ca884329f2` passed 616 tests and system/topology/smoke checks. That is the engineering baseline only; it does not prove native Skill activation or future creative outcomes.

## Competing root-cause hypotheses

| Hypothesis | Evidence | Disposition |
|---|---|---|
| Private method cards were absent | Library listing and readback show 16 cards | Rejected |
| Private method cards existed but were not discoverable from SMS startup | Skill and entry source omitted the Methods index path | Confirmed integration gap |
| A prior selected phrase was incorrectly promoted as a global rule | Current private profile explicitly warns against it; previous portfolio cards are marked candidate and task-scoped | No promotion observed in the records inspected; future retrieval still needs an explicit guard |
| CAOS parent Skill was natively selected in every fresh chat | No first-party client trace available | Unknown; cannot claim |
| The model can retrieve and apply the right card in a fresh task | No independent fresh-chat outcome trace | Not yet validated |
| More database/controller infrastructure is needed | Existing private Library, casebook and SMS Skill/entry can carry the missing discovery contract | Not supported; no new control plane justified |

## Alternatives considered

1. **Add more global prompt formulas or force every card into every task.** Rejected: duplicates the existing owner profile, increases context noise and encourages overgeneralization.
2. **Create a new SQLite table, agent, scheduler or controller for cross-chat method retrieval.** Rejected: the existing private Library is the owner-scoped source and SMS explicitly has no second scheduler/database; this would add authority and complexity without evidence.
3. **Promote the 16 cards or 12 method families into globally verified methods.** Rejected: the cards are summary-derived project candidates and do not satisfy the complete evidence ladder.
4. **Connect the existing private method portfolio to the existing CAOS-governed session entry and Skill.** Selected: smallest change that closes the observed retrieval gap while preserving source scope, privacy and candidate status.

## Decision and implementation

- `skills/social-media-studio/SKILL.md` now resolves the current CAOS parent Skill before substantive decisions. If no native workspace copy is available, it directs the session to retrieve the canonical read-only source:
  `D1traverser-debug/cognition-agent-os/.agents/skills/goal-grounded-semantic-review/SKILL.md`.
- It distinguishes `CAOS_SOURCE_READ_FOR_SESSION` from `NATIVE_SKILL_SELECTION_VERIFIED`. Reading GitHub is not evidence that a fresh ChatGPT client natively selected the Skill.
- The Skill now reads the private `Methods/Cross-Project/INDEX.md` before substantive method selection, retrieves only relevant project cards, and consults the cross-project taxonomy/backlog only when needed.
- Each candidate card must be checked for mechanism, trigger, applicability, avoid-when condition, counterexample, evidence level and rollback/re-entry point.
- A one-off owner-selected phrase, title, joke, cover line, mood, ratio, platform package or visual composition is a project decision/example (`D`), not a professional method (`M`). Transfer mechanisms, not surface expressions.
- `STUDIO_ENTRY.md` carries the same startup and retrieval contract.
- `tests/test_learning_source_admission.py` now checks that the CAOS source fallback, native-selection distinction, private method index and anti-template applicability contract remain discoverable.
- No private owner history, raw transcript or project-specific owner detail was added to public GitHub. No CAOS repository file was modified. No new controller, database, agent or scheduler was created.

## Acceptance and falsifiers

**Narrow engineering acceptance:** the exact updated PR head must pass focused tests, full test suite, system audit, topology audit and standalone smoke. Tests only prove the written discovery contract exists.

**Real behavior acceptance remains OPEN.** The decision is falsified or must be revised if:
- a fresh independent chat cannot retrieve the CAOS parent source or relevant private method index;
- the model copies a previously selected line or asset without current owner selection or dependent-stage continuity;
- it retrieves a superficially similar but inapplicable card;
- it ignores a relevant card, repeats a documented failure, or fails to explain why a method was not applicable;
- owner corrections/rework do not decrease without a quality trade-off.

Fresh-chat testing must record native Skill-selection trace if available, exact private source versions retrieved, selected/rejected method card, actual task output, independent review and owner correction burden. If no first-party trace exists, keep native selection `NOT_TESTED`; do not substitute this ADR, a passing test or a GitHub read.

## Re-entry

On a future owner task, start from the actual current demand; retrieve the private index and only relevant card(s); apply CAOS to compare the candidate against current evidence and counterexamples; record only material application/outcome evidence in the existing private casebook or project-local record. Keep method candidates unpromoted until the SMS evidence ladder and CAOS acceptance pass.
