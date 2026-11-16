# Standalone Video Studio — Product, Method and Runtime Contract

Status: `ACTIVE_CANDIDATE_1.0`
Runtime: `video_studio.engine`
Entry: `STUDIO_ENTRY.md`
CLI: `vga-studio`
Manifest: `video_studio/data/studio_manifest.json`

## 1. Product outcome

Video Studio turns an owner's media goal into finished media and release materials. Its primary success oracle is the delivered work, not the presence of roles, stages, prompts, diagrams, task counts or passing tests.

Supported work may include cinematic explainers, technology/business documentaries, engineering demonstrations, news × fictional-video satire, meme and entertainment edits, product/brand films, animation, trailers, tutorials, shorts, long-form videos, platform-native derivatives and mixed-media work.

No single visual style, runtime, aspect ratio, duration, model, editor or production method is universal.

## 1.1 Business-domain scope

The Studio is the standalone control plane for the complete Video Growth Agent domain, not only a clip renderer. A project graph may cover one workstream or connect several:

- **MEDIA_GROWTH** — audience/problem research, demand signals, platform strategy, portfolio and series hypotheses, packaging, distribution, retention and audience outcomes.
- **ORIGINAL_DIGITAL_IP** — video-side use of approved IP, recognition/performance evidence, character/asset usage strategy and licensing-use value. Canon, likeness and identity rights remain owned by IPOS.
- **COMMERCIALIZATION** — sponsor/category fit, offer hypotheses, deliverable obligations, product-truth requirements, rights scope, measurement and commercial outcomes.
- **PRODUCTION_SYSTEM** — editorial research and claims, story/shot design, assets/takes, generation, compositing, edit, sound, QA and release.

Cross-workstream decisions must be explicit. Audience evidence may change a series hypothesis; IP performance may change packaging or licensing strategy; sponsor obligations may change format and product-asset requirements; production cost, failure and reuse evidence may change future portfolio allocation. Editorial truth, rights and owner authority remain hard constraints. Do not optimize one proxy such as views, CTR, cinematic quality, AI-video percentage or lowest credit cost.

The `video_studio` engine supplies the durable project control plane: briefs, dynamic task DAGs, leases, artifacts, decisions, reviews, failures and learning receipts. It does **not** silently recreate every legacy domain object. When Program/Series/Episode/Shot/Timeline, continuity, provider routing, business metrics or IP identity semantics are required, reuse the corresponding Video-owned domain module through an explicit, tested adapter and register its outputs as versioned Studio artifacts. Do not use the legacy fixed-stage `StudioOrchestrator` as the new controller. Existing specialized modules are optional capability libraries, not a hidden parent workflow.

## 2. Authority and independence

- **Owner request and corrections** define the goal and constraints.
- **Project brief** is the current executable outcome contract. Revisions are recorded in the append-only event history with old/new digests and reason.
- **Decision receipts** explain material choices and their falsifiers; they do not override owner requirements.
- **Task graph** owns execution dependencies and task state.
- **Artifact records** own exact file identity, digest, version, rights and producer lineage.
- **Review records** own artifact-bound evaluation evidence.
- **Event log** is append-only operational history.
- **IPOS** remains the sole authority for original character/identity canon.

The new runtime is standalone. It has no CAOS imports, network calls, API, parent task identity, parent lease, hidden chat-memory dependency or external governance callback. The old 0.8 product architecture, `vga` CLI, stage workflow, and CAOS integration notes remain compatibility/history surfaces; the new `vga-studio` runtime does not load them.

## 3. Goal recovery and requirement governance

Every project brief should record:

- `goal`: the observable result the owner wants;
- `audience`: intended viewer and their prior knowledge;
- `deliverables`: exact files or publication packages expected;
- `format`: duration, aspect ratio, resolution, frame rate, language and platform when known;
- `content_contract`: topic, argument, emotional effect, narrative promise and content boundaries;
- `craft_contract`: visual, motion, editing, sound, voice, typography and continuity expectations;
- `hard_constraints`: non-negotiable facts, rights, identity, budget, deadline, tool and safety limits;
- `preferences`: ranked preferences that may be traded off transparently;
- `examples`: references or examples, not automatically hard requirements;
- `unknowns`: unresolved facts or decisions;
- `success_criteria`: observable acceptance conditions;
- `release_policy`: required review rubrics, rights states and publication evidence.

When requirements conflict, do not silently choose one. Record the conflict, identify which source has authority, compare the consequences, and ask one concise question only if the owner must decide. Never convert an illustrative example into a universal rule.

## 4. Recursive decision method

Decision work is a revisitable graph responsibility, not a fixed pre-production stage. Use it when a material uncertainty, repeated failure, creative fork, expensive commitment or architectural choice exists.

A material decision receipt contains:

1. the exact question and scope;
2. source references and their freshness/authority;
3. at least two competing root-cause or interpretation hypotheses;
4. a discriminating observation/test for each hypothesis;
5. at least two viable alternatives, with benefits, costs and counterevidence;
6. the selected option and why it fits the whole outcome;
7. a falsifier that would overturn the choice;
8. a rollback or recovery route.

Rechallenge the preferred solution and the research coverage before execution. New evidence may invalidate a downstream decision and reopen an upstream one. Do not repeat analysis without new evidence; do not stop while a material discriminator remains available.

## 5. Dynamic task graph, not a fixed production pipeline

The planner creates nodes around the work actually needed. A node declares:

- stable `task_id`, title and task kind;
- executor class (`agent`, `tool`, `human` or `external`);
- dependencies (`depends_on`);
- exact input artifact names;
- exact output artifact names;
- `requirements` such as capability, source, rights, model operation, cost or quality constraints;
- non-empty `acceptance` conditions;
- priority and bounded retry count.

The graph must be acyclic. Each output name has one producer. Independent nodes are eligible concurrently. A task with missing inputs waits; a task whose dependency fails or becomes stale is blocked. The runtime distinguishes READY work from actual dispatch: only a registered executor can be claimed by the local worker pool. The engine does not force every project through research → script → storyboard → lookdev → generation → rough cut → sound → QA. Those are possible tasks only when the project needs them.

Typical parallel lanes may include:

- factual/editorial research;
- audience and competitor research;
- alternative creative concepts;
- visual reference and art-direction research;
- audio/voice/music research;
- tool/provider capability and cost checks;
- rights/product/likeness checks;
- cover and platform packaging.

Their outputs converge only where there is a real decision or production dependency.

## 6. Production strategy

Choose the medium per story beat or shot, not per project. Admissible methods may include real footage, licensed archive, image generation, video generation, image-to-video, 3D, procedural animation, kinetic typography, diagrams, code-driven graphics, compositing, practical photography, screen capture, NLE editing, generated voice, human narration, music, sound effects and deliberate silence.

A hybrid film may use different methods for different shots. The most expensive engine is not automatically best; the cheapest engine is not acceptable if it misses the required craft ceiling. Tool feature declarations are not proof of the exact operation combination, current availability, rights or output quality.

For high-risk creative assumptions, build a 3–12 second near-final sample or a small set of hero shots before full production. The sample should represent the final visual language, camera/motion, material quality, typography, sound and transition where relevant. A technical proof that a tool runs is not a quality proof.

## 7. Execution, leases and recovery

The runtime uses SQLite with WAL, foreign keys, busy timeout and `BEGIN IMMEDIATE` for task claims. Each worker receives a unique claim token and time-bounded lease. Heartbeats extend leases. Expired claims are recoverable within the task's retry budget. A worker whose token is no longer current cannot complete or overwrite the task.

The work packet contains only the declared task, acceptance contract, requirements and exact input artifacts/digests. Workers do not peer-chat as an authority mechanism; handoffs occur through artifacts and receipts.

A task completes only when all declared output names are supplied and each output is a real regular file inside the project workspace. The runtime computes SHA-256 and size itself. Registered artifact paths are immutable; a new take or revision gets a new path and version. Files outside the project must first be imported as source assets.

## 7.1 Local audiovisual assembly and delivery packaging

The production execution package provides two registered operations:

- `python_frame_render`: executes a declared project-owned Python source artifact exposing `render_frame(t, width, height, assets, params)`. Both the task contract and FrameRenderSpec must set `trusted_code_execution=true`. It streams exact RGB frames to FFmpeg and emits a silent candidate shot plus a receipt binding source/assets to the output digest. This is trusted code execution, not an OS/network sandbox; never expose secrets and execute only reviewed project code.
- `ffmpeg_assemble`: consumes a versioned render spec plus exact registered video/audio/SRT inputs. It assembles sequential shot assets, applies cover/contain fit, mixes offset/gain-controlled audio tracks, optionally burns valid SRT captions, and emits a candidate MP4, a separate 24-bit/48 kHz WAV audio master and a receipt binding input artifact IDs/digests to output hashes. It requires FFmpeg and FFprobe. The current first version uses cut-based sequential assembly; transitions and complex overlays belong in shot rendering or a later tested timeline capability.
- `delivery_package`: validates required artifact presence, SHA-256 and expected media types, then creates a ZIP containing final deliverables, project timeline/source assets and QA/rights evidence plus an external manifest with the package digest. It is candidate-only and never authorizes release.

Run registered local tools with:

```bash
vga-studio --root ./studio-work run-ready-tools PROJECT_ID --max-workers 4
```

The worker pool claims up to the configured concurrency of independent READY tool tasks, executes them concurrently, refreshes the DAG and continues in downstream rounds. It only runs registered local operations, including trusted Python frame rendering, FFmpeg master assembly, delivery packaging and FFprobe technical-measurement tasks. It reports tool tasks with no registered executor instead of claiming them. It does not spawn LLM agents, human reviewers or external providers. Use executor-filtered claims for session agent work:

```bash
vga-studio --root ./studio-work claim PROJECT_ID --worker researcher-01 --executor agent
```

The assembler composes shot assets; it is not itself a general scene renderer. Engineering-proof capture, cinematic 2.5D shot rendering, voice/narration, music/SFX creation, cover design and platform copy must be produced by their own verified route and supplied as registered artifacts. No paid provider operation is inferred from a task label.

## 8. Asset, rights and provenance contract

Each asset has a stable ID, logical name, version, relative path, SHA-256, byte size, media type, kind, status, rights state, producer and metadata. Rights states include `OWNED`, `AUTHORIZED`, `LICENSED`, `PUBLIC_DOMAIN`, `UNKNOWN` and `NOT_APPLICABLE`.

`UNKNOWN` is allowed for exploration but blocks release when rights clearance is required. Source origin, permission, consent, likeness, product-truth, synthetic-content disclosure and licensing terms must be recorded as evidence, not inferred from the existence of a file.

An upstream change invalidates only the affected task and dependency descendants. Their prior files and event history remain for audit; unaffected work remains current.

## 9. Independent quality review and release

A review is bound to the exact artifact ID and SHA-256, reviewer identity, producer identity, rubric, dimensions, evidence references, outcome and notes. A producer cannot review its own artifact. A review on stale bytes cannot authorize the current artifact.

The runtime does not impose one global quality score. The brief selects relevant rubrics and may name every required final/package artifact and every source asset whose rights must be cleared. Conflicting PASS and FAIL reviews on the same exact artifact/rubric block release; a single PASS cannot erase a conflicting independent review. Typical rubrics include:

- editorial truth and source quality;
- argument/story clarity and retention;
- humor/naturalness/platform voice;
- visual craft, composition, motion and continuity;
- voice, music, sound design and mix;
- editing, pacing and transitions;
- technical playback/encoding/audio/subtitle QA;
- rights, likeness, provenance and disclosure;
- platform format and packaging.

The built-in FFprobe adapter currently measures stream presence, duration, resolution, frame rate and available stream-duration consistency. Additional FFmpeg/ subtitle analyzers may be added as separately declared, tested adapters for loudness, clipping, black frames or subtitle bounds; do not claim those checks ran unless their receipts exist. No technical tool proves that a film is compelling, funny, emotionally coherent or commercially effective. Human or genuinely independent multimodal review must inspect the actual media when the rubric requires it.

`release-check` verifies the exact current file digest, required independent PASS reviews, rights state and configured release evidence. It records acceptance evidence; it does not publish to a platform. Publication remains a separate authorized action.

## 10. Failure diagnosis and method repair

A material failure record contains the observed symptom, at least two competing root-cause hypotheses, discriminating tests, selected cause, a challenge to the previous method/diagnostic, repair plan, falsifier, rollback and evidence references.

Do not assume every failure needs another prompt, reviewer, role, gate or stage. Distinguish:

- local execution lapse;
- missing/incorrect source or requirement;
- capability/tool limitation;
- weak quality standard or benchmark;
- dependency/coordination defect;
- architecture defect;
- incorrect goal interpretation.

Repair at the causal layer supported by evidence. A failure cannot be marked resolved without independent verification and regression/replay references.

## 11. Learning and method promotion

Learning sources must be explicitly admitted and source-bound. A method candidate records the problem it solves, mechanism, evidence, applicability, counterexamples, failure conditions and replay references.

A candidate remains `CANDIDATE` until there is independent validation evidence and at least one counterexample trial. A successful single project or a model's self-rating does not establish a universal rule. Provider-specific knowledge expires faster than durable storytelling or production principles. Rejected approaches remain recorded with the reason they failed.

## 12. Operational commands

```bash
# create a project from an outcome brief
vga-studio --root ./studio-work init episode-001 --title "Episode 001" --brief examples/technology-explainer.brief.json

# create a dynamic dependency graph
vga-studio --root ./studio-work plan episode-001 examples/technology-explainer.tasks.json

# inspect ready/blocked work
vga-studio --root ./studio-work status episode-001
vga-studio --root ./studio-work tasks episode-001

# atomically claim an agent task, or run registered local tool tasks in parallel
vga-studio --root ./studio-work claim episode-001 --worker researcher-01 --executor agent
vga-studio --root ./studio-work run-ready-tools episode-001 --max-workers 4

# record an artifact-bound independent review
vga-studio --root ./studio-work review episode-001 ARTIFACT_ID --reviewer reviewer-01 --rubric craft --outcome PASS --dimensions review-dimensions.json --evidence frame://01 --evidence frame://02

# inspect current state and durable event history
vga-studio --root ./studio-work audit episode-001
vga-studio --root ./studio-work events episode-001
```

`vga-studio --help` lists brief revision/history, task-contract revision, claim heartbeat, complete, fail, wait-input, decision, failure, resolve-failure, invalidate, reopen, learn and release-check commands. `qa-media` runs the built-in FFprobe measurement adapter against a claimed `technical_measurement` task, writes a digest-bound QA receipt and completes that measurement task. It checks technical properties only; it cannot approve craft, truth, rights or release.

## 13. Migration and compatibility

The existing `vga` CLI and 0.8 Media Business OS remain available for historical Pilot recovery and proven specialized capabilities. They are not the new Studio's controller or task graph. Reuse old modules only through explicit adapters after verifying their current behavior, compatibility, real outputs and failure cases. Do not migrate old fixed stage order or role assignments merely because they exist.

## 14. Known limits of this first standalone runtime

The core supplies durable project governance, DAG scheduling, atomic claims, leases, artifact identity, review evidence, failure records and learning admission. The first local production executor now assembles registered shot assets and audio into a candidate audiovisual master and packages exact delivery/source artifacts. It still does not itself create every shot, provide a universal LLM, NLE, music library, human voice or paid provider credential. Nor does the core itself implement every business-domain object; the Skill coordinates those domain capabilities through explicit adapters and evidence-bound artifacts. The active worker must use the actual available media tools/provider adapters, report capability gaps honestly, and return files into the project workspace. The absence of a provider blocks only the affected operation or triggers an explicitly accepted degradation path; it never fabricates media output.

This boundary is intentional: the orchestration core remains provider-neutral and independently operable instead of pretending a generic task scheduler can create cinematic video by itself.