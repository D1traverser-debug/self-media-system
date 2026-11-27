# ADR — Cross-chat experience, owner preferences and process evolution

Date: 2026-11-27  
Status: CANDIDATE_IMPLEMENTED__FRESH_CHAT_VALIDATION_OPEN  
Scope: Social Media Studio only. CAOS parent source/configuration is not modified.

## Problem evidence

The owner reports repeated use of the SMS Skill across separate chats. Individual deliverables were eventually repaired, but the corrections, preferred styles, rejected approaches, process failures and methods were not reliably carried into future work.

Source inspection found:
- `self-learning.md` default-denied prior chats without a first-class owner-authorized retrospective import path.
- The engine's `learning` table is project-local; `record_learning` always creates a candidate. This is correct for project method evidence but cannot serve as the owner-wide preference profile for direct conversational work.
- Direct-session work is allowed without creating a dummy project, but there was no explicit private episode destination for material learning.
- Exact demand profiles already pointed to short-form, packaging and visual references, but candidate references could be skipped unless explicitly included as nonactive sources.
- The public repository is public; user-specific preferences and prior-chat history must not be committed there.

## Alternatives considered

1. Put all owner preferences and historical conversations into public GitHub — rejected for privacy.
2. Create a second global SQLite task/learning scheduler — rejected; duplicates the task ledger and is unnecessary for direct conversational continuity.
3. Keep all learning only in project-local SQLite — rejected; it misses direct-session work and owner-wide preferences.
4. Treat every historical conversation as automatically learnable — rejected; ambient and unrelated chats must remain default-denied.
5. **Selected:** use existing private Library as the owner-scoped episodic/preference source; keep public GitHub responsible for generalized Skill behavior, schemas, tests and validated reusable methods. Explicit owner authorization opens only the relevant retrospective self-media subset.

## Implemented boundary

- Private `OWNER_PREFERENCE_PROFILE.md`: current instruction > task brief > scoped persistent preference > inferred pattern. Explicit owner preferences apply immediately within scope; they are not empirical method claims.
- Private `CROSS_CHAT_EXPERIENCE_CASEBOOK.md`: material episodes, accepted/rejected outcomes, owner corrections, root causes, applicability and evidence confidence. Summary-level retrieval is not misrepresented as transcript-level evidence or independent replay.
- Private `PROCESS_QUALITY_BASELINE.md`: outcome quality and process quality are evaluated separately, including preventable corrections, repeated rework, research adequacy, tool correctness, verification coverage and owner burden.
- Direct-session work can append a material episode to the private casebook without creating a dummy project. Durable project records remain in the existing StudioEngine ledger.
- Retrospective cross-chat import requires explicit owner authorization and is limited to relevant self-media history. Raw private conversations, owner preferences and private case histories remain out of public GitHub.
- Exact demand-selected candidate references are retrieved with `--include-nonactive` and used as bounded hypotheses. Candidate status prevents promotion, not scoped study or use.
- Preference, episode and reusable method are separate lifecycles. General method promotion still requires real cases, distinct independent replays, counterexamples, cross-task transfer, regression, rollback, owner-burden evidence, independent readback and CAOS acceptance.

## Verification and remaining limits

- Private Library files were created and read back.
- SMS Skill, canonical entry, self-learning protocol, manifest, knowledge catalog and operating manual were updated.
- Regression tests cover scoped retrospective import, direct-session capture, preference/method separation, private source discovery and exact demand-to-reference mapping.
- Exact-head commit `24b4d64bae618d77909d4758a9e075bef738d3c4`: 612 tests passed; both PR and push CI passed; system audit, topology audit, smoke, historical regression and installed-outside-repo checks passed.

Not yet proven:
- native CAOS/SMS Skill selection in every fresh ChatGPT chat (requires first-party client trace);
- successful use of these private files and lower owner rework in a future independent fresh-chat task;
- independent validation/promotion of any reusable craft method;
- user satisfaction or publication/performance outcomes beyond explicit selections already recorded in the private summary casebook.

Falsifier: a fresh independent task fails to load relevant private sources, selects the wrong method, repeats a recorded failure, or produces no reduction in preventable rework without a quality trade-off. Reopen the earliest contradicted layer rather than adding another prompt patch.
