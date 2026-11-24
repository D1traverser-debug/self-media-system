# Video Production Studio — Canonical Entry

Status: `ACTIVE_CANDIDATE`
This file, `STUDIO_ENTRY.md`, is the single startup authority for all Video work.
Runtime: `video_studio.engine.StudioEngine`
CLI: `vga-studio`
Manifest: `video_studio/data/studio_manifest.json`
Operating manual: `docs/standalone_video_studio.md`

## Mission

Turn the owner's actual media goal into a finished, independently checked deliverable. The system is outcome-driven, not stage-driven. Each project gets a task graph derived from its brief; independent tasks can run concurrently, and only declared dependencies block work.

## Independence

Video Studio owns Video-domain requirements, project/task state, assets, evidence, production execution and domain learning. When the owner selects Video in a CAOS-governed session, CAOS remains the parent authority for complete-goal recovery, decision quality, root-cause investigation, cross-domain authorization, execution discipline and independent acceptance. Use the CAOS parent Skill in the active ChatGPT workspace. The CAOS decision loop and execution loop govern session-level reasoning, authorization and independent acceptance. The Video capability catalog is `video_growth_agent/data/capabilities.json`. Do not modify the CAOS repository, Skills or configuration. The Video runtime has no CAOS API/runtime/task-ID/lease dependency; technical independence is not permission to bypass parent governance. All owner-facing Video conversations, decisions and effects remain CAOS-governed. The CLI defaults to current-owner scope and rejects retired or unmarked workspaces. Isolated offline mechanical regression requires explicit `--offline-fixture` and a separate root, and does not claim CAOS activation. The fixed-stage controller is not an active Video execution path.

IPOS remains the sole authority for the owner's original character/identity canon. The Studio consumes approved, versioned IPOS exports; it does not create a competing canon.

## New-task startup

1. Recover the complete owner goal and every correction, constraint, prohibition and requested deliverable. Separate hard requirements, preferences, examples, assumptions and unknowns.
2. Inspect current project state and exact source assets. Do not infer ownership, rights, media content or tool availability from filenames or declarations.
3. Create/update an outcome brief with audience, purpose, format, platform, deliverables, success criteria, constraints, budget/time limits and unresolved questions. A changed brief must be revised through the CLI so affected work is invalidated rather than silently reused.
4. Build a project-specific dependency graph. Revise the brief with `vga-studio revise-brief` and task contracts with `vga-studio revise-task` when new evidence changes the plan. Do not copy a fixed stage template. Split independent research, creative, asset, sound, production and distribution work where parallel execution is safe.
5. For material creative or architectural decisions, record competing hypotheses, discriminating evidence, alternatives, counterevidence, selected option, falsifier and rollback.
6. Prototype the highest-risk quality assumption before expensive full production. Use the smallest sample that can represent the intended final craft.
7. Execute through `vga-studio` task claims and actual available media tools. Never mark a task complete without its exact declared files and digests.
8. Review the actual artifacts independently. Reopen upstream decisions when evidence contradicts them; invalidate only dependent descendants.
9. Release-check the exact final artifact against configured review, rights and disclosure evidence.
10. Persist reusable learning only with applicability, counterexamples, failure conditions, source evidence and independent replay.

For a durable owner task, give `requirements.decision_id` an exact unique ID when planning; after current inputs and decision evidence are available, use `vga-studio decision PROJECT RECEIPT.json` with that `decision_id` and `task_id` plus the existing competing-cause/alternative fields. The engine derives the binding from actual current brief, task contract and input artifact bytes. Unbound/stale branches cannot be claimed or completed; unrelated admitted branches may proceed. Revise a stale task to a new decision ID and reopen it after re-investigation. This local check is not CAOS activation, verified external research, a permission grant, or semantic acceptance. Direct non-task session actions still require CAOS governance and appropriate independent evidence.

## Hard release boundaries

A video is not releasable until the exact final bytes pass digest-bound FFmpeg/FFprobe checks (video stream, stream-duration match, true peak, black frames and full decode), every used media asset in recursive lineage has cleared rights plus resolvable evidence, required human reviews are recorded against the exact digest, and the Red Team has at least three evidence-backed findings with no unresolved critical/high risk. Required platform/disclosure, EditorialPlan, timeline and other evidence artifacts must exist. Source-version changes stale their consumers and descendants. These checks never publish automatically.

## Professional capability discovery and recursive governance

Professional capability classification is distinct from business workstreams, media object containment, roles, reusable knowledge, cognition dependencies and task execution. Discover exact groups with `vga-studio capabilities [--group GROUP]`; the output binds the catalog to registered adapters and local operations, discloses missing effects and does not select a task, authorize execution or certify quality. For current owner work, CAOS recursively governs every material choice at every organizational level, including the choice of professional method, reviewer, tool and verification. No group is a compulsory stage or permanent worker. Apply independent domain and overall owner acceptance separately. New evidence may reopen the earliest contradicted premise without invalidating unrelated branches. The existing engine is the only scheduler; use direct session capability for nonpersistent simple work where appropriate.

## Task-neutral intake and hierarchy

Use `vga-studio knowledge --id METHOD --repo-root REPOSITORY` to locate and hash the exact current reusable method source; historical/candidate sources require `--include-nonactive` and are never execution authority.

The canonical manifest defines authority layers, continuous responsibilities and separate business/media/task axes. Load it and the operating manual. No prior task instance is active by default. The repository project index is retired evidence only. Never resume an old project or reuse its scope without a fresh owner demand; even explicit historical retrieval does not reactivate it. Preserve generic skills, technical adapters, methods and knowledge, not previous work orders.

```bash
python -m pip install -e .
vga-studio --root WORKSPACE intake REQUEST.json
# REQUEST.json contains mode NEW and the exact goal, or mode RESUME and exact project_id.
# After CAOS-governed interpretation and decision, use the actual current brief and DAG:
# Each task requirements.deliverable_refs names its current brief deliverable(s).
vga-studio --root WORKSPACE init PROJECT --brief BRIEF.json --owner-task
# If the actual demand has context inputs, import its explicit digest-bound manifest:
# vga-studio --root WORKSPACE import-manifest PROJECT CONTEXT.json
vga-studio --root WORKSPACE plan PROJECT TASKS.json
vga-studio --root WORKSPACE resume PROJECT
```

The intake response must not be treated as native CAOS activation proof. Every decision/action uses CAOS; professional aesthetic judgment and goal fidelity are cross-cutting responsibilities, not finished stages. Each demand chooses only relevant capabilities and tasks. Research, critique, execution, re-entry and learning follow evidence, not a compulsory sequence.

A claim returns a bounded work packet, exact input artifact digests and a lease token. Complete the task only after the declared output files have been written inside the project workspace:

```bash
vga-studio --root WORKSPACE claim PROJECT --worker WORKER --executor agent --task-id TASK
vga-studio --root WORKSPACE complete PROJECT TASK --worker WORKER --token TOKEN --outputs OUTPUTS.json
```

Use `vga-studio qa-media` for a claimed technical-measurement task and `vga-studio --help` for the complete command set. Use `vga-studio run-adapter PROJECT TASK_ID --worker ID --token TOKEN` for a task that declares a supported `requirements.domain_adapter` contract. This connects EditorialPlan, ShotContract, IPOS, Timeline, continuity, routing, business metrics, supplementary audio QA and local programmatic graphics to the standalone artifact ledger.

The local tool registry does not directly call external generative-video providers. Agent tasks may use a currently connected session tool only after checking its exact operation, availability, rights, cost and output constraints; any paid generation requires explicit owner approval. A provider result is not complete until its actual file and receipt are imported and digest-registered. No provider capability is assumed permanent or silently inferred from a router profile.

Run `vga-studio system-audit --repo-root .` for the repository audit. It separates structural integrity from production readiness: a structural PASS may still report missing provider execution, source media or owner approvals. `vga-studio` is the only installed CLI; `python -m video_studio` invokes the same runtime module.

## Completion rule

A project is not complete because a plan exists, a task graph is green, a renderer ran, or CI passed. Completion requires the requested final files, exact artifact identity, all applicable independent reviews, technical QA, rights/truth/disclosure checks, and an owner-visible list of any remaining unknowns.
