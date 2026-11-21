# Standalone Video Studio — Product, Method and Runtime Contract

Status: `ACTIVE_CANDIDATE_1.0`
Runtime: `video_studio.engine`
Entry: `STUDIO_ENTRY.md`
CLI: `vga-studio`
Manifest: `video_studio/data/studio_manifest.json`

## 1. Product outcome

Video Production Studio turns an owner's media goal into the exact requested media package and independently checks the resulting bytes. The primary success oracle is the delivered work, not the presence of roles, stages, prompts, diagrams, task counts, adapters or passing tests.

Supported work may include cinematic explainers, technology/business documentaries, engineering demonstrations, news × fictional-video satire, meme and entertainment edits, product/brand films, animation, trailers, tutorials, shorts, long-form videos, social image sets, platform-native derivatives and mixed-media work. No single visual style, runtime, aspect ratio, duration, model, editor or production method is universal.

## 1.1 Optional business-domain scope

Video production is the primary product. A project may attach these workstreams only when the owner's brief establishes a real dependency:

- **MEDIA_GROWTH** — audience/problem research, demand signals, platform strategy, portfolio/series hypotheses, packaging, distribution and audience outcomes.
- **ORIGINAL_DIGITAL_IP** — video-side use and performance of approved original IP. IPOS remains the sole authority for character identity canon, likeness and identity rights.
- **COMMERCIALIZATION** — sponsor/category fit, offer hypotheses, deliverable obligations, product truth, rights scope, disclosure and commercial measurement.

Cross-workstream decisions must be explicit and evidence-bound. These workstreams must not become mandatory gates for an unrelated video. The AI self-media commercialization Program is an optional business workspace, not the default destination for generic video-production requests. Exact project IDs/aliases resume existing work; otherwise create a project-specific media job.

## 2. Authority and governance boundary

- **Owner request and corrections** define the outcome and hard constraints.
- **Project brief** is the current executable outcome contract. Revisions are recorded with old/new digests and a reason.
- **Task graph** owns real execution dependencies and task state.
- **Artifact records** own exact file identity, digest, version, rights and producer lineage.
- **Review records** own artifact-bound evaluation evidence.
- **Event history** is append-only operational history.
- **IPOS** remains the sole authority for original character/identity canon and identity rights.
- **CAOS**, when the active ChatGPT session is CAOS-governed, supplies parent-level decision, execution and independent-acceptance governance externally.

The Video runtime has no CAOS runtime/API dependency, parent task identity or parent lease. This is runtime independence, not permission to bypass active CAOS session governance. Never modify the CAOS repository, branches, files, configuration, pull requests or installed skills during Video work.

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

The graph must be acyclic. Each output name has one producer. Independent nodes are eligible concurrently. A task with missing inputs waits; a task whose dependency fails or becomes stale is blocked. The engine does not force every project through research → script → storyboard → lookdev → generation → rough cut → sound → QA. Those are possible tasks only when the project needs them.

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

## 6. Production strategy and capability boundary

Choose the medium per story beat or shot, not per project. Admissible methods may include real footage, licensed archive, image generation, video generation, image-to-video, 2D/2.5D motion, 3D, procedural animation, kinetic typography, diagrams, code-driven graphics, compositing, practical photography, screen capture, NLE editing, generated voice, human narration, music, sound effects and deliberate silence.

Classify every task as `agent`, `tool`, `human` or `external`. A task declaration is not an installed capability. The agent class is executed by the current agent session or an explicitly connected worker; the local CLI does not auto-spawn LLM workers. Tool tasks require a registered and tested local operation. External tasks require a current capability handshake covering exact input roles, output limits, availability, rights/terms and price. Human tasks require the named human action or review.

Session tools are not persistent repository integrations. If a current ChatGPT session provides image/video/audio generation or editing tools, verify the exact operation for that run, use them only within the owner's cost/rights authorization, and import the actual outputs into the project. Do not infer current availability from a stored model list or vendor feature page.

The cheapest route is not acceptable if it fails the craft floor. Prototype the highest-risk assumption with a 3–12 second near-final sample or a small set of hero shots before full production. Do not execute arbitrary project-supplied Python as a renderer unless a genuine OS/network sandbox and explicit owner authorization exist. A boolean configuration flag is not a sandbox.

## 7. Execution, leases and recovery

The runtime uses SQLite with WAL, foreign keys, busy timeout and `BEGIN IMMEDIATE` for task claims. Each worker receives a unique claim token and time-bounded lease. Heartbeats extend leases. Expired claims are recoverable within the task's retry budget. A worker whose token is no longer current cannot complete or overwrite the task.

The work packet contains only the declared task, acceptance contract, requirements and exact input artifacts/digests. Workers do not peer-chat as an authority mechanism; handoffs occur through artifacts and receipts.

A task completes only when all declared output names are supplied and each output is a real regular file inside the project workspace. The runtime computes SHA-256 and size itself. Registered artifact paths are immutable; a new take or revision gets a new path and version. Files outside the project must first be imported as source assets.

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

# atomically claim the next ready task
vga-studio --root ./studio-work claim episode-001 --worker researcher-01 --lease-seconds 900

# record an artifact-bound independent review
vga-studio --root ./studio-work review episode-001 ARTIFACT_ID --reviewer reviewer-01 --rubric craft --outcome PASS --dimensions review-dimensions.json --evidence frame://01 --evidence frame://02

# inspect current state and durable event history
vga-studio --root ./studio-work audit episode-001
vga-studio --root ./studio-work events episode-001
```

`vga-studio --help` lists brief revision/history, task-contract revision, claim heartbeat, complete, fail, wait-input, decision, failure, resolve-failure, invalidate, reopen, learn and release-check commands. `qa-media` runs the built-in FFprobe measurement adapter against a claimed `technical_measurement` task, writes a digest-bound QA receipt and completes that measurement task. It checks technical properties only; it cannot approve craft, truth, rights or release.

## 13. Migration and compatibility

The existing `vga` CLI and 0.8 Media Business OS remain available for historical Pilot recovery and proven specialized capabilities. They are not the new Studio's controller or task graph. Reuse old modules only through explicit adapters after verifying their current behavior, compatibility, real outputs and failure cases. Do not migrate old fixed stage order or role assignments merely because they exist.

## 14. Current implementation limits and release status

The repository is in `REBUILD_IN_PROGRESS`. The standalone control plane provides durable briefs, dynamic DAGs, atomic claims, leases, immutable artifact digests, review records, release checks, failure records and learning receipts. The built-in FFprobe path provides technical measurement only. The new image-set module validates concept/prompt diversity and compiles independent prompts; it does not generate images or prove visual diversity in the resulting pixels.

The current mainline does not yet provide a complete registered image/video/audio provider executor, general scene/character renderer, integrated timeline/audio production pipeline, automated local-tool worker pool, recursive rights-evidence lineage validation or full output-level end-to-end acceptance. Connected ChatGPT tools, when available, are session capabilities—not persistent repository integrations. The system must report these gaps honestly and must not claim production readiness until real image-set and video dogfood deliverables pass the acceptance gates in the rebuild decision record.

The 0.8 Media Business OS and specialized domain modules remain compatibility/capability sources only. Reuse them selectively through reviewed, tested, evidence-bound adapters; do not restore the legacy fixed-stage controller as the new execution architecture.

