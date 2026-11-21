# CAOS → Video Session Governance Handoff

**Status:** `ACTIVE_SESSION_GOVERNANCE_HANDOFF__NOT_VIDEO_STARTUP`  
**Canonical Video startup:** `STUDIO_ENTRY.md`  
**Video Skill:** `skills/video-growth-agent/SKILL.md`  
**Video runtime:** `video_studio.engine.StudioEngine`  
**CAOS parent source:** `D1traverser-debug/cognition-agent-os` (read-only)  
**Governance mode:** `CHAT_GOVERNED_EXTERNAL`

This is a Video-owned handoff for sessions in which the user has explicitly selected or entered Video under CAOS. It is not a second Video startup entry, a second controller, a parent task identity, or a runtime integration.

## Parent governance

When the active ChatGPT session is CAOS-governed, CAOS retains parent-level responsibility for:

- Restoring the complete user goal, constraints, corrections and authorization.
- Running the decision loop: investigate, compare competing explanations and methods, challenge assumptions, and select a justified approach.
- Running the execution loop: plan, execute, inspect, correct and independently verify.
- Returning to the earliest failed decision when a root cause is found.
- Accepting the result against the user's actual outcome, not documents, CI or model self-assessment alone.
- Promoting reusable methods only with evidence, applicability conditions, counterexamples and rollback boundaries.

Video retains authority over its own project IDs, media briefs, task DAGs, artifact records, rights/provenance, production execution, domain reviews and Video-specific learning.

## Runtime and capability boundary

The Video runtime is independently deployable. It has no CAOS runtime/API dependency, parent task ID or parent lease. Runtime independence does not permit bypassing CAOS parent governance when the active session is CAOS-governed.

Capability sources have distinct roles:

- `video_studio/data/studio_manifest.json`: current Video runtime and harness capability authority.
- `video_growth_agent/data/capabilities.json`: Video-domain capability inventory; it does not prove that a provider or tool is available in the current session.
- `STUDIO_ENTRY.md`: the only Video startup authority.
- `skills/video-growth-agent/SKILL.md`: Video-domain execution instructions.
- `docs/standalone_video_studio.md`: Video operating contract.

External image, video, audio and editing providers must be checked against the tools available in the active session. Their availability, model limits, cost and output evidence must not be inferred from this catalog.

## Hard boundary

**CAOS source is read-only. Do not modify the CAOS repository.**

Do not create, edit, delete, rename, merge or otherwise mutate CAOS repository code, files, documentation, branches, pull requests, configuration, releases or installed Skill assets. All system changes authorized for this task belong exclusively to the Video repository.

Do not create a second parent-governance ledger inside Video. Do not turn this handoff into a Video runtime dependency. Follow `STUDIO_ENTRY.md` for all Video startup and project routing.
