# Social Media Studio — CAOS owner-goal reconstruction and bounded execution evidence
Date: 2026-11-25
Status: OPEN / partial engineering slice; NOT production ready
Base: main @ 7cd1cff75fdb807cab8a23c8991dab793573c051
Change branch: refactor/caos-continuity-handoff-20261125
Authority: original owner request and subsequent corrections, not this report or test names

## Goal and evidence boundaries
Owner's primary requirement is an integrated Social Media Studio governed across all material decisions by CAOS, not merely a set of documented components: accurate task interpretation, professional content/image/video on demand, scoped parallel execution and corrective loops, content/media/rights provenance, reliable handoff across fresh ordinary chats, task migration into the Studio when authorized, exact separation of unrelated projects, repeated-error prevention and learning that is verified before cross-task reuse. The user also requires full-repository reality checks and no replacement of the CAOS or IPOS canonical authorities.

Observed on main:
- Canonical entry STUDIO_ENTRY.md, manifest and one active engine/CLI exist.
- StudioEngine uses per-project SQLite WAL, append-only events, tasks/decisions/failures/learning, artifact digests and existing resume().
- Existing resume() returns current project/task/asset/decision/failure/event state, but no dedicated exhaustive record of owner chat corrections and source-tagged carryover. The last-N events window can omit earlier chat notes. This is the concrete first vertical gap.
- record_learning() records project-scoped candidates; does not implement real independently authenticated promotion or automatic method transfer.
- CAOS chat-native Skill selection and external creative provider access are not verifiable in the Studio runtime. No inference of native activation.
- Draft PR #48 (signed review execution) and stacked #50 (cross-content gate tests) are open, unmerged, and do not establish the entire owner's result.

Source set examined: exact owner historical architecture transcript (983 lines), live Studio entry/manifest/subsystem catalog/engine/scope/CLI/system audit/tests, external CAOS parent Skill and parent protocol at main, and primary references LangGraph persistence, Azure event sourcing and OWASP persistent prompt/memory injection.

## Competing causal hypotheses and discriminators
H1 — Entry-selection failure: a new ordinary chat does not select CAOS/SMS. Discriminator: real positive and negative client-native selection traces, including unrelated chats. Status UNKNOWN; cannot be fixed with a new local SQLite command alone.
H2 — Context-loss failure: exact owner quote and corrections are not stored in the durable project. Discriminator: new engine instance after >40 unrelated/recorded events cannot recover earliest source-labelled owner requirement. Main lacked typed capture; current branch adds this path and tests.
H3 — Source-authority failure: previous chat summary/retired task or external text is treated as instructions/current truth. Discriminator: forged note authority, cross-project references, stale brief, altered packet. Current branch forbids note authority escalation and adds bounded tests; native LLM resistance NOT TESTED.
H4 — Method/acceptance failure: bad creative work receives green structural CI and globally learned guidance without independent cross-task outcomes. Discriminator: real content and real reviewer trials, two independent cross-task replays plus counterexamples. OPEN.

Diagnosis of the previous engineering drift: work collapsed into review-attestation proof, leaving H1/H2/H4 unaddressed. The observed engine resume H2 gap justifies a bounded integrated slice; it does NOT disprove the other hypotheses.

## Alternatives compared, and rechallenge before action
A. Add another CAOS-like independent controller / Host to own chat memory: rejects the existing single-ledger boundary, duplicates authority, and does not make native ChatGPT activation happen. Not selected.
B. Prompt-only session summaries, stored in docs: easiest but susceptible to truncation, provenance loss, cross-project confusion and stale resumes. Not selected as an authority.
C. Extend existing Studio event ledger with project-scoped typed continuity and digest-bound handoff/readback: reuses existing scheduler and durable source; minimal new write surface; preserves legacy behavior. Selected CONDITIONALLY for H2.
D. Replace all existing project storage with LangGraph/Temporal checkpoints: no evidence current owner requires replacement, large migration and stale source risk; defer unless C fails a genuine required use case.

Counterarguments against C: hashes only identify bytes, not truth or owner approval; manual context capture misses unseen chats; workspace is not automatically accessible from a new ChatGPT session; a semantic requirement conflict still needs owner/CAOS decision; broad README or CI cannot prove correct client routing. Therefore no auto-import, auto-publish, implicit authorization, or global promotion.

Falsifiers: duplicate current owner identities, resurrected retired task, leaking another project's context, stale handoff accepted, forged digest accepted, old note lost on restart, previously accepted unrelated workflows blocked, or source/artifact tampering accepted. Rollback: revert this isolated branch and its additive event writers; existing project data/old event schema remain intact, with no mutation to CAOS/IPOS.

## Implemented on isolated branch
1. social_media_studio/continuity.py uses the existing engine transaction and append-only SQLite events to capture typed context with a declared source, project revision, brief digest, exact task IDs, verified local artifact bytes and per-record digest.
2. StudioEngine exposes capture_continuity(), continuity_records(), handoff(), verify_handoff(); resume() includes ALL captured notes despite its normal bounded operational event history.
3. CLI explicitly surfaces capture-context / continuity / handoff / verify-handoff under the same owner/fixture workspace gate.
4. Handoff binds complete recorded ledger view, revision and event checkpoint; verifier rereads current state and rejects altered/cross-project/stale packets. It remains a locator/carryover of **recorded** context, never full-chat discovery or an effect grant.
5. The single subsystem catalog owns the new source module; the canonical entry and operating manual spell out exact boundaries and commands.
6. Negative and cold-reentry tests: >40 notes recovery, new engine process, copied/tampered/stale packet, cross-project isolation, explicit correction not silently mutating Brief, denied forged approvals, task/asset reference validation, real asset byte corruption and CLI fixture path.

## Required independent acceptance, not yet satisfied
- Matching-commit GitHub Actions system audit, full tests and separate subsystem audit PASS; then independently inspect changed files and negative test behavior. Until run, engineering status is UNVERIFIED.
- Actual new ChatGPT conversation selects CAOS/SMS from the owner's simple request without special project membership: native entry selection NOT TESTED.
- A genuinely long task with owner-authored corrections, source files, tools and generated artifacts handed to another real chat, resumed without omissions: NOT TESTED.
- Automatic capture of all authorized source chat content: NOT IMPLEMENTED. Manual capture is a supported bridge, not silent universal memory.
- Requirement corrections -> revised task graph -> independent semantic owner acceptance -> cross-task regression and procedure promotion: OPEN.
- Professional originality/quality, visual and video effects and platform content impact: OPEN.
- Draft PR #48's actual trusted review executor and independent real quality review: OPEN.
- Provider permissions and side-effect authority: no new grants or paid provider invocation.
- Existing project-level structural event immutability is a local database contract, not cryptographic authentication against a hostile database administrator.
- A live owner project should be verified with exact workspace and real owner authorization, never copied from historical examples.

## Next CAOS graph priorities
P0 governance: establish owner requirement source coverage, explicit source lifecycle, scope and native selection observations; resolve corrections without auto-authority, and prove whole-workflow cross-chat continuation.
P0 infrastructure: audit integration branch #48/#50 as evidence, choose safe base, ensure release semantics and real reviewer trust, test positive and negative release cases.
P1 production: verify research/editorial/visual/media tool execution and semantic outcome with real (owner-authorized) tasks, including image context pollution and separate-chat generation.
P1 learning: link validated failure repair to bounded reusable method, two distinct real tasks, counterexample, rollback and independent approval; do not self-promote from this document.
P2: actual platform metrics and release packages after owner authorization.

The work stays OPEN until the complete owner goal is independently accepted; no branch draft or green tests may upgrade it to READY.
