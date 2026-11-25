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

## Task identity, cross-chat continuity and isolation

Keep four identities separate:

- **Subsystem ID:** a reusable long-lived capability boundary. It is not a work order.
- **Project ID:** one coherent owner outcome and its durable task context. It may span many conversations.
- **Task ID:** one project-local execution node in the dynamic DAG.
- **Conversation:** an ephemeral interaction surface. It is neither project identity nor task authority.

A short, self-contained request may stay in direct conversational execution; do not create a project merely to simulate governance. When durable persistence is warranted, use exactly one project for one coherent owner outcome. Split independent outcomes into separate projects. Reuse of a subsystem does not transfer another project's task state, brief, images or decisions. Cross-project reuse requires an explicit exact-artifact transfer by ID, version and SHA-256.

Use three explicit entry modes:
- `NEW`: a genuinely new owner outcome; no prior project is inherited by recency.
- `RESUME`: continue one exact current `project_id`.
- `ADOPT`: move an already-started conversation task into a new project using a validated `SOCIAL_MEDIA_STUDIO_ADOPTION_PACKET`. If the project already exists, use `RESUME` or append a checkpoint; do not duplicate it.

An adoption packet preserves the original and current goal, chronological user corrections, constraints, source references and their coverage level, claimed versus verified completed work, prior decisions, failures, open items, next action and context boundary. Prior decisions remain `REQUIRES_REVALIDATION`. A chat statement that something was completed is not proof; verified completion requires current artifact readback. Import source files separately through the digest-bound asset manifest. Unknown or partial chat history must be labelled as such, never upgraded to a complete transcript by inference.

At every deliberate pause or chat switch, append a project checkpoint with the session summary, user corrections, open items, work not yet registered as artifacts, source coverage and next action. Use `sms-studio checkpoint PROJECT CHECKPOINT.json`. Re-enter with `sms-studio resume PROJECT --output HANDOFF.json`. The exported handoff is a read-only projection, not a second authority; reconcile its project revision and event cursor against the live project ledger before making state-changing claims. If the live ledger is unavailable, continue only provisionally from the snapshot and label that limitation.

A long-running task can be continued in a new chat without becoming a new project. For a subtask that needs a clean context, declare `requirements.context_boundary` and use `sms-studio handoff PROJECT TASK_ID`. `DECLARED_INPUTS_ONLY` exposes only that task's exact declared inputs and contract; it omits the project brief and sibling-task context. Explicit excluded references remain excluded. The packet is read-only, does not claim the task, does not authorize effects, and cannot prove that the chat platform itself isolated its context. Return the produced artifact to the original project and verify its exact bytes before completing the task.

Project-local corrections and failures remain local. A reusable method is a candidate until independently replayed on distinct tasks, challenged with counterexamples and regressed. A system defect requires a versioned code/Skill/contract change and regression evidence. No single task can silently promote its preferences or a one-off workaround into global system rules.

## Task-neutral intake and hierarchy

Use `sms-studio knowledge --id METHOD --repo-root REPOSITORY` to locate and hash the exact current reusable method source; historical/candidate sources require `--include-nonactive` and are never execution authority.

The canonical manifest defines authority layers, continuous responsibilities and separate product/business/professional/task axes. Load it and the operating manual. The candidate architecture in `docs/SOCIAL_MEDIA_STUDIO_ARCHITECTURE_V2.md` is a design/reference contract, not a second active control authority. For task-specific inspection, `sms-studio inspect-editorial`, `inspect-visual`, and `quality-plan` expose structure or intended reviews only; they cannot claim generation or professional quality. No prior task instance is active by default. The repository project index is retired evidence only. Never resume an old project or reuse its scope without a fresh owner demand; even explicit historical retrieval does not reactivate it. Preserve generic skills, technical adapters, methods and knowledge, not previous work orders.

```bash
python -m pip install -e .
sms-studio --root WORKSPACE intake REQUEST.json
# REQUEST.json contains mode NEW with the exact goal, mode RESUME with the exact project_id, or mode ADOPT with a new project_id, brief and adoption packet.
# After CAOS-governed interpretation and decision, use the actual current brief and DAG:
# Each task requirements.deliverable_refs names its current brief deliverable(s).
sms-studio --root WORKSPACE init PROJECT --brief BRIEF.json --owner-task
# To adopt ongoing work from chat, use an explicit packet; ADOPT never creates a task graph:
# sms-studio --root WORKSPACE adopt PROJECT --brief BRIEF.json --packet ADOPTION.json --owner-task
# If the actual demand has context inputs, import its explicit digest-bound manifest:
# sms-studio --root WORKSPACE import-manifest PROJECT CONTEXT.json
sms-studio --root WORKSPACE plan PROJECT TASKS.json
sms-studio --root WORKSPACE resume PROJECT --output HANDOFF.json
# Record a chat-switch checkpoint without changing task state:
# sms-studio --root WORKSPACE checkpoint PROJECT CHECKPOINT.json
# Build one exact task handoff for an isolated clean chat:
# sms-studio --root WORKSPACE handoff PROJECT TASK_ID
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
