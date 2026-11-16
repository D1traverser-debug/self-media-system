# Video Production Semantic Audit and Re-Architecture Decision

**Audit date:** 2026-11-17  
**Status:** REARCHITECTURE_REQUIRED — CURRENT ADAPTER PR IS NOT A RELEASE CANDIDATE  
**Scope:** Video production system and its execution path.  
**CAOS boundary:** CAOS repository, code, documents, branches, PRs, configuration and installed assets are read-only and were not modified.

## 1. Executive decision

Do not continue extending the current adapter patch series. Do not merge PR #36 as the production-system solution.

The selected direction is an outcome-first Video Production OS: retain useful durable control-plane primitives, but rebuild the product boundary, execution layer, media pipeline, worker orchestration, deliverable contract and end-to-end acceptance around actual finished videos.

The production system must be independently operable without CAOS. CAOS is being used only as the external governance method for this re-architecture. Video must own the durable requirements, decision, failure, execution, verification and learning workflow that remains after CAOS is no longer in the loop.

The primary acceptance oracle is a complete, inspectable, reproducible video delivery package. Task counts, roles, DAG readiness, adapter declarations, CI status and architecture documents are supporting evidence, never substitutes for the output.

## 2. Owner outcome contract recovered

The system must serve at least these production families without forcing one visual template or one rendering method:

1. **Engineering-proof video.** Real code, commands, logs, measurements, source files, failures and verified results are the evidence. A fabricated terminal, invented metric or synthetic screen must never be presented as observed engineering proof.
2. **Cinematic technology/business explainer.** A clear argument is expressed through spatial cause-and-effect, purposeful motion, material/light/depth, editing rhythm and coherent sound. Static slides or generic SaaS-card motion are not an acceptable substitute.
3. **News × fiction × meme.** Current factual material and its sources remain distinct from fictional, satirical or meme elements. The work may be funny and expressive without presenting invented scenes or claims as real events.

Projects may be hybrids or define a custom type. These families are production-intent profiles, not mandatory stage templates.

A normal finished delivery must be able to include:
- final master video in the exact requested platform format;
- audio master and, where useful, separate voice/music/SFX stems;
- accurate subtitle/caption files;
- cover/thumbnail;
- editable project/source bundle and the assets required to reproduce the master;
- platform title, description, copy, tags and disclosure material;
- source, rights, provenance and release evidence.

The brief may add or remove optional package items, but it must not silently omit an explicitly requested deliverable. The current technology-explainer sample declares final video, cover, captions and publish copy, but does not explicitly require an editable source/project bundle or a separate audio master.

Cost policy is quality-constrained and free/local-first, not “use the cheapest tool regardless of quality.” No paid generation, GPU rental, subscription, upload or external spend is authorized by a tool declaration. A paid action requires an exact current capability/price quote and explicit owner authorization. Low-quality Mandarin TTS is not an acceptable shortcut. The Descript route was rejected as the core pipeline because of separate credits, watermark risk and inability to inspect the final render reliably.

## 3. Evidence examined

### 3.1 Repository and current branch state

- Video repository: D1traverser-debug/video-growth-agent.
- Main branch at audit: 6fac8f58227e8a9bf7f59707895692ade06b8806.
- Current PR #36 head at audit: 595838c78a3e28c59fb2fe6c7336664dd0f11bc2.
- PR #36 is open, unmerged, changes 22 files, adds approximately 4,389 lines and deletes 118 lines.
- The latest CI run examined for that head failed: 1 failed, 321 passed. The failure is in the Red Team evidence-validation test.
- The latest Codex review findings were attached to commit 296b218, not the current PR head. A historical “CI green” comment is superseded by the later failed run.

The new re-architecture branch is deliberately based on main, not on the accumulated adapter patch branch. PR #36 remains historical evidence and is not treated as the canonical target architecture.

### 3.2 Old 0.8 production controller

The old workflow declares 20 fixed stages and 56 work orders:
- 14 produce tasks;
- 39 review tasks;
- 1 measurement task;
- 2 meta-review tasks;
- 55 agent executors and 1 tool executor.

AgenticStudio dispatches work-order records, marks them READY/WAITING and returns work packets. It does not itself launch or supervise a pool of independent workers. Lower-wave completion rules also impose broad stage barriers where explicit dependencies are absent.

This is an approval-heavy stage/work-order controller, not a reliable parallel media-production executor. It is not to be extended as the new controller.

### 3.3 Standalone Video Studio

The standalone Studio has useful control-plane primitives:
- dynamic task DAGs and dependency validation;
- SQLite/WAL persistence and append-only events;
- atomic claims, worker leases and bounded retries;
- immutable artifact registration and SHA-256;
- downstream invalidation;
- decision, failure, review, release and learning records.

These are worth retaining or selectively refactoring.

However, the current CLI exposes project/task management, one-at-a-time claim/complete operations, technical QA and deterministic domain-adapter execution. It does not contain a worker-pool dispatcher that launches multiple agent/tool workers. Independent tasks can become READY and separate workers can claim them, but the runtime does not itself create, supervise or schedule those workers.

The 13-task technology-explainer graph has a sensible initial dependency shape: research and creative exploration can start in parallel; shot production and sound work can proceed independently after the plan; technical QA, rights, platform review and editorial review can fan out after assembly. But its production, sound and edit tasks are declared as agent work, not connected to actual media executors. A graph declaration is not a render.

The 35-task AI self-media commercialization graph is a business-program graph across growth, IP, commercialization and production economics. It is not a video-production acceptance test. For example, its Jensen source-media-inspection task is declared as a tool task without a tested domain adapter; platform-performance and commercial-outcome imports are external tasks without connected executors. This business program must not be mistaken for a finished-video workflow.

### 3.4 Current local media execution

The local programmatic-graphics renderer is explicitly constrained to short, silent, non-character information graphics such as title/quote/stat/bar-chart cards. It is not a cinematic scene renderer, audio engine, timeline compositor, voice pipeline or final-video production system.

The standalone adapter demonstration is a two-second title-card candidate. Its integration test validates graph wiring, not the complete execution chain from authored EditorialPlan through materialized ShotContract, real render, sound, assembly, QA and release.

The existing domain modules contain useful editorial planning, ShotContract, IPOS, MediaGraph, continuity, timeline, routing and metrics models. They are not yet joined into a complete executable production path. The current adapter switchboard is not a substitute for that path.

### 3.5 Proven production evidence

Two prior production lines demonstrate that actual video delivery is achievable without making paid AI-video generation the default:

- **Pilot 001 V9:** 31.000 seconds, 1080×1920, 30 fps, 930 frames, stereo AAC 48 kHz, -16.6 LUFS, -1.9 dBFS true peak, zero additional cash cost for the local release build. The final file passed stream-duration, frame-count, black-frame, silence and sampled visual checks. The V9 direction used real code, real failed versions, real FFprobe output, real QA and persistent project artifacts.
- **Pilot 002 V4:** 59.500 seconds, 1080×1920, 30 fps, 1,785 frames, H.264/AAC, BT.709, stereo 48 kHz, -16.07 LUFS and -1.49 dBFS true peak. It passed full decode, A/V duration parity, black/silence checks, spoken-content ASR checks and final contact-sheet review. Its visual route was original code-generated 2.5D motion using Remotion/SVG/CSS or equivalent local rendering; paid generative-video shots were not required.

The Pilot 002 motion review records real rejected iterations: flat labeled boxes, inadequate spatial depth, framing/cropping defects and a near-freeze were corrected before progression. The final QA explicitly distinguishes machine-measured checks from subjective human listening that was not performed.

These are production references, not universal style mandates. They prove that the system must preserve and generalize successful local render, audio, review and re-render methods instead of replacing them with a silent title-card demo.

## 4. Requirement-to-capability traceability

| Owner requirement | Current state | Audit judgement |
|---|---|---|
| Recover full goal, corrections, constraints and deliverables | Brief and Skill provide a useful structure | PARTIAL — no end-to-end dogfood proof across the three production families |
| Project-specific task graph | Dynamic DAG exists | PARTIAL — graph authoring exists; real execution is not connected |
| Independent tasks run concurrently | READY tasks and atomic claims exist | PARTIAL — no built-in worker-pool dispatch/supervision |
| Research and claim traceability | EditorialPlan/ClaimSpec domain modules exist | PARTIAL — not integrated into a complete production execution path |
| Shot-level production contract | ShotContract and materializer exist | PARTIAL — current adapter has contract-shape defects |
| Engineering-proof capture and rendering | Historical pilot evidence exists outside the canonical runtime | FAIL — no reusable, packaged production executor with evidence binding |
| Cinematic 2.5D/scene rendering | Pilot 002 proves a route; current local renderer is only short static graphics | FAIL |
| News/fact/fiction/meme separation | Brief has general truth/disclosure fields | PARTIAL — no tested archetype-specific editorial and release contract |
| Voice, music and sound design | Historical pilot output proves local sound design; current adapter renderer is silent | FAIL as a reusable current production capability |
| Timeline assembly and editing | Timeline domain model exists | PARTIAL — no complete executable master-composition path |
| Captions/subtitles and spoken-content QA | Deliverable names exist in examples; no complete integrated generation/alignment pipeline | PARTIAL |
| Cover and platform package | Candidate outputs appear in task graphs | PARTIAL — no complete executable/package validation |
| Editable source/project bundle | Not an explicit required artifact in the current technology-explainer brief | FAIL against the recovered owner output contract |
| Technical QA | FFmpeg/FFprobe hard-gate path exists | PARTIAL — freeze, silence, subtitle, ASR and route-specific checks are not all integrated |
| Rights and provenance | Metadata refs and release checks exist | FAIL-CLOSEDNESS NOT PROVEN — some references are not resolved to and byte-verified against evidence artifacts |
| Independent craft/audio/editorial review | Review records and self-attestations exist | PARTIAL — records do not prove actual independent multimodal inspection |
| Standalone method after CAOS | New Entry/Skill declare independence and contain decision/failure/learning methods | PARTIAL — declared method has not been proven through a real production/resume/failure cycle |
| No CAOS repository mutation | No CAOS files, code, branches or PRs were modified | PASS |

## 5. Concrete defects in the current adapter candidate

These defects are evidence of a broken integration contract, not a reason to add another isolated patch:

1. **ShotContract handoff mismatch (P1):** materialization writes an envelope containing adapter metadata and a nested shot_contract. Downstream validation/rendering passes the entire artifact to a parser expecting top-level ShotContract fields. The advertised materialize-to-render example therefore fails before rendering.
2. **IPOS reference-shape mismatch (P2):** generic materialization reads a references array but the native IPOS receipt carries reference_bindings. The current path can silently discard imported versions, digests, rights and consent references.
3. **Rights evidence false-pass path (P2):** some rights references are checked only for a current database row, not for the existence and digest of the referenced evidence bytes. A missing license document can therefore escape the recursive lineage byte checks.
4. **Silent-audio true-peak parsing (P2):** the numeric parser does not accept FFmpeg's negative-infinity true-peak value for intentional silence.
5. **Red Team finding validation gap:** per-finding evidence validation is nested under the minimum-finding-count branch. The current CI test expects unresolved evidence to be reported even when the finding count is below minimum; the test fails. Release still fails on the minimum count, but the evidence audit is incomplete.
6. **Current CI:** the latest examined run for PR #36 reports 1 failed and 321 passed.

Some earlier findings were addressed on the branch: FFmpeg's ordinary Peak label is parsed, strict decode uses -xerror, and the ShotContract's permitted production modes are compared against the EditorialPlan. The latest Codex review was not performed on the current head, so the remaining findings and regressions have not received a fresh independent review.

## 6. Root-cause analysis by layer

### L0 — Local defects
Broken payload envelopes, reference-shape mismatches, incomplete true-peak parsing and a release-check branch that skips some evidence checks.

### L1 — Capability gaps
The current production executor surface does not provide full scene rendering, engineering-proof capture, 2.5D motion, audio/voice production, timeline composition, subtitle alignment, project packaging or a complete visual/audio review loop.

### L2 — Workflow/execution gaps
The task graph describes production work but the runtime does not dispatch/supervise the required workers. Several tasks have executor labels without a tested executor. READY/claim state is being confused with actual work execution.

### L3 — Architecture gap
The control plane, old domain libraries, proven pilot render methods, current-session media tools and actual output packaging do not share one explicit executable contract. The adapter switchboard is a narrow bridge, not a production engine. The repository has two generations of runtime/entrypoint and still runs legacy controller smoke checks.

### L4 — Product boundary gap
The new Studio is scoped as the complete media-business domain, while the owner's immediate primary outcome is finished video production. Growth, IP and commercialization can inform a project, but should not be mandatory controller/workflow dependencies for every video. The product contract does not fully require the editable project/source bundle and audio master that the owner expects.

### L5 — Method-selection gap
The recent evolution optimized for connecting existing modules and proving adapter declarations rather than starting from successful end-to-end outputs and reconstructing the minimum reusable production system around them. The work therefore improved control-plane structure without closing the production outcome.

**Root cause selected:** the system lacks an integrated, outcome-driven production execution substrate and a complete deliverable acceptance contract. The local adapter defects are symptoms. A provider connection alone is not the root cause: Pilot 001 and Pilot 002 prove viable local production routes.

## 7. Competing architecture hypotheses and decision

| Option | Benefit | Failure mode | Decision |
|---|---|---|---|
| A. Keep the 20-stage/56-work-order controller and add more gates | Preserves legacy role and review data | Reintroduces stage barriers, review bureaucracy and no real worker execution | REJECT |
| B. Keep the 13-task DAG and keep adding adapters | Preserves the current standalone control plane | Still has no complete renderer/audio/editor/worker execution and encourages local patching | REJECT AS FINAL ARCHITECTURE |
| C. Make a paid external video provider the primary renderer | Fast access to generative footage | Cost, account availability, watermarks, rights and provider limitations become architecture dependencies; ignores proven local routes | REJECT AS DEFAULT |
| D. Outcome-first Production OS with a real executor/renderer layer, parallel worker orchestration, route-specific methods and complete package QA | Directly addresses output, parallelism, reproducibility and method independence | Requires deliberate migration and full end-to-end acceptance | SELECT |

The chosen architecture retains the useful dynamic DAG, durable state, claims/leases, artifact identity and release evidence concepts, but does not preserve the current adapter switchboard or the 20-stage controller as the product's execution architecture.

## 8. Target architecture

### 8.1 Product boundary

The primary product is Video Production. A project may attach growth research, IPOS canon, commercial obligations or platform-performance data as optional, typed evidence/context. These workstreams must not block unrelated production work unless an actual dependency exists.

### 8.2 Outcome compiler

Compile the owner's request into:
- production family and any hybrid/custom declaration;
- audience, thesis/story promise and factual/fictional boundaries;
- exact master/export formats and platforms;
- explicit delivery package;
- hard constraints, preferences, examples and unknowns;
- quality rubric and risk-specific acceptance criteria;
- cost/time limits and paid-action authorization;
- source/rights/disclosure obligations.

A changed owner outcome revises the brief and invalidates only affected descendants.

### 8.3 Dynamic production graph and parallel scheduler

Create tasks around the real work, not a fixed sequence. Independent research, competing concepts, source/rights checks, visual-method prototypes, provider capability/cost checks, audio tests and packaging research should run in parallel when inputs are ready.

After a story/shot plan exists, shot-level visual production, narration/audio, subtitles, cover concepts and platform-copy work may fan out where their inputs permit. Assembly joins only the assets it actually consumes. Technical, visual, audio, editorial, rights and platform checks fan out against the exact candidate and converge at release.

The scheduler must distinguish:
- READY work from work actually dispatched;
- declared executor from installed/verified executor;
- session tool capability from repository capability;
- candidate generation from promotion and release;
- blocked external dependency from failed work.

It must support worker capacity, concurrent claims, resource locks where needed, lease/heartbeat/recovery, idempotency, bounded retries, cancellation and a durable resume snapshot. A task without a real executor must be marked blocked/waiting, never silently completed.

### 8.4 Production executor layer

Use a provider-neutral execution contract with exact inputs, operation profile, cost/rights limits, run identity, status, output artifacts, provenance and verification receipt.

Initial execution routes:
- **Engineering evidence renderer:** imports exact source/code/log/measurement artifacts and produces a proof-led scene without fabricating observations.
- **Local 2D/2.5D motion renderer:** reusable scene/timeline composition derived from the proven Pilot 001 and Pilot 002 local approaches. It must support purposeful motion, spatial depth, scene transitions and a full audiovisual master, not only static title cards.
- **External video/image provider adapter:** optional and capability-handshaken per operation. No assumed availability, no implicit paid action and no provider lock-in.
- **Footage/screen-capture/compositing routes:** optional task executors with explicit source and rights contracts.
- **Audio executor:** human narration or a quality-approved voice route, procedural/licensed music and SFX, mix/master and separate stems. If voice quality fails, use an intentional text-led design with full sound rather than shipping poor TTS.
- **Timeline/composition executor:** assemble shot assets, audio, subtitles and transitions into the exact master; preserve editable project identity and source dependencies.

### 8.5 Archetype-specific acceptance

- Engineering proof: source-bound claims, reproducible commands/logs, real measurement, no fabricated UI/evidence, exact artifact lineage.
- Cinematic explainer: argument clarity, spatial causality, material/depth, purposeful motion, scene variety, audio integration, no static-slide substitution.
- News × fiction × meme: dated source map, fact/analysis/satire/fiction labels, no invented event presented as real, disclosure and platform fit, humour/voice review.

Each project may define its own rubric. The system must not force every film through the same visual style, duration, voice, provider or renderer.

### 8.6 Delivery package

The default production package must explicitly support:
- final master video;
- audio master and requested stems;
- subtitle/caption files;
- cover/thumbnail;
- editable source/project bundle with dependencies;
- platform title/copy/description/tags/disclosure;
- source and rights manifest;
- technical QA and independent review receipts;
- a reproducibility/resume manifest.

### 8.7 Quality and release

QA must consume the actual final bytes and exact digest. Separate technical, visual, motion, editorial, audio, spoken-content, subtitle, rights, disclosure and platform checks. At minimum, technical QA must cover video/audio streams, A/V duration parity, frame count, resolution, frame rate, full decode with strict error handling, black frames, freezes, unexpected silence, integrated loudness and true peak. Intentional silence is valid only when the brief declares it; a measurement of negative infinity is not a parser failure.

Contact sheets and extracted frames support review but do not replace inspecting the actual video. ASR supports spoken-content/subtitle alignment but does not prove naturalness. A model's self-review or a different reviewer label is not proof of independent human judgement. Any unavailable subjective review must be disclosed rather than fabricated.

## 9. Governance method that remains after CAOS

The Video Skill and runtime must independently preserve the useful governance loop:

1. Recover the owner's goal, corrections, prohibitions and deliverables.
2. Separate facts, assumptions, examples, preferences and unknowns.
3. Build a traceable requirement-to-output contract.
4. Research primary evidence and actively seek counterevidence.
5. Compare competing hypotheses and viable methods with discriminating tests.
6. Challenge the selected method and state its falsifier and rollback.
7. Build the smallest graph that satisfies the actual dependencies and parallelizes independent work.
8. Execute with durable claims, exact artifacts, provenance and failure recovery.
9. Verify the exact output independently; replay regressions after repairs.
10. Admit learning as a candidate first, then validate by independent replay and counterexample trials.

The runtime must enforce structured decision/failure/learning contracts and bind evidence references to real artifacts. A field containing a URL or arbitrary string is not proof. The Video Skill must be sufficient for a fresh Agent to resume and finish work without CAOS or hidden chat memory.

## 10. Migration plan

1. Freeze PR #36 as a historical candidate; do not merge it as the production solution.
2. Define and test the owner outcome contract and the three production archetypes.
3. Map useful 0.8 domain modules to typed capabilities; keep business/IP modules optional and remove the old fixed-stage controller from the canonical path.
4. Build the production executor and parallel worker protocol.
5. Package and generalize the proven local rendering/audio approaches; preserve pilot sources as benchmark fixtures, not as a single universal template.
6. Build full end-to-end project graphs for engineering proof, cinematic explainer and news × fiction × meme.
7. Verify all requested delivery files, source/project reproducibility, rights and exact-byte QA.
8. Dogfood primary success, failure, revision, concurrent work, session interruption and fresh-Agent resume.
9. Obtain independent review on the exact final branch head, run CI and real-media end-to-end tests, then prepare one canonical merge path.

## 11. Acceptance gates for the re-architecture

The re-architecture is not complete until:
- each of the three production families can execute a real end-to-end sample;
- each sample produces the complete requested delivery package, including editable project/source bundle;
- independent tasks demonstrably execute concurrently without duplicate claims or lost outputs;
- no task can complete with only a declaration, placeholder, missing executor or fabricated output;
- local motion rendering and full audio composition can reproduce the proven pilot quality envelope;
- optional external providers require exact current capability/price/rights evidence and owner authorization before paid operations;
- exact final media passes technical, visual, audio, editorial, subtitle, rights and platform gates appropriate to the project;
- the project can be resumed by a fresh Agent from durable Video state without CAOS;
- CI, independent review and actual media acceptance all pass on the exact final commit;
- CAOS remains unchanged.

**No local adapter additions are authorized by this audit as a substitute for the selected architecture.**
