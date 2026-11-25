# Social Media Studio — Product, Method and Runtime Contract

Status: `ACTIVE_CANDIDATE_1.0`
Runtime: `social_media_studio.engine`
Entry: `STUDIO_ENTRY.md`
CLI: `sms-studio`
Manifest: `social_media_studio/data/studio_manifest.json`

## 1. Product outcome

Social Media Studio turns the owner's specific content goal—including independent long/short text, visuals, platform packaging, media repair and original moving media—into the requested output and applicable release materials. Its primary success oracle is the delivered work, not the presence of roles, stages, prompts, diagrams, task counts or passing tests.

Supported work may include cinematic explainers, technology/business documentaries, engineering demonstrations, news × fictional-video satire, meme and entertainment edits, product/brand films, animation, trailers, tutorials, shorts, long-form videos, platform-native derivatives and mixed-media work.

No single visual style, runtime, aspect ratio, duration, model, editor or production method is universal.

## 1.1 Optional business-domain scope

Business workstreams are optional objectives, not the full set of professional content domains. Social Media Studio includes the nested Original Identity/IPOS specialist for permanent character and creator identity design. Its installed Skill and private canonical state are separately maintained, while Social Media Studio owns only verified downstream bundle consumption. Ordinary temporary avatars remain general visual craft. The Studio is the **sole active control plane for durable Social Media Studio work**; for bounded direct conversational work no persistent controller is required. This does not give the historical 0.8 runtime authority or turn the Studio into merely a clip renderer. A project graph may cover one workstream or connect several:

- **MEDIA_GROWTH** — audience/problem research, demand signals, platform strategy, portfolio and series hypotheses, packaging, distribution, retention and audience outcomes.
- **ORIGINAL_DIGITAL_IP** — video-side use of approved IP, recognition/performance evidence, character/asset usage strategy and licensing-use value. Canon, likeness and identity rights remain owned by IPOS.
- **COMMERCIALIZATION** — sponsor/category fit, offer hypotheses, deliverable obligations, product-truth requirements, rights scope, measurement and commercial outcomes.
- **PRODUCTION_SYSTEM** — editorial research and claims, story/shot design, assets/takes, generation, compositing, edit, sound, QA and release.

Cross-workstream decisions must be explicit. Audience evidence may change a series hypothesis; IP performance may change packaging or licensing strategy; sponsor obligations may change format and product-asset requirements; production cost, failure and reuse evidence may change future portfolio allocation. Editorial truth, rights and owner authority remain hard constraints. Do not optimize one proxy such as views, CTR, cinematic quality, AI-video percentage or lowest credit cost.

The `social_media_studio` engine is the sole durable project control plane: briefs, dynamic task DAGs, leases, artifacts, decisions, reviews, failures and learning receipts. Program/Series/Episode/Shot/Timeline, continuity, provider routing, business metrics and IP identity semantics remain self-media-owned domain logic and are exposed through the single tested adapter boundary. The fixed-stage `StudioOrchestrator` is not an active controller. No second task scheduler or parent workflow is permitted.

The Studio runtime exposes those explicit adapters through `sms-studio run-adapter`: EditorialPlan validation, ShotContract materialization/validation, IPOS bundle inspection/import, exact-version IPOS shot binding and canon continuity snapshot/link creation, MediaGraph bootstrap, TimelineSpec validation, shot continuity assessment, operation-specific shot routing, business outcome metrics, supplementary loudness/silence QA and deterministic programmatic-graphics rendering. Each adapter reads only declared, digest-verified task inputs and registers exact outputs through the Studio artifact transaction. The graphic renderer creates a silent candidate only; a separate sound task, canonical technical QA, human review and release check remain required.

This is not a claim that every external provider is connected. The repository currently has no trusted external generative-video executor registered. Provider generation remains a tool/session capability operation; the router can select only from supplied, current, evidence-backed engine profiles. The runtime does not invent availability or invoke paid providers implicitly.


For a durable owner task, give `requirements.decision_id` an exact unique ID when planning; after current inputs and decision evidence are available, use `sms-studio decision PROJECT RECEIPT.json` with that `decision_id` and `task_id` plus the existing competing-cause/alternative fields. The engine derives the binding from actual current brief, task contract and input artifact bytes. Unbound/stale branches cannot be claimed or completed; unrelated admitted branches may proceed. Revise a stale task to a new decision ID and reopen it after re-investigation. This local check is not CAOS activation, verified external research, a permission grant, or semantic acceptance. Direct non-task session actions still require CAOS governance and appropriate independent evidence.

## 1.2 Architecture: independent views

The canonical manifest defines authority, optional business domains, professional capabilities, roles, optional media containment, cognition dependency, knowledge, execution resources, acceptance and per-demand execution DAG. Professional capability classification is distinct from business workstreams, media object containment, roles, reusable knowledge, cognition dependencies and task execution. Discover exact groups with `sms-studio capabilities [--group GROUP]`; the output binds the catalog to registered adapters and local operations, discloses missing effects and does not select a task, authorize execution or certify quality. For current owner work, CAOS recursively governs every material choice at every organizational level, including the choice of professional method, reviewer, tool and verification. No group is a compulsory stage or permanent worker. Apply independent domain and overall owner acceptance separately. New evidence may reopen the earliest contradicted premise without invalidating unrelated branches. The existing engine is the only scheduler; use direct session capability for nonpersistent simple work where appropriate. None is a mandatory stage sequence. CAOS owns parent cognition, Social Media Studio owns domain execution; SQLite is the only self-media task ledger. Business groups are reusable responsibilities, not permanently running task instances. Group feedback is an evidence-triggered new decision/revision, not a cycle inside one DAG. The generic feedback relations are in `social_media_studio/data/business_feedback.json`.

Continuous responsibilities are evaluated at each applicable decision/effect: complete owner goal and corrections, CAOS recursive governance, aesthetic and narrative coherence, audience/communication value, rights/truth, exact context and version, independently observed quality, and learning/re-entry. Aesthetic direction remains in scope from concept to final review and upstream revisions; it is not a standalone gate or a task to mark done. Unknowns reopen the earliest affected decision and only invalidate dependent work. There is no default project or default task plan. Old instances are retired; fixtures are for tests only.

## 2. Authority and independence

- **Owner request and corrections** define the goal and constraints.
- **Project brief** is the current executable outcome contract. Revisions are recorded in the append-only event history with old/new digests and reason.
- **Decision receipts** explain material choices and their falsifiers; they do not override owner requirements.
- **Task graph** owns execution dependencies and task state.
- **Artifact records** own exact file identity, digest, version, rights and producer lineage.
- **Review records** own artifact-bound evaluation evidence.
- **Event log** is append-only operational history.
- **IPOS** is an internal professional identity-design bounded context of Social Media Studio. Its existing private canon and owner approval are separately custodied; approved bundles may be imported into downstream Video only with exact provenance.

CAOS governs every owner-facing self-media conversation, decision and action, including revisions, retrieval, method selection, execution and final acceptance. Social Media Studio owns domain execution, project/task state and artifact records. The runtime has no CAOS imports, API, parent task identity or parent lease; this runtime boundary does not waive the active session's CAOS governance. The fixed-stage controller is not loaded by `sms-studio`. specialist content-domain modules are imported only through `social_media_studio.adapters` when a task declares a supported adapter.

## 3. Goal recovery and requirement governance

**Choose the execution surface, not a default workflow.** Recover the full current goal and apply CAOS recursively in either surface. A bounded conversational text, image-planning, critique or simple edit task may be performed with actual available session tools and direct outcome checks; do not create a project or DAG solely to simulate governance. Use the durable Studio ledger when persistence, artifact lineage, parallel dispatch, repeatable tooling or recovery materially requires it. A continuation resolves the exact current workspace identity from authorized evidence, not recency or retired history. The execution surface does not grant authorization or waive any applicable quality, rights, truth or independent acceptance requirement.

Every durable project brief should record the applicable dimensions:

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

## 6. Production strategy

Choose the medium per story beat or shot, not per project. Admissible methods may include real footage, licensed archive, image generation, video generation, image-to-video, 3D, procedural animation, kinetic typography, diagrams, code-driven graphics, compositing, practical photography, screen capture, NLE editing, generated voice, human narration, music, sound effects and deliberate silence.

A hybrid film may use different methods for different shots. The most expensive engine is not automatically best; the cheapest engine is not acceptable if it misses the required craft ceiling. Tool feature declarations are not proof of the exact operation combination, current availability, rights or output quality.

For high-risk creative assumptions, build a 3–12 second near-final sample or a small set of hero shots before full production. The sample should represent the final visual language, camera/motion, material quality, typography, sound and transition where relevant. A technical proof that a tool runs is not a quality proof.

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

The built-in FFmpeg/FFprobe adapter measures stream presence, stream-duration agreement, complete video/audio decode, black-frame segments and audio true peak. When the brief specifies them, it also checks duration range, resolution and frame rate. Subtitle geometry, caption safe-area compliance, integrated loudness, visual continuity and editorial craft require separate declared analyzers or human review; do not claim those checks ran unless their receipts exist. No technical tool proves that a film is compelling, funny, emotionally coherent or commercially effective. Human or genuinely independent multimodal review must inspect the actual media when the rubric requires it.

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

Repair at the causal layer supported by evidence. A failure cannot be marked resolved by opaque URI strings or caller-declared PASS alone. `verification_refs` and `regression_refs` must each contain distinct exact artifact IDs registered in the current project. Every referenced artifact must be current, its bytes must match its recorded SHA-256, and it must have an exact-digest PASS review under `failure-verification` or `failure-regression`, respectively. Each review must cite separate current artifact IDs whose bytes also match their recorded digests. Import external verification reports, regression reports and the evidence they inspect as artifacts before resolving. The engine records the artifact digests and review IDs it checked. Reviewer/producer separation is structural evidence only, not cryptographic identity proof or semantic acceptance; CAOS still performs the independent owner-level acceptance.

## 11. Learning and method promotion

Learning sources must be explicitly admitted and source-bound. A method candidate records the problem it solves, mechanism, evidence, applicability, counterexamples, failure conditions and replay references.

A candidate remains `CANDIDATE` until there is independent validation evidence and at least one counterexample trial. A successful single project or a model's self-rating does not establish a universal rule. Provider-specific knowledge expires faster than durable storytelling or production principles. Rejected approaches remain recorded with the reason they failed.

## 12. Hard release gates and provenance

The task graph is a scheduler, not the authority that decides whether a deliverable may be released. Release policy is declared in the owner brief and enforced against exact registered artifacts.

### Artifact lineage and source changes

When a task completes, the runtime records each declared input artifact ID and SHA-256 as an immutable `DERIVED_FROM` edge for every output. The lineage is recursive. The release check verifies all bytes and recorded parent digests. Re-importing a new version of an existing source name marks the prior version stale and invalidates every task that declared or consumed it, plus dependency descendants; old outputs and receipts remain historical evidence. Workers must reopen and regenerate affected tasks rather than reusing stale outputs.

### Rights and provenance

For public release, the final deliverable and every used media asset in its lineage must have one of `OWNED`, `AUTHORIZED`, `LICENSED` or `PUBLIC_DOMAIN`. `UNKNOWN` is fail-closed. By default, media artifacts also require non-empty `metadata.rights_evidence_refs`; each reference must resolve to a registered current artifact name/ID or an explicit HTTP(S) source URL. Briefs may name mandatory source assets and evidence artifacts. Required source assets must actually occur in the final artifact's recorded lineage, not merely exist elsewhere in the project.

The rights status field is a declaration backed by evidence, not an automatic legal opinion. Likeness, voice, music, font, stock footage, product truth, territory, duration, paid-media and derivative-use scope still require a competent human review.

### Technical media QA

A video artifact automatically requires a current technical QA receipt at release, even if the brief forgets to set `require_technical_qa`. A project can also explicitly require QA for a non-video output. The receipt must identify the exact target artifact ID and SHA-256, contain a recognized `ffmpeg-ffprobe-v1.0` checker identity, have `hard_pass=true`, no hard failures, and PASS for every mandatory check.

Mandatory checks are:

- `video_stream` — a video stream exists;
- `stream_duration_match` — measurable stream durations agree within the declared tolerance;
- `true_peak` — audio true peak is measured and stays within the configured ceiling;
- `black_frames` — black segments are detected and remain within the configured maximum;
- `full_decode` — FFmpeg can decode the complete selected video/audio streams without errors.

The brief may add mandatory checks such as duration range, resolution and frame rate; it cannot remove the five core checks. Missing FFmpeg/FFprobe, timeout, malformed reports, unavailable measurements or digest mismatch block release. The QA adapter does not certify editorial truth, craft, rights, continuity or audience response.

### Independent reviews and Red Team

A review is bound to the exact artifact digest and must not be written by its producer. A brief can require reviewer kind, execution mode, blind review, inspected digest, context ID, score floors and reviewer quorum. Human cold-read contracts require `reviewer_kind=HUMAN`, `execution_mode=INDEPENDENT_COLD_READ`, `blind_review=true`, a matching inspected digest and a context ID.

The Red Team contract can require at least three concrete findings. Each finding must contain a description, evidence reference, severity and disposition. When `require_resolvable_evidence_refs` is enabled, both review-level evidence refs and every finding's evidence ref must resolve to a current registered artifact ID/name; a free-form URI is not accepted as proof. A PASS with unresolved CRITICAL/HIGH findings is rejected. Findings are not decorative checklist entries; unresolved material risks block release.

These reviewer attributes are recorded as attestations. The runtime can validate their structure and consistency but cannot cryptographically prove that a named person actually performed the review or remained blind to other verdicts. Do not describe self-attested metadata as cryptographic independence.

### Evidence and publication boundary

`required_evidence_artifact_names` requires registered, current, digest-verified artifacts of an allowed evidence/document/report/decision/timeline/domain-state kind. `required_artifact_names` requires every declared deliverable. `required_asset_names` requires source assets to be in final lineage and rights-cleared. String-only evidence references are descriptive only and cannot satisfy machine-verified evidence requirements; use registered artifact names/IDs.

A successful release check marks the exact artifact ACCEPTED; it does not upload, publish, schedule or spend money. Publication remains a separate owner-authorized action. No CLI option can override a hard rights requirement in the owner brief.

### Review and QA CLI

Review dimensions and scores are supplied as JSON. Independence metadata is supplied separately:

```bash
sms-studio review PROJECT ARTIFACT_ID \
  --reviewer human-reviewer-01 --rubric human-cold-read --outcome PASS \
  --dimensions review-scores.json --attestation review-attestation.json \
  --evidence frame://00:00:02 --notes "Blind cold read of exact final digest"
```

The attestation JSON should identify `reviewer_kind`, `execution_mode`, `blind_review`, `inspected_artifact_digest` and `context_id`. Red Team review dimensions should include a `findings` array with at least three evidence-backed findings when the brief requires it.

## 13. Operational commands

### 13.1 Task-neutral intake and planning

For each new durable demand, use `sms-studio intake REQUEST.json` with a JSON object containing the owner's exact goal and mode NEW. For continuation provide mode RESUME and the exact workspace project_id. No default project, previous brief, preset tasks, IP or source media are selected. A retired repository identity is not resumable. The route is a mechanical projection; CAOS session governance and independently verified outcomes remain separate.

Plan the actual deliverable(s) and dependencies using the applicable capability contracts; a one-step task is valid. Initialize a fresh owner project with `init PROJECT --brief BRIEF.json --owner-task`; `requirements.deliverable_refs` on each task must reference exact current brief deliverable names. The local marker is an epoch/identity check, never evidence of cognition. Mechanical offline regression fixtures deliberately do not carry that marker. Owner project creation requires explicit `--owner-task`. `--offline-fixture` requires an explicit dedicated root that is empty on first initialization; the CLI writes a root-bound `.sms-offline-fixture.json` marker. Fixture mode cannot adopt a pre-existing unmarked workspace, and owner mode cannot open a fixture-marked root. The marker prevents accidental mode mixing; it is not an authentication boundary. Only a current owner requirement or verified input can add owner scope. Examples below are isolated regression fixtures, not task templates or current work.

### 13.2 Episode-specific example

```bash
# create a project from an outcome brief
sms-studio --offline-fixture --root ./studio-work init episode-001 --title "Episode 001" --brief examples/technology-explainer.brief.json

# create a dynamic dependency graph
sms-studio --offline-fixture --root ./studio-work plan episode-001 examples/technology-explainer.tasks.json

# inspect ready/blocked work
sms-studio --offline-fixture --root ./studio-work status episode-001
sms-studio --offline-fixture --root ./studio-work tasks episode-001

# atomically claim the next ready task
sms-studio --offline-fixture --root ./studio-work claim episode-001 --worker researcher-01 --lease-seconds 900

# record an artifact-bound independent review
sms-studio --offline-fixture --root ./studio-work review episode-001 ARTIFACT_ID --reviewer reviewer-01 --rubric craft --outcome PASS --dimensions review-dimensions.json --evidence frame://01 --evidence frame://02

# inspect current state and durable event history
sms-studio --offline-fixture --root ./studio-work audit episode-001
sms-studio --offline-fixture --root ./studio-work events episode-001
```

`sms-studio --help` lists brief revision/history, task-contract revision, claim heartbeat, complete, fail, wait-input, decision, failure, resolve-failure, invalidate, reopen, learn and release-check commands. `qa-media` runs the built-in FFmpeg/FFprobe measurement adapter against a claimed `technical_measurement` task, writes a digest-bound QA receipt and completes that measurement task. It checks technical properties only; it cannot approve craft, truth, rights or release.

`run-adapter` executes a task's declared `requirements.domain_adapter` against its registered inputs and completes the task with immutable output artifacts. Example task requirement:

```json
{
  "domain_adapter": {
    "name": "programmatic_graphic_render",
    "editorial_plan_input": "editorial-plan",
    "shot_contract_input": "shot-contract",
    "graphic_spec_input": "graphic-spec",
    "font_input": "font-asset",
    "rights_evidence_input": "rights-clearance",
    "video_output": "graphic-candidate",
    "receipt_output": "graphic-render-receipt"
  }
}
```

Run it only after claiming the task:

```bash
sms-studio run-adapter PROJECT TASK_ID --worker local-renderer --token CLAIM_TOKEN
```

The adapter verifies the ShotContract against the exact EditorialPlan, requires the font and rights evidence as declared inputs, and emits a candidate plus receipt. It does not promote the asset. A later `qa-media` task must bind canonical FFmpeg/FFprobe QA to the registered candidate artifact ID and digest.


### Standalone adapter proof

The repository includes `examples/standalone-domain-adapters.brief.json` and `examples/standalone-domain-adapters.tasks.json`. They demonstrate a real, deterministic local render rather than a mocked task completion:

1. An agent authors an EditorialPlan and GraphicSpec.
2. The `editorial_plan_validate` adapter validates claims, beats and shots.
3. The `shot_contract_materialize` adapter derives a ShotContract from the exact plan.
4. The `programmatic_graphic_render` adapter checks the plan binding, font input and rights evidence, then writes a silent MP4 candidate and render receipt.
5. The `qa-media` command runs the canonical digest-bound FFmpeg/FFprobe checks against that registered candidate.

Import a licensed font and its rights evidence before claiming the renderer task:

```bash
sms-studio --offline-fixture --root ./studio-work init adapter-demo --title "Standalone adapter demo" --brief examples/standalone-domain-adapters.brief.json
sms-studio --offline-fixture --root ./studio-work plan adapter-demo examples/standalone-domain-adapters.tasks.json
sms-studio --offline-fixture --root ./studio-work import-asset adapter-demo rights-clearance ./font-license-evidence.txt --kind document --media-type text/plain --rights-status OWNED
sms-studio --offline-fixture --root ./studio-work import-asset adapter-demo font-asset ./DejaVuSans.ttf --kind font --media-type font/ttf --rights-status LICENSED --metadata examples/adapter-demo-font.metadata.json
```

The example is an adapter integration proof, not a claim that a title card alone is a finished film or that external generative-video providers are connected.

## 14. Single runtime and governance boundary

`STUDIO_ENTRY.md` is the only self-media startup entry. `sms-studio` is the only installed CLI and `social_media_studio.engine.StudioEngine` is the only active project runtime. CAOS parent governance is applied at the ChatGPT session level; the Social Media Studio runtime does not create a second parent controller or make runtime/API calls to CAOS. specialist content-domain logic is accessed only through the Studio adapter registry.

## 15. Known limits of the current runtime

The core supplies durable project governance, DAG scheduling, worker leases, artifact identity, review evidence, failure records and learning admission. It does not itself contain a universal LLM, image/video generation model, NLE, music library or paid provider credential. Nor does the core itself implement every business-domain object; the Skill coordinates those domain capabilities through explicit adapters and evidence-bound artifacts. The active worker must use the actual available media tools/provider adapters, report capability gaps honestly, and return files into the project workspace. The absence of a provider blocks only the affected operation or triggers an explicitly accepted degradation path; it never fabricates media output.

This boundary is intentional: the orchestration core remains provider-neutral and independently operable instead of pretending a generic task scheduler can create cinematic video by itself.

## Current bounded work-cycle and source evidence boundary

`sms-studio work-cycle PROJECT --plan-only` exposes current parallel-ready lanes, decision blockers and exact-input handoff packets. It does not claim tasks or exercise agent, human or external execution authority. The execution form runs only explicitly registered and admitted local tool operations in bounded DAG rounds; the worker pool does not repeatedly run the same failed tool in one invocation. Input SHA mismatches block only affected branches. `source_evidence_audit` is a deterministic research execution operation over registered UTF-8 sources with immutable digests. Its quote-coverage receipt is candidate evidence, not external fact verification, independent acceptance or publication authority.

Current new owner work uses `SOCIAL_MEDIA_OWNER_SCOPE_V2_20261125`. Previously current owner projects from the prior product scope require explicit `migrate-scope`; the upgrade retains existing events and assets, revokes live claims and supersedes old decisions, without granting any old archive instance current authority. CAOS remains external parent governance; this runtime cannot prove that ChatGPT/Codex selected or performed the parent's native Skill.
