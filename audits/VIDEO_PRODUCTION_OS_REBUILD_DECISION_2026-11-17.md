# Video Production OS Rebuild — CAOS-Governed Decision Record

Date: 2026-11-17 (Asia/Tokyo)
Status: SELECTED_ARCHITECTURE__IMPLEMENTATION_IN_PROGRESS
Repository: `D1traverser-debug/video-growth-agent`
Rebuild branch: `refactor/video-production-os-rebuild-20261117`
Base: `main@6fac8f58227e8a9bf7f59707895692ade06b8806` (PR #35 merge)
CAOS source: `D1traverser-debug/cognition-agent-os` — READ ONLY; no source changes.

## 1. Owner outcome and scope

The governing outcome is useful, finished media, not a larger process model. The Video system must be able to turn an owner request into the actual requested assets, independently check them, and deliver a complete package. The owner may give examples, references or rough ideas; these are not limits on creative exploration. The system must originate concepts, compare them, select strong candidates and produce the requested outputs without repeatedly asking the owner to invent the creative direction.

Current concrete dogfood acceptance: a news-led X/Twitter meme package consisting of eight separately authored and separately generated images plus post copy and alt text. The eight images must have distinct core concepts, visual metaphors, compositions and styles; one shared prompt with eight cosmetic variations is not acceptable. Image text should be minimal. Factual reporting, interpretation, satire and fiction must remain distinguishable and source-grounded.

The system must also support actual video deliverables, including shot assets, assembled master, audio master, captions, cover, platform copy, editable source/project bundle, rights/provenance manifest and technical/craft QA evidence where applicable.

Hard boundaries:
- CAOS governs this work externally through its active ChatGPT intake and recursive decision/execution method. Do not modify the CAOS repository, branch, PR, files, installed Skill or configuration.
- Video owns its own requirements, task graph, artifacts, execution state, quality gates and learning. The finished Video system must not require a CAOS runtime, API, parent task ID or parent lease.
- IPOS remains the sole authority for original-character canon and identity rights. This rebuild does not modify IPOS.
- No paid provider, paid credit, external upload, publication or owner-device action is authorized by this decision.
- Never claim a declared provider, role, worker, review or test is executable without current execution evidence.

## 2. Live source and branch reconciliation

### Authoritative baseline
- Video `main` is `6fac8f58227e8a9bf7f59707895692ade06b8806`, the merge commit for PR #35, “Refactor Video Growth Agent into standalone outcome-driven Studio”.
- The baseline `video_studio.engine.StudioEngine` already provides a dynamic task DAG, atomic task claims, time-bounded leases, immutable artifact registration and digests, dependency invalidation, decisions, failures, reviews, release checks, learning receipts and an append-only event history. The baseline tests cover these mechanisms. This is valuable control-plane work and is retained unless an independent counterexample shows a defect.

### Competing candidate branches
- PR #36 (`fix/video-standalone-hard-gates-20261116`) is closed and unmerged. It is not a production baseline.
- PR #37 (`refactor/video-production-integrated-20261117`) is open at `a675e5d6a0c7de10342f9194b50cdd01dc9c6121`. Its exact-head CI run `44041064955` reports 347 passing and 2 failing tests. Its review has three findings: rights evidence is not propagated to assembled media outputs; the local tool scheduler can leave expired claims unrecovered when no other tool task is READY; task revision resets the attempt counter and reuses an existing output directory. The latter two behaviors were independently traced in the current source.
- `refactor/video-production-outcome-os-20261117` at `9cad189dc519982951f3ef6f5e82169977c2a266` is a divergent 64-commit branch with no matching CI run. Its semantic audit is useful evidence, but its code version removes rights-clearance validation from the production handler and does not retain the integrated adapter/executor surface. It is not safe to adopt wholesale.
- This rebuild branch is created directly from the verified Video mainline merge commit. Neither competing branch is merged or silently treated as current.

## 3. Whole-system findings

### 3.1 Legacy 0.8 fixed-stage controller
- `video_growth_agent/data/workflow.json` defines 20 fixed stages.
- `video_growth_agent/data/execution-plan.json` defines 56 work orders: 55 use `executor=agent`, one uses `executor=tool`.
- `video_growth_agent/data/executors.json` has an empty `trusted_executors` registry.
- `AgenticStudio` creates READY work packets and prompts; its own `AgentRegistry` documentation explicitly says registration does not mean persistent execution. It does not launch or supervise independent model workers.
- This fixed-stage system is not the new controller. Preserve historical records and selectively reuse proven domain logic; do not restore its 20-stage/56-work-order barrier as the production architecture.

### 3.2 Standalone Studio control plane
The mainline dynamic DAG, artifact ledger, lease, decision, failure, review, release and learning primitives are retained. They are not themselves a media-production engine. A READY task is eligibility, not proof that an executor ran. A task graph can be structurally valid while all its substantive work remains external.

### 3.3 PR #37 production layer is not an end-to-end production system
The PR adds four local production operations:
- `python_frame_render`
- `ffmpeg_assemble`
- `delivery_package`
- `ffprobe_media_qa`

The local worker pool executes registered `tool` tasks only. It explicitly leaves `agent`, `human` and `external` work outstanding. This is a valid boundary, but no actual agent-session dispatcher or provider executor is registered.

Current examples demonstrate the gap:
- `technology-explainer`: 13 tasks (7 agent, 5 human, 1 tool); media, audio and edit work is still agent work, not connected to the production executors.
- `news-fictional-media`: 13 tasks (8 agent, 5 human); no local production task is wired to generate the promised media.
- `program-linked-episode`: 14 tasks (7 agent, 5 human, 2 tool); actual shot/voice/edit production is still declared as agent work.
- `ai-self-media-commercialization`: 50 tasks (32 agent, 12 human, 6 tool). The local smoke test executes the MediaGraph bootstrap tool, not the five independent initial agent tasks.

The system audit validates the repository contract, graph shape, adapter registry and a local tool smoke. It returns `production_readiness=PARTIAL` when provider/owner inputs are absent. A structural audit PASS is not evidence that an episode or image set was produced.

### 3.4 Existing production tests prove plumbing, not the requested craft
The test called `test_end_to_end_production_render_qa_and_delivery_package` assembles pre-imported synthetic clips/audio, runs technical QA and packages declared files. It does not create the source shots or independently review their craft. The Python renderer test creates a 10-frame, 5-fps moving-circle sample. The parallel tool test claims two independent local render tasks in one round; it does not establish an agent-worker pool or automatic dispatch of agent tasks.

The Python frame renderer executes project-supplied Python in a child process. Isolated Python mode is not an OS/network sandbox. A task field `trusted_code_execution=true` is a declaration, not proof of an owner-granted execution boundary. Arbitrary project code must not be treated as safely sandboxed.

The existing programmatic-graphics renderer is a narrow, deterministic candidate renderer for title, quote, stat and bar-chart cards. It is not a general image-generation engine and does not satisfy a diverse meme/image-set request.

### 3.5 Product and acceptance gaps
- No first-class image-set contract or X/Twitter image-generation workflow exists.
- There is no collection-level prompt/visual diversity gate to prevent eight near-identical concepts.
- There is no registered image-generation executor in the repository. A current ChatGPT image tool may be used only through an explicit session-capability check; the repository must not claim a local provider is connected.
- The video production tasks do not yet bind story/shot contracts to actual renderer operations, sound operations, assembly and complete source delivery.
- The current brief examples omit important output obligations in some paths, including a consistent editable source/project bundle and separate audio master.
- Rights evidence must be attached to each media output and resolve to exact, current evidence bytes. A clearance status alone is insufficient.
- Technical QA cannot substitute for visual craft, editorial truth, image-set diversity, platform compliance or owner outcome acceptance.

### 3.6 Quality evidence
- Pilot 002 V4 is explicitly rejected by the owner for insufficient visual quality. Its failure audit records visual sameness, narrow object vocabulary, limited shot scale, decorative rather than causal material behavior, weak human/technology contrast and excessive dependence on typography. It is a negative benchmark and must not be promoted or reused as a default style.
- The Pilot 002 quality rebase requires a small near-final sample before full production and separates technical correctness from craft quality.
- The local graphics renderer audit establishes a constrained, candidate-only deterministic route, not general cinematic quality or generative-image capability.

## 4. Root-cause decision

### Competing hypotheses
1. **Local defects alone** (missing import, float assertion, output-path collision, rights metadata). These are real defects, but fixing them cannot create missing image/video executors or connect production tasks to the graph. Rejected as the root cause.
2. **Insufficient worker concurrency alone.** The tool pool is narrow and agent tasks are not automatically dispatched. This is a contributing cause, but adding more workers cannot execute a task that has no registered production capability or complete output contract. Rejected as sufficient.
3. **External provider availability alone.** No repository-registered generative-video executor exists, and session tools are not the same as a persistent provider integration. This constrains some routes, but does not explain missing local task wiring, incomplete output contracts or the absent image-set pipeline. Contributing cause, not the root.
4. **Product/execution/acceptance boundary mismatch.** The repository is strong at describing and governing work but weak at binding each requested deliverable to a real executor and an independent output-level acceptance oracle. Structural task completion and tool registration have been mistaken for production readiness. This explains the repeated failure across the old fixed-stage system, the new DAG and PR #37. **Selected root cause.**

### Alternatives
- Continue PR #37 and patch its three findings: rejected as the primary route because it preserves the current adapter-switchboard and task/executor mismatch.
- Adopt the outcome-os branch: rejected because it lacks exact-head CI and removes a necessary rights gate.
- Restore the 0.8 fixed-stage controller: rejected because it reinstates serial stage barriers and 55 unexecuted agent work orders.
- Rebuild from main, retain the proven control-plane primitives, and design a real outcome-to-executor-to-delivery path: selected.

## 5. Target architecture

### A. Outcome contract
Introduce a typed media-job contract. A job declares exact deliverable types and counts, audience, platform, facts/fiction boundaries, rights/likeness, disclosure, budget, format, quality rubric and delivery package. Supported deliverables include:
- `image_set` and individual `image`
- `social_post` (copy, alt text, source/disclosure metadata)
- `short_video` and `long_video`
- `audio_master`, captions/subtitles and cover
- `editable_project_bundle`
- evidence/QA/review manifests

A deliverable is complete only when the requested bytes exist and pass the appropriate output-specific acceptance. A plan, prompt, work packet or renderer declaration is not the deliverable.

### B. Creative and editorial layer
Separate research/fact map, creative concept cards, selection, shot/image contracts and prompt compilation. Treat user examples as optional inspiration unless explicitly made hard requirements. Generate competing creative directions independently.

For an eight-image set, each image must have its own concept identity and complete prompt. Require eight distinct core visual metaphors, no reused prompt body, at least six visibly different visual grammars by default, and a collection-level diversity report. A single shared prompt with `n=8` cosmetic variations does not satisfy this contract. Keep image text minimal unless the concept specifically needs it. Factual claims and satirical invention must remain separately labelled.

### C. Dynamic production DAG
Retain the mainline DAG engine. Add tasks around real production dependencies, not universal stages. Research, concept exploration, rights checks, visual references, sound options and platform packaging can fan out in parallel. Each task must bind:
- a typed capability ID and executor class;
- exact, digest-bound input artifacts;
- exact outputs and output schema;
- real prerequisites and resource/cost policy;
- measurable acceptance and failure conditions.

### D. Modular executor registry
Replace the monolithic adapter switchboard with small, typed capability modules. Distinguish:
- `agent_session`: work executed by the current ChatGPT/connected agent session or an explicitly connected worker. No auto-spawn claim without a real worker.
- `local_tool`: deterministic local render, audio, assembly, QA and packaging.
- `external_provider`: image/video/audio provider operation, only after current-session or account capability, availability, rights and cost handshake.
- `human`: genuine owner or independent-human decision/review. Do not synthesize human approval.

An unregistered executor remains blocked/awaiting capability. It must never be marked completed because its prompt or adapter declaration exists.

### E. Media execution plane
Build a coherent, provider-neutral media plane:
- image generation and image-set handling;
- shot asset/reference preparation;
- deterministic graphics for the limited formats they actually support;
- scene/shot rendering and compositing;
- voice, music, ambience and SFX as separately governed assets;
- timeline assembly and captions;
- final media measurement;
- visual/editorial/craft review;
- complete editable-source and delivery packaging.

Keep local-first methods where they meet the craft target. Use external engines only when their exact operation is currently available and owner-approved. A cheap route that fails the craft floor is not an acceptable optimization.

### F. Reliability and provenance
- Reconcile expired leases before deciding there is no work.
- Use a unique execution/revision identifier for every output directory; never derive output identity solely from an attempt counter that resets on task revision.
- Preserve immutable candidate versions and exact input/output digests.
- Rights and consent evidence must resolve to current registered evidence artifacts with verified bytes, digest and allowed kind; propagate those references to every derived media output.
- Do not execute arbitrary project Python without a real OS-level sandbox and explicit owner authorization. The boolean `trusted_code_execution` alone is not authorization.
- Candidate generation, asset promotion, final release and publication remain separate decisions.

### G. Independent acceptance and learning
Use distinct acceptance oracles for:
- editorial truth and source fidelity;
- visual concept diversity and meme readability;
- visual craft and continuity;
- audio/speech/caption quality;
- technical stream integrity;
- rights, consent, likeness and disclosure;
- platform fit and final delivery completeness.

Review the actual output bytes, not only metadata. A technical PASS cannot override a craft rejection. Persist methods only with applicability, counterexamples, failure conditions and independent replay.

## 6. Dogfood acceptance

### Social/news image-set
A fresh source-led job must produce:
1. exactly eight separate image files;
2. eight independently authored concept cards and prompts;
3. no duplicated core metaphor or prompt body;
4. at least six different visual grammars, with clearly different composition and focal event;
5. minimal/no in-image text;
6. a concise X post, alt text and source/disclosure notes;
7. per-image visual QA plus a collection-level diversity check;
8. a complete manifest binding each output to its prompt, source claims, generation method and digest.

The assistant must originate the creative directions; the owner is not required to invent the concepts. No automatic publication.

### Video
A real near-final sample must be generated from declared source assets and shot contracts, then assembled and inspected at normal playback speed. The complete delivery package must include the master, separate audio master, captions, cover, publish copy, editable project/source dependencies, rights manifest and exact-digest QA/review receipts. The sample must pass its project-specific craft floor; a synthetic moving-shape test is only an executor smoke test.

### Runtime and recovery
- Independent ready tasks must be claimable and executed concurrently by actual workers, not merely listed as READY.
- All executor classes must report their actual status and blocker.
- A killed worker must be recoverable after lease expiry.
- A task revision must create new output paths and preserve old artifacts.
- Missing provider, rights or owner inputs must fail closed without blocking unrelated work.
- Release must be checked against the exact final artifact and all required evidence.

## 7. Implementation scope and order of work

This is a dependency graph of implementation obligations, not a new fixed production pipeline:
- establish typed media-job and deliverable contracts;
- implement the image-set/social-post vertical slice and dogfood it against the owner's eight-image requirement;
- connect video shot/timeline/audio/assembly tasks to real registered executors;
- implement the worker/external-capability boundary and genuine parallel execution;
- harden lease recovery, revision-unique outputs, rights evidence and code-execution isolation;
- replace structural-only system audit with output-level end-to-end acceptance;
- update the Video Skill, entrypoint, examples and migration guide so the system operates independently of CAOS.

Do not merge PR #37 or the outcome-os branch as a shortcut. Selectively reuse a component only after reading its source, verifying its security/rights behavior and passing the new vertical-slice acceptance.

## 8. Falsifier, rollback and open limits

The selected route should be reconsidered if the current PR #37 can, without new architectural work, pass exact-head CI and produce the full social image-set and video deliverables with actual parallel execution, complete rights evidence, reliable crash/revision recovery, visual/craft acceptance and editable delivery. Current evidence does not meet that test.

Rollback: this rebuild is isolated on a new branch from the mainline merge commit. PR #37 and the outcome-os branch remain untouched as historical candidates. No mainline merge occurs until exact-head CI, independent code review, end-to-end user-outcome acceptance, recovery tests and a verified rollback are all complete.

Open limits:
- The repository has no verified persistent external generative-video executor.
- The current ChatGPT image-generation tool is a session capability, not a repository-local executor; it must be explicitly invoked and its resulting assets must be registered through an available artifact handoff.
- No paid provider or publication action is authorized.
- Owner approval remains required for final publication and any separately gated paid/external effect.

## 9. Governance boundary

CAOS supplied the recursive diagnosis, source reconciliation, alternatives challenge, falsifier and independent-acceptance method for this rebuild. This decision and all implementation remain Video-owned. The Video Skill and runtime must carry the durable method so future Video work can continue without a CAOS runtime or parent task. The CAOS repository and installed CAOS Skill were not modified.
