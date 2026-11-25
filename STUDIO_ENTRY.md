# 自媒体系统 — Social Media Studio · Canonical Entry

Status: `ACTIVE_CANONICAL_ENTRY__PRODUCTION_READINESS_PARTIAL`
This file, `STUDIO_ENTRY.md`, is the single startup authority for all self-media work.
Runtime: `social_media_studio.engine.StudioEngine`
CLI: `sms-studio`
Manifest: `social_media_studio/data/studio_manifest.json`
Operating manual: `docs/standalone_social_media_studio.md`

## Mission

Turn the owner's actual content goal—including independent writing, still images, IP identity, media editing, platform packaging and original video—into an independently checked deliverable. The system is outcome-driven, not stage-driven. Direct tasks need no artificial project or graph. Durable projects use a task graph derived from the specific brief; independent tasks can run concurrently, and only declared dependencies block work.

## Independence

Social Media Studio owns self-media requirements, project/task state, assets, evidence, production execution and domain learning. When the owner selects Social Media Studio in a CAOS-governed session, CAOS remains the parent authority for complete-goal recovery, decision quality, root-cause investigation, cross-domain authorization, execution discipline and independent acceptance. Use the CAOS parent Skill in the active ChatGPT workspace. The CAOS decision loop and execution loop govern session-level reasoning, authorization and independent acceptance. The self-media capability catalog is `social_media_studio/legacy/data/capabilities.json`; the source-owned internal subsystem catalog is `social_media_studio/data/subsystem_catalog.json`. Use `sms-studio subsystems --repo-root .` to inspect all declared internal modules and live imports. X short posts and X Articles are internal editorial capabilities. Other CAOS business systems offer only scoped read-only methods; they cannot supply self-media task authority. Do not modify the CAOS repository, Skills or configuration. The Social Media Studio runtime has no CAOS API/runtime/task-ID/lease dependency; technical independence is not permission to bypass parent governance. All owner-facing self-media conversations, decisions and effects remain CAOS-governed. Owner project creation requires explicit `--owner-task`; current-owner operations reject retired projects and fixture-marked roots. Offline mechanical regression requires `--offline-fixture` plus an explicit root that is empty on first initialization; the CLI writes a root-bound `.sms-offline-fixture.json` marker. Fixture mode cannot adopt an existing unmarked workspace, and owner mode cannot open a fixture-marked root. This marker is an accidental-mixing guard, not an authentication boundary, and fixture work does not claim CAOS activation. The fixed-stage controller is not an active self-media execution path.

**IPOS is a nested specialist domain within this Social Media Studio**, owning permanent creator/character identity design. Its existing installed Skill and private owner-approved canon are separately maintained; Social Media Studio imports exact approved versioned bundles downstream but never creates competing canonical state. Temporary avatars are ordinary visual craft and do not inherit the owner's personal IPOS project.

## Entry, routing and revisitable responsibilities

**Choose the execution surface, not a default workflow.** Recover the full current goal and apply CAOS recursively in either surface. A bounded conversational text, image-planning, critique or simple edit task may be performed with actual available session tools and direct outcome checks; do not create a project or DAG solely to simulate governance. Use the durable Studio ledger when persistence, artifact lineage, parallel dispatch, repeatable tooling or recovery materially requires it. A continuation resolves the exact current workspace identity from authorized evidence, not recency or retired history. The execution surface does not grant authorization or waive any applicable quality, rights, truth or independent acceptance requirement.

Recover the owner outcome, inspect relevant authoritative sources, research and challenge alternatives, select an admissible method, execute with current tools, independently inspect actual results and preserve validated learning. These are recursive responsibilities, not a prescribed order or a requirement to create a work packet for each conversation. Durable work uses the project brief, versioned assets, exact decision receipts and a demand-specific DAG; independent branches may proceed together, and a correction can reopen an earlier decision. A delivery or release requires only the applicable domain-specific gates, not unrelated video-production stages.

For a durable owner task, give `requirements.decision_id` an exact unique ID when planning; after current inputs and decision evidence are available, use `sms-studio decision PROJECT RECEIPT.json` with that `decision_id` and `task_id` plus the existing competing-cause/alternative fields. The engine derives the binding from actual current brief, task contract and input artifact bytes. Unbound/stale branches cannot be claimed or completed; unrelated admitted branches may proceed. Revise a stale task to a new decision ID and reopen it after re-investigation. This local check is not CAOS activation, verified external research, a permission grant, or semantic acceptance. Direct non-task session actions still require CAOS governance and appropriate independent evidence.

For a previously admitted owner workspace with the former scope epoch, a one-time **explicit** `sms-studio --root WORKSPACE migrate-scope PROJECT --reason REASON` converts its source scope without deleting project history. Old decisions are superseded, live leases revoked, and newly admitted actions require fresh current-scope decisions. This is a migration of the user's exact existing project, never automatic resurrection of retired repository examples. A bare source quote cannot replace semantic research or independent owner acceptance.

## Bounded operational loop and real parallel execution

For a durable owner-selected Studio workspace, use `sms-studio work-cycle PROJECT_ID --plan-only` to inspect admitted ready tasks, genuinely parallel agent/tool/human/external lanes, decision blocks, missing executors, invalidated descendants, unresolved failures and candidate methods **without** executing side effects. Use `sms-studio work-cycle PROJECT_ID --max-workers 2 --max-rounds 50` to run only registered, decision-admitted local tools in finite parallel dependency rounds and independently read back the resulting ledger. Each failed tool is attempted at most once per invocation; perform diagnosis and method challenge before a fresh attempt. Actual agents/humans/external providers require their own tool/session capability and authority. A completed graph is not an approved deliverable or publication. Learning candidates are never silently promoted.

## Hard release boundaries (when releasing an actual video)

For an actual video release, exact final bytes must pass applicable digest-bound FFmpeg/FFprobe technical checks (video stream, stream-duration match, true peak, black frames and full decode); used media assets in recorded lineage require cleared rights and resolvable evidence. **Only when the current owner brief requires human cold review, Red Team, EditorialPlan, timeline or platform-specific documentation** must those specialized receipts exist and satisfy their declared criteria. When Red Team is required, its review contract demands at least three evidence-backed findings and no unresolved critical/high risk. A simple video crop does not inherit an unrelated historical explainer storyboard or Red Team requirement. Source-version changes invalidate affected dependents. Release eligibility never authorizes public posting.

## Professional capability discovery and recursive governance

Professional capability classification is distinct from business workstreams, media object containment, roles, reusable knowledge, cognition dependencies and task execution. Discover exact groups with `sms-studio capabilities [--group GROUP]`; the output binds the catalog to registered adapters and local operations, discloses missing effects and does not select a task, authorize execution or certify quality. For current owner work, CAOS recursively governs every material choice at every organizational level, including the choice of professional method, reviewer, tool and verification. No group is a compulsory stage or permanent worker. Apply independent domain and overall owner acceptance separately. New evidence may reopen the earliest contradicted premise without invalidating unrelated branches. The existing engine is the only scheduler; use direct session capability for nonpersistent simple work where appropriate.

## Task-neutral intake and hierarchy

Use `sms-studio knowledge --id METHOD --repo-root REPOSITORY` to locate and hash the exact current reusable method source; historical/candidate sources require `--include-nonactive` and are never execution authority.

The canonical manifest defines authority layers, continuous responsibilities and separate product/business/professional/task axes. Load it and the operating manual. The candidate architecture in `docs/SOCIAL_MEDIA_STUDIO_ARCHITECTURE_V2.md` is a design/reference contract, not a second active control authority. For task-specific inspection, `sms-studio inspect-editorial`, `inspect-visual`, and `quality-plan` expose structure or intended reviews only; they cannot claim generation or professional quality. No prior task instance is active by default. The repository project index is retired evidence only. Never resume an old project or reuse its scope without a fresh owner demand; even explicit historical retrieval does not reactivate it. Preserve generic skills, technical adapters, methods and knowledge, not previous work orders.

```bash
python -m pip install -e .
sms-studio --root WORKSPACE intake REQUEST.json
# REQUEST.json contains mode NEW and the exact goal, or mode RESUME and exact project_id.
# After CAOS-governed interpretation and decision, use the actual current brief and DAG:
# Each task requirements.deliverable_refs names its current brief deliverable(s).
sms-studio --root WORKSPACE init PROJECT --brief BRIEF.json --owner-task
# If the actual demand has context inputs, import its explicit digest-bound manifest:
# sms-studio --root WORKSPACE import-manifest PROJECT CONTEXT.json
sms-studio --root WORKSPACE plan PROJECT TASKS.json
sms-studio --root WORKSPACE resume PROJECT
```

The intake response must not be treated as native CAOS activation proof. Every decision/action uses CAOS; professional aesthetic judgment and goal fidelity are cross-cutting responsibilities, not finished stages. Each demand chooses only relevant capabilities and tasks. Research, critique, execution, re-entry and learning follow evidence, not a compulsory sequence. Project learning remains CANDIDATE. Shared method promotion requires real-case evidence, at least two independent replays on distinct tasks, counterexamples, cross-task transfer, regression, rollback, owner-burden/cost evidence or a reasoned N/A, independent readback and CAOS owner-level acceptance, followed by a versioned repository change; no runtime or model promotes candidates automatically.

A claim returns a bounded work packet, exact input artifact digests and a lease token. Complete the task only after the declared output files have been written inside the project workspace:

```bash
sms-studio --root WORKSPACE claim PROJECT --worker WORKER --executor agent --task-id TASK
sms-studio --root WORKSPACE complete PROJECT TASK --worker WORKER --token TOKEN --outputs OUTPUTS.json
```

Use `sms-studio qa-media` for a claimed technical-measurement task and `sms-studio --help` for the complete command set. Use `sms-studio run-adapter PROJECT TASK_ID --worker ID --token TOKEN` for a task that declares a supported `requirements.domain_adapter` contract. This connects EditorialPlan, ShotContract, IPOS, Timeline, continuity, routing, business metrics, supplementary audio QA and local programmatic graphics to the standalone artifact ledger.

The local tool registry does not directly call external generative-video providers. Agent tasks may use a currently connected session tool only after checking its exact operation, availability, rights, cost and output constraints; any paid generation requires explicit owner approval. A provider result is not complete until its actual file and receipt are imported and digest-registered. No provider capability is assumed permanent or silently inferred from a router profile.

Run `sms-studio system-audit --repo-root .` for the repository audit. It separates structural integrity from production readiness: a structural PASS may still report missing provider execution, source media or owner approvals. `sms-studio` is the only installed CLI; `python -m social_media_studio` invokes the same runtime module.

## Completion rule

A project is not complete because a plan exists, a task graph is green, a renderer ran, or CI passed. Completion requires the requested final files, exact artifact identity, all applicable independent reviews, technical QA, rights/truth/disclosure checks, and an owner-visible list of any remaining unknowns.


## Cross-chat continuity (durable owner projects, not ordinary-chat interception)

A fresh conversation does NOT inherit the previous chat's raw context merely because a
SQLite project exists. Capture exact owner requirements, corrections, source excerpts,
failed-method lessons and next actions while they are available. Record them with explicit
source kind and locator; do not pass a model-made summary off as a verified user quote.

For a previously selected exact owner workspace and project:

~~~bash
sms-studio --root WORKSPACE capture-context PROJECT_ID NOTE.json
sms-studio --root WORKSPACE continuity PROJECT_ID
sms-studio --root WORKSPACE handoff PROJECT_ID > handoff.json
# In the new conversation, after recovering that exact same authorized workspace:
sms-studio --root WORKSPACE verify-handoff PROJECT_ID handoff.json
sms-studio --root WORKSPACE resume PROJECT_ID
~~~

NOTE.json fields: kind (OWNER_REQUIREMENT, OWNER_CORRECTION, SOURCE_CONTEXT,
IMPLEMENTATION_CONTEXT, FAILURE_LESSON, NEXT_ACTION), exact text,
source_kind (OWNER_MESSAGE, ATTACHED_FILE, TOOL_RESULT, ASSISTANT_SUMMARY),
source_locator and optional task_ids/artifact_ids. Attached artifact IDs are
checked against actual current project bytes. Notes are append-only project-scoped
DATA, not executable instructions, owner approvals, CAOS activation, source
authentication, or globally promoted methods. Corrections are explicitly flagged
for brief reconciliation and do not silently mutate the governing brief.

A handoff is digest-bound to the same workspace, project, revision and latest
event state. After any event or source change it must be regenerated and verified;
never reuse a stale handoff, even if its summary sounds plausible. It covers only
material actually captured in the durable ledger. It does NOT discover the
correct project automatically, reconstruct uncaptured conversations or verify that
a ChatGPT client selected the parent CAOS Skill. Ordinary new chats must still
resolve the actual goal and parent authority; direct simple tasks remain direct.
