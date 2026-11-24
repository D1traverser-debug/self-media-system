# Social Media Studio — Architecture Contract v2 (DESIGN CANDIDATE)

**Status:** ARCHITECTURE_CANDIDATE / NOT_PROMOTED / NO_RUNTIME_AUTHORITY  
**Owner:** SOCIAL_MEDIA_STUDIO (self-media system identity)  
**Frozen implementation baseline:** PR #40, commit 1cbc3acf0491ecaa297576372f80163d8c255606; 370-test exact-head CI 45416359779 PASS.  
**Governance authority:** owner intent + corrections; CAOS parent Skill and private owner original, read-only; child domain decisions and execution remain self-media-owned.  
**Identity subsystem:** IPOS is a professional identity-design bounded context WITHIN the Social Media Studio product architecture; its current Skill/private Library source and permanent approved canon have independent source custody. No automatic state duplication.  
**Scope:** design all architecture dimensions before runtime implementation; no change to CAOS source; no old task reactivation, automatic publication or provider authorization.

## A. Product boundary and invariants

The product is a **general digital content creation, transformation and multi-platform delivery capability**, not a mandatory video production pipeline. The historical repository name is an address, not a domain restriction. Accept one-line text, X long-form articles, Chinese/English and other-language platform titles/descriptions/tags/cover copy, images, aspect variants, avatars, prompt development, visual edits, brief video trims, restoration, audio preservation, QA, original audiovisual work, audience/growth and optional commercial work. A request may activate none, one or many of these capabilities. Every demand is interpreted from the current owner goal, not a previous project or title.

Non-negotiable architecture properties:
1. **One goal authority:** the owner's original demand plus ordered corrections; an example, past project, viral trend or prior assistant plan does not acquire authority.
2. **One parent cognition authority:** read-only CAOS guidance across all levels and every substantive decision/effect, including routing, diagnosis, method research, tool choice, code change, review and learning. The Social Media Studio runtime cannot certify native ChatGPT Skill selection or mental quality. No copied CAOS Host.
3. **One Social Media Studio durable task ledger:** StudioEngine's current per-project SQLite and append-only event history; no second planner/controller for the same project. Direct session work needs no artificial project.
4. **Independent bounded domains:** business objectives, professional craft, optional media containment, temporary work groups, methods, task DAG, cognition dependencies, artifact lineage and post-release business feedback are NOT one graph.
5. **Only current scope:** old project IDs, old 50-task graph, prior IP goals and other historical work orders are RETIRED_EVIDENCE_ONLY; original files remain traceable and never auto-select work.
6. **Source-before-authority:** exact source owner, ID, version/commit or byte hash, applicability, and active/obsolete lifecycle; snapshots and library filenames do not prove current truth.
7. **No fictitious execution:** discover available exact operations and constraints; a declared capability, agent role, prompt or adapter does not imply successful generation or business quality.
8. **Typed artifact-specific acceptance:** structural execution success, technical media integrity, editorial/aesthetic quality, rights/truth and owner outcome are distinct proofs. Avoid universal numeric aesthetic scores.
9. **Failure can reopen ancestors:** a bad output can invalidate the prior narrative, source, goal interpretation, method or architecture; only actual dependent conclusions and tasks become stale.
10. **No unauthorized effects:** paid provider, release, real posting, canon mutation, permanent deletion and account changes need their own authorized effect boundary.
11. **Architectural reversibility:** versioned contracts, compatibility shims for read-only historical fixtures, safe rollback and no destructive migration of user assets.

## B. Competing diagnoses and architecture choice

**H1 — missing orchestration framework.** Contradicted by one SQLite engine with atomic claims, task DAG, leases, artifact lineage and a real concurrent local tool pool. Replacing all control logic first risks losing verified capabilities.

**H2 — only prompt/policy language is inadequate.** Partly supported by repeated CAOS execution drift, but not the sole cause; both capability and authority directories contain stale assumptions and the local engine only checks limited decision/form contracts.

**H3 — ontology conflation.** Strongly supported: existing four workstreams describe an integrated growth program; historically mandatory video QA/lookdev contracts don't fit short copy or image tasks; capability profiles contained legacy controller invocations. Address the shared domain boundary, not just prompt wording.

**H4 — poor creative tools alone.** Insufficient: poor originals also reflect concept/visual narrative/quality oracle failures. New models without upstream method/acceptance redesign would not cure these.

**H5 — all tasks need a multi-agent graph.** Falsified by simple copy and local edits. A graph is warranted only when declared dependencies, persistent state, cross-actor handoffs, repeatability or costly risks require it.

Alternatives:
- A. Rebuild a monolithic CAOS+Social Media Studio all-purpose controller: reject duplicate authority, excess coupling and unverifiable native enforcement.
- B. Split professional teams into permanent microservices/agents: defer; introduces distributed task truth and gratuitous chat/handoff overhead before real demand.
- C. Keep the current video/business ontology and add handlers to each exception: reject; perpetuates fixed workflow and low-quality creative assumptions.
- D. **Selected conditional design:** a *modular domain-centered core with ports/adapters*, one optional durable engine, independent domain contracts, on-demand specialist composition, and CAOS governing actual ChatGPT interaction. Reuse the proven engine/asset/QA modules; adapt/replace overfit domain and policy interfaces; remove obsolete active authorities without deleting evidence.
- E. Replace the durable engine with LangGraph/Temporal/Agent SDK immediately: not justified; these implement particular persistence/agent/tool boundaries, not unconditionally better owner outcome nor native ChatGPT hard intercept.

**Pre-action rechallenge:** A valid architecture must pass tiny text/no-ledger, source-audio-copy, bilingual packaging, single image, real original video, owner revision during parallel execution, and untrusted provider results without copying a fixed production stage. If not, reopen the domain boundaries before changing runtime code.

Primary comparisons (mechanisms, not mandates):
- AWS hexagonal/DDD: bounded context owns its contracts, low-level provider or database adapters depend inward, not vice versa: https://docs.aws.amazon.com/prescriptive-guidance/latest/hexagonal-architectures/overview.html
- LangGraph StateGraph: conditional edges and checkpoints are useful if chosen as an explicit execution substrate; node re-execution requires idempotent side-effects: https://github.com/langchain-ai/langgraph/blob/main/libs/langgraph/langgraph/graph/state.py and https://docs.langchain.com/oss/python/langgraph/graph-api
- OpenAI Agents SDK guardrail source: function tool guardrails do not cover handoffs, hosted/built-in tools or native ChatGPT tools: https://github.com/openai/openai-agents-python/blob/main/src/agents/guardrail.py and https://openai.github.io/openai-agents-python/guardrails/
- Temporal workflow versioning: persistent action history requires compatible code evolution; copying a framework name does not solve creative quality: https://docs.temporal.io/develop/python/workflows#workflow-versioning (reference path may move; research again before implementation).
- Local original implementation: social_media_studio/engine.py, scope.py, adapters.py, production/{registry,worker_pool,ffmpeg_assembler}.py, social_media_studio/legacy/{editorial_packaging,roles,quality-rubric}. All verified against the frozen baseline, with limits noted below.

## C. Multiple architectural VIEWS (never present as one sequential chart)

### C1. Authority and responsibility
- USER: original goal, constraints, preferences, effect authorization, owner acceptance, corrections.
- CAOS parent: recurring, recursively re-enterable cognitive and execution governance, root-cause diagnosis, source qualification, method challenge, independent overall goal assessment. **Read-only source; no child state ownership.** Native first-mile activation NOT_TESTED.
- CONTENT STUDIO domain: demands, deliverables, craft judgement, planning, local evidence, asset custody, quality/acceptance and optional platform distribution preparation.
- ORIGINAL_IDENTITY / IPOS: the nested specialist context of Social Media Studio for durable creator identity design; real IPOS workflow and canonical state are separately custodied. Social Media Studio can import an owner-approved versioned bundle, not rewrite canon. One-off avatars do not imply IPOS involvement.
- PROVIDER/PLATFORM: actual operations and state, available only through current checked interfaces, not inferred from documentation.
- INDEPENDENT REVIEWER: distinct actor/context where required, with actual artifact readback; an arbitrary reviewer string is not proof of independence.

The existing L0–L6 labels are **responsibility scopes**, never an execution ordering. CAOS crosses every applicable scope, including itself being challenged as a method and the adequacy of its evidence. Child authority is not a grant from a parent configuration string.

### C2. Product bounded contexts
1. **Demand & Portfolio** — current goal, correction sequence, typed deliverables, versioned acceptance, platforms/locales/constraints, optional program context; owns no generated media.
2. **Research & Understanding** — source media and text, transcription/scene or claim understanding, evidence/fact provenance, intellectual context, epistemic uncertainty.
3. **Editorial & Language** — argument, structure, original viewpoint, narrative, long-form article, concise copy, jokes, natural Chinese/English, translation/localization.
4. **Visual Craft** — composition, visual hierarchy, art direction, cover/portrait, prompt specification, revision, image generation/edit interfaces and temporary characters.
5. **Original Identity / IPOS** — nested durable creator and character design, identity research, design, owner approval, versioned canon, and media continuity; its current Skill and private Library remain identity source authority.
6. **Motion, Sound & Media Operations** — video concept/shot planning, rendering, editing, clips, crop/reframe, enhancement, restoration, strict audio handling, subtitles.
7. **Platform Packaging & Growth** — platform-specific variant, title/description/tags/cover copy, publication specifications, packaging hypotheses, analytics and experimental learning.
8. **Evidence, Asset & Knowledge** — immutable source/output versions, lineage, rights, knowledge status, index, search, import/transfer/invalidation, durable episodes.
9. **Planning, Execution & Effect** — direct mode or existing StudioEngine, dynamic task dependencies, workers, leases, idempotency, actual tool ports and authorization.
10. **Quality & Independent Acceptance** — typed oracles, technical and craft reviews, owner-goal evaluation, release/admission separation, failure re-entry.

These are **bounded responsibility contexts**, not nine servers, nine compulsory phases or nine permanent workers. A one-sentence task may require only Demand, Editorial, relevant Quality and direct outcome verification.

### C3. Orthogonal graphs
- **Cognition/justification graph:** question → hypotheses/alternatives → sourced decision → dependent conclusions/effects; can cycle via falsification/research. CAOS parent governs; Social Media Studio stores local evidence for self-media effects. This is NOT the task DAG.
- **Work dependency graph:** finite DAG of actual executable tasks, explicit inputs/outputs, readiness and concurrency. Revision creates a new generation; cycles occur between generations, not within one DAG.
- **Composition/containment:** Article→Section→Paragraph, Campaign→Post/Variant, Video→Sequence→Shot→Take as applicable. Do not impose the full Program→Episode→Take hierarchy on an image or social caption.
- **Artifact provenance DAG:** source version/byte digest → transformations → output variants → review receipts. Integrity and rights follow exact dependent edges.
- **Knowledge dependency graph:** source/method versions → claims, decisions and tasks they justified; source change invalidates affected active claims, not all history.
- **Business feedback graph:** published evidence/outcome → hypothesis revision → next demand; never auto-post or create an endless loop.

Each graph has its own key, lifecycle, mutation owner and query interface. Cross-graph relations use explicit typed references; no magic task ID equivalence.

### C4. Organization and professional roles
Persistent resources: craft capability specifications, methods, quality standards, provider contracts, knowledge assets and source provenance.
Ephemeral demand-scoped responsibilities: owner-facing producer/brief owner; a relevant researcher, writer, art director, editor, technical operator, platform specialist and independent critic *only if materially justified by craft/tool/context/evidence separation*. These are **responsibility assignments**, not guaranteed concurrent agents.
Coordination patterns selected by demand: direct single actor; consultative; competing concepts; bounded critique/revision; fan-out/fan-in; independent review; authorized adjudication. A model reviewing its own artifact under a new title is not independent verification. Requirements and handoffs are artifact/evidence mediated, bounded and versioned, with an explicit decision owner.

## D. Canonical semantic object model

At minimum establish stable **type and identity** distinctions:
- DemandID / DemandRevisionID: owner goal + ordered corrections, provenance, hard constraints, preferences, prohibitions, assumptions, unknowns, full business outcome oracle.
- DeliverableID / DeliverableType / DeliverableRevision: exactly requested output, independent contract. Types: SHORT_COPY, LONG_ARTICLE, PLATFORM_PACKAGE, PROMPT_SPEC, STATIC_IMAGE, MULTI_ASPECT_IMAGE_SET, MEDIA_TRANSFORM, ORIGINAL_VIDEO, IDENTITY_ASSET, ANALYSIS_REPORT, plus extensible typed families; no default video final.
- VariantID: Locale×Platform×MediaShape×AspectRatio×DistributionChannel where applicable. A change in one dimension must not silently mutate others. Fields can be absent if irrelevant.
- ContentIntentID: core semantic promise/story/claim/mood/value; shared across variants without forcing identical surface wording.
- EvidenceClaimID: source owner, URI/file ID, exact revision/digest, claim scope, confidence and fact/fiction status.
- DecisionID + revision: question, applicable goal & version, competing explanations/alternatives, discrimination/research, selected action, falsifier, rollback, authority, dependencies, stale state and evidence. Local structurally bound records are not proof of native CAOS cognition.
- MethodID + version: applicability, counterexamples, failure conditions, reference implementation, observed efficacy, verification tier and lifecycle.
- CapabilityID + operation: semantic operation, input/output types, required effects, tool/provider availability, permissions, assurance ceiling, constraints, quality evidence and fallback.
- ExecutionTaskID + TaskRevision: actual declared dependencies, producer, input refs, output refs, risk/budget, current decision binding, lease, retry/idempotency key, timeouts, permission and outcome test.
- ArtifactID + ArtifactVersion + digest: actual owner-custodied bytes or verified provider object, media type, rights/provenance, transformations, expected variant and revision, independence of source and derivative.
- ReviewID: independently verified reviewer provenance and inspected exact digest, rubric/case, contrary evidence, outcome, unresolved risks and confidence.
- EffectReceiptID: actual tool/provider, operation, request identity, cost/rights grant, result ID/hash, idempotency, side effects and readback.
- LearningCandidateID: evidence, adversarial trials, scope, method/knowledge dependency and positive/negative independent replay; promotion/retirement is not merely a flag supplied by the same agent.

**Consistency:** stable IDs may identify records but never replace version hashes. Reverting text does not restore an invalidated old decision. Source mutation cannot be hidden behind a stable filename. Stale dependency references fail closed at execution where tooling can enforce.

## E. Entry, planning and execution modes

1. **Recover / route:** current user goal and corrections have precedence; identify existing exact project only when explicitly intended and verified. The existence of stored historical tasks does not imply continuation.
2. **Direct session:** short text, critique, straightforward image planning/one-off edit and other bounded outputs when no durable, concurrent or artifact-graph need exists. CAOS applies to every meaningful method/tool choice. Actual provider tool constraints and artifact readback still apply. The native ChatGPT surface currently lacks a hard pre-send interception hook; do not claim otherwise.
3. **Durable Studio:** necessary for long jobs, multi-file artifacts, source lineage, expensive parallel work, replay, approvals, long session continuation, audit or repeatable CLI operators. The existing StudioEngine is the only durable scheduler; no second store/Host. Its current local decision binding is a structural prerequisite, not cognitive quality proof.
4. **Research and method choice:** retrieval must consider goal, source authority, competing root causes, original implementations/counterexamples, alternative methods, pre-action rechallenge, costs and expected outcome. A high-risk unknown can trigger additional research before external effect; a trivial reversible copy choice still checks applicable obligations, but need not create two artificial diagnoses in a database.
5. **Decompose only real dependencies:** create smallest meaningful tasks and outputs; no mandatory storyboard, IP, monetization, trend hunting, research essay, cover, 3-second prototype or RED_TEAM for irrelevant work.
6. **Specialist handoff packet:** exact goal/variant & demand revision, objective, constraints, work contract, source and artifact digests, risk/permissions, decision+method refs, acceptable outputs, independent acceptance rule; any unavailable dependency is explicit WAITING/BLOCKED.
7. **Dispatch:** ask whether a candidate is currently authorized and technically feasible. Ready is not the same as admitted; admitted is not completed; completed is not independently accepted; accepted is not released; released is not posted.
8. **Failure/retry:** classify wrong goal, stale source, bad method/creative concept, tool/provider execution, artifact corruption, quality failure, rights/authorization and missing evidence. Re-open earliest contradicted ancestor, invalidate downstream dependencies only, preserve immutable history. Explicit WAITING_EXTERNAL must not auto-ready because an unrelated declared file exists. Retry budgets and lease expiry must be enforced uniformly; effects need idempotency and reconciliation.
9. **Exit/handoff:** exact bytes, applicable semantic/technical validation, final outcome proof, outstanding obligations, unresolved assumptions, rollback and owner-visible result; do not end on an internal unit-test pass.

## F. Technical ports and provider boundary

Use ports over concrete vendors: source reader; research/browse; translation; text writer; image generator/editor; video generator; timeline editor; audio copy/transform; restoration/enhancement; media probe; render; asset store; review; platform spec discovery; external publication (separately authorized); analytics and IPOS bundle import.

Every provider adapter declares:
- operation exactness (create/edit/extend/restore/upscale/trim/copy), input format, aspect/size/duration/audio behavior, output format, batch/cost, rights, region/account, deterministic vs model-assisted behavior, retry characteristics, and receipt provenance;
- availability = NOT_CHECKED / AVAILABLE_NOW / UNAVAILABLE / BLOCKED_AUTHORIZATION / EXPIRED, with a timestamp and evidence;
- quality assurance = UNTESTED / FIXTURE_TESTED / REAL_ARTIFACT_VERIFIED / USER_OUTCOME_VERIFIED by operation and task type;
- explicit failure/degradation policy and independent readback. No provider claims implied by Skill text.

**Operations are typed.** A format transformation is not AI upscaling; FFprobe success is not semantic video understanding; a story prompt is not a good scene; an image rendering interface is not aesthetic direction. Current five production operations and seventeen domain adapters keep their exact scope. Legacy 0.8 orchestrator is evidence only.

### F1. Audio preservation: three independent promises
- BITSTREAM_IDENTITY: exact audio payload bytes/codec stream unchanged; only offer when container, cut boundaries and mux support it; prove stream hashes/packet identity as applicable. A remux can preserve encoded audio without making output-file bytes identical.
- PCM_IDENTITY: decoded audio samples unchanged through a specified time alignment; compare decoded PCM, channel layout and clock.
- PERCEPTUAL_SIMILARITY: allowed audio processing but independent listen/loudness/sync measures required. **Never silently substitute** a reencoded AAC mix for either identity promise.
User can also request audio untouched while video duration changes; explicitly define crop/ending policy and prove it. Current FfmpegAssembler performs amix/atrim/AAC encoding and therefore cannot claim BITSTREAM_IDENTITY or PCM_IDENTITY by default.

### F2. Aspect and visual integrity
Represent ratio as explicit \`width:height\` plus orientation and target pixel dimensions; e.g., \`4:3 landscape\` is a different deliverable from \`3:4 portrait\`. A multi-aspect set carries shared creative intent but separate composition, text safe regions, focal points, artifact IDs and review. Cropping is not automatically a valid adaptation. Do not infer platform specs from old examples; verify current specifications when a real platform is in scope.

### F3. Original video / IP
Original video requires creative premise, visual narrative, direction, style/lookdev, shot contracts, audio, actual video rendering, editing, real-time media inspection and audience/owner oracle as applicable; it may be hybrid or wholly AI-assisted depending on current authorized provider availability. A moving text card alone cannot assert cinematic quality.
Long-lived original character canon comes from owner-approved IPOS export with exact identity version/rights; a stand-alone avatar is not implicitly a permanent IP identity task. Missing approved canon blocks only canon-dependent shots.

## G. Output quality and acceptance families

No one global PASS from static source, green tests or a text-only LLM self-rating. Each DeliverableType chooses its proof:
- SHORT_COPY: native idiom & language, factuality, originality, tone, hook/reaction purpose, no redundant explanation, precise format, tags only if requested, no involuntary duplicate title/description/cover text.
- LONG_ARTICLE: credible research, independently sourced factual claims, clear thesis, argument/counterargument, original insight, value to reader, causal logic, emotional progression, nonempty conclusion, planned visual placement and actual publishability. Translation quality independent of English source.
- PLATFORM_PACKAGE: platform-current restrictions, title/description/tag/cover copy as distinct complementary functions, local language and cultural context, actual media fit, disclosure and honest attention hypothesis. Engagement/CTR not knowable from copy alone; classify forecast vs observed.
- PROMPT_SPEC: precise creative intent and constraints, reference interpretation, generative model applicability and failure conditions, clear positive instructions, output verification plan; no generated image or video is implied.
- STATIC_IMAGE / MULTI_ASPECT: pixel inspection, story in one glance, composition, hierarchy, subject/reference fidelity, typography accuracy, safe regions, originality, art quality, per-ratio re-layout, visible QA at intended mobile thumbnail size. Prompt elegance alone is irrelevant.
- MEDIA_TRANSFORM: exact source event understanding, specified change-only scope, no accidental scene or time change, original audio mode guarantees, technical stream/codec/sync evidence, full or representative-frame perceptual review; verify real output bytes.
- ORIGINAL_VIDEO: genuine audiovisual narrative, coherent visuals and motion, sound, editing, continuity, art direction, truth/rights, playback QA, final human/independent creative quality. Frame count and FFmpeg success alone insufficient.
- IDENTITY_ASSET: distinct temporary concept vs approved long-lived canon; external authority grants for persistent IP.
- REPORT/ANALYSIS: source coverage, reproducible reasoning, correct limits and auditable conclusions.

Evidence tiers: INVENTORIED; SOURCE_BYTES_READ; STRUCTURALLY_VALIDATED; EXECUTED_ON_FIXTURE; REAL_ARTIFACT_READ_BACK; INDEPENDENT_CRAFT_REVIEWED; OWNER_OUTCOME_VERIFIED. Never roll these up to a fictitious single "completed" grade. Conditional release gates selected by exact type, risk and owner instructions; no video-only red-team/minimum-finding requirement on a one-line text response.

Review independence is an evidence claim: distinct task/context or actual human/provider readback where available; separate role names in one model call cannot establish independence. User satisfaction and live performance remain distinct from internally predicted craft.

## H. Sources, knowledge, skills and lifecycle

- **Source strata:** owner original and corrections (goal), CAOS private source/installed Skill (parent governance), Social Media Studio source revision/PR/test (implementation), active owner Project ledger (state), relevant private assets (raw evidence), external platform/provider sources (volatile capability), historical examples (training/regression only). Never merge strata into one "current" search index.
- **Memory strata:** working context; episodic events; semantic source-versioned facts; procedural independently tested methods; invalidated/superseded history.
- **Knowledge states:** DISCOVERED → SOURCE_VERIFIED → CANDIDATE → TRIALLED → VALIDATED_SCOPE → ACTIVE_SCOPE, with QUARANTINED, SUPERSEDED and RETIRED branches. Transitions require evidence, conditions, negative trials, decision owner and readback; no model self-asserted independent replay.
- **CRUD:** exact ID/path, owner/permissions, prior version/hash, dependency graph, prospective effect, no-op detection, transaction/backup/recovery, independent provider readback. Retire authority separately from irreversible deletion. No CAOS write; no cross-system file auto-mutation.
- **Discoverability:** skill/method applicability and scope tags, explicit matcher/falsifier, trigger criteria and provenance; choose relevant methods per decision rather than injecting the whole corpus. Historical project-specific prompts do not become default global standards.
- **Evolution:** method failures produce knowledge candidates; independent trials against held-out content types and opposite cases before promotion. An old success does not override current owner preferences.

## I. Operational reliability, security and observability

- State machines are scoped: Demand ACTIVE/REVISED/CLOSED; Task PENDING/READY/RUNNING/WAITING_EXTERNAL/BLOCKED/FAILED/COMPLETED/STALE/CANCELLED; Artifact CANDIDATE/ACCEPTED/REJECTED/STALE; Method CANDIDATE/VALIDATED_SCOPE/SUPERSEDED/RETIRED. Never conflate current legacy statuses with target design without migration.
- Append-only events; monotonic revisions; exact CAS or equivalent concurrency control; leases and retry budgets; cancellation; isolated temp files and atomic promotion; multiple workers never double-complete the same effect.
- Input and prompt injection boundaries: web/plugin text and user assets are data, not policy. Rights/consent/likeness and disclosure are separately checked. Imported assets never imply an external publication grant.
- Read-only CAOS parent integration and internal IPOS specialist bridge. Social Media Studio cannot mutate IPOS private state via generic knowledge CRUD; only owner-approved versioned canon export may be used downstream.
- Trace IDs for Demand, Decision, Task, Effect, Artifact, Review, Method; event causality supports replay, missing-data inspection and reversal. Sensitive private originals stay in private destinations; public repository contains mechanism or sanitized test cases only.
- Operation budget and provider switching: live constraints, failure rate, source cost, risk and quality ceiling matter; no fabricated price or guarantee. Consider serial, parallel, competing candidate and no-operation decisions.
- User-visible reporting distinguishes requested result, exact files/links, verified effects, unresolved blockers and next legitimate action. No promise of background work without actual automation.

## J. Migration and refactor dependency plan — ONLY AFTER ARCHITECTURE GATE

M0. Freeze evidence: baseline exact PR head/CI, collect repository and Library inventory, audit protected CAOS/IPOS boundaries, source snapshots and rollback points. No old task activation.
M1. **Contract/authority consolidation:** one canonical *promoted* architecture reference from the existing Studio entry and manifest; rewrite stale legacy active locators as read-only evidence. Remove competing authority, not source history. Align built-in and installed Skill without claiming native auto-trigger.
M2. **Typed demand & deliverable models:** hard/soft constraints, correction chronology, outputs, platform/locale/ratio variants, owner truth and evidence. No mandatory article/video fields on unrelated deliverables.
M3. **Capability & method interface:** port/adapter registry by actual operation with availability and assurance; separate reusable craft knowledge, roles and real provider effects. Existing 17+4 operations remain, no invented general generation operation.
M4. **Cognition/effect bridge:** retain one CAOS parent, current local decision event and artifact ledger; evidence versions and dependencies; affected upstream invalidation; direct-session assurances explicitly soft; red-team negative probes for bypass and stale references. Do not copy parent runtime.
M5. **Planner + scheduler recovery:** demand-specific DAG, optional direct mode, bounded role and group coordination, retry/WAITING semantics, revised outputs and cancel/idempotency; parallel independence and adversarial race checks.
M6. **Domain operations:** generic editorial/longform/short copy/packaging contracts; image/prompt/variant contracts; media transform including strict audio identity; original video adapter optional; IPOS handoff; real provider checks. Do not turn old specialty routines into global templates.
M7. **Quality/learning/lifecycle:** artifact-type release checks, independent craft oracles, versioned knowledge CRUD, source invalidation, event traces and full owner-goal acceptance. Conclude only after actual example outputs are inspected.
M8. **Cleanup and cutover:** snapshot old historical fixtures, compare behavior across main, PR #37 and candidate, remove stale active references/dead control paths without deleting archives, independently verify installed CLI, exact head CI, real end-to-end tasks, owner outcomes and rollback. Merge/promote only after full owner-goal gate and delegated authority conditions.

Ordering is by **change dependencies**, not a compulsory creative workflow. A failing M2 semantics test returns to M1 or the architecture decision; a failed real M6 artifact reopens M3/M4 and perhaps the fundamental domain ontology.

## K. Architecture acceptance matrix (design gate, not runtime proof)

The accompanying \`docs/SOCIAL_MEDIA_STUDIO_ARCH_ACCEPTANCE_V2.json\` encodes representative scenarios and forbidden side effects. Gate design when:
1. Every owner-named operation maps to an applicable DeliverableType, craft bounded context, semantic oracle and admissible execution surface with current-known capability gaps disclosed.
2. No type invokes unrelated video lookdev/Red-Team/production stages by default; no task copies retired historic work.
3. CAOS governance is addressed at every decision/effect level with explicit native-session NOT_TESTED limitation and no cross-repository mutation.
4. Direct vs durable entry, knowledge/roles/professional skills, multi-graph semantics, authorization, external canon and owner-goal acceptance are separate.
5. Every effect boundary has contract, permissions, technical limitations, independent verification and failure path.
6. The precise current implementation gaps have migration owners and real test oracles, not only aspirational prose.
7. Two adversarial reviews pass: conceptual contradiction review and executable mapping/readback review; failures reopen architecture before runtime implementation.

**Architecture PASS is only design readiness.** Runtime, native cognition and media/creative quality remain NOT_TESTED until independently observed. A green documentation check is not product release.

## L. Known gaps that may invalidate this proposal

- Current generation/editing tools and ChatGPT native Skill activation can change independently; not remotely controllable by this repository.
- The 9 current "professional capability groups" are an index, not established final organizational departments or a complete ontology; unknown types are accepted into a researched extension path, not silently assigned.
- Current \`quality-rubric.json\` hardcodes video stages and \`editorial_packaging.py\` is news×video satire-specific; both must be reclassified as scoped methods before use elsewhere.
- Current local FFmpeg assembler mixes/reencodes audio; strict audio identity needs a separate operation and independent byte/sample validation.
- Existing task decision gate checks local structural fields and hashes; native reasoning authenticity, external source truth and semantic sufficiency remain OPEN.
- StudioEngine mixes persistence, decision effects, scheduling, review and release in one 2400+ line module; refactor internal boundaries only once target interfaces and regression oracles are pinned.
- Platform policies, formats and locales change; live provider or official platform evidence requires current query, not an evergreen JSON string.
- Real artistic quality and CTR cannot be inferred from repository tests; require real distinct output samples, mobile read tests, blinded comparison where feasible, actual owner response or real platform analytics.
- Existing tests and branch CI cover structural contracts/fixtures. They do not prove complete source semantic audit, native fresh-chat selection, or real end-to-end owner goals.

**Promotion condition:** design source and cross-reference accepted against this matrix, no unresolved architectural contradiction, exact revision pinned, rollback identified. Until then this file is an architectural candidate with no override power.


## M. Source-to-boundary migration and implementation map (design contract)

The module inventory below was obtained from exact original GitHub file bytes at 1cbc3acf0491ecaa297576372f80163d8c255606. "Read" means imports/public operations were examined, not an assertion of complete line-by-line semantic audit. Keep these original paths in the source ledger until migrated and independently regression-tested.

| Existing source | Current ownership / diagnosed risk | Target operation / migration decision | Protection test |
|---|---|---|---|
| social_media_studio/cli.py (436 lines) | single real CLI; direct/durable split mostly prose | keep thin CLI; delegate typed demand entry, evidence and command ports; avoid novel second CLI | installed smoke; no other launch path |
| social_media_studio/scope.py (168) | task-neutral intake, project epoch, capability/knowledge locator; accepts text goals | adapt to typed DemandContract & route decision without choosing a historical task | exact current owner request / no stale examples |
| social_media_studio/engine.py (~2459) | durable aggregate for state, graph, decisions, assets, review, release | **decompose behind preserved StudioEngine API** into typed demand, graph/admission, artifact/event store, review/quality, knowledge/evidence services only after pinned behavioral fixtures | same public methods, migration and concurrency replay |
| social_media_studio/system_audit.py (454) | current structural audit; cannot prove creative quality | add source/import/authority graph and real operation registry checks; differentiate design/system/real-outcome reports | expected current paths/registries, no green-PASS overclaim |
| social_media_studio/adapters.py (1091) | 17 registered adapters, heterogeneous domain logic | keep compatibility bridge, later group by capability port and version without unreviewed business semantic changes | 17 adapter positive/negative fixtures, input digest, rights |
| social_media_studio/media.py (284) | FFprobe/FFmpeg technical measurement | preserve technical QA port; add typed media/audio transformation oracle, do not conflate artistic review | real-media probes and negative streams |
| social_media_studio/production/{registry,handlers,executors,worker_pool}.py | 4 operations, actual FFmpeg execution, leases, worker concurrency | retain local executor registry; add operation metadata, exact rights/approval constraints, effect receipts and idempotency | two real tools in parallel, stale decision, timeout, retry |
| social_media_studio/production/{contracts,ffmpeg_assembler}.py | video-only RenderSpec; current audio amix/AAC transform | preserve existing assembler for TRANSFORM_AUDIO_AND_VIDEO; introduce distinct AUDIO_STREAM_COPY and other media edit operations **only after feasibility proof** | bitstream/PCM/hash controls, time range, error/fallback |
| social_media_studio/production/{frame_worker,python_frame_renderer,delivery}.py | constrained local graphics and archive | retain as typed local ports; delivery is not platform posting, frame render is not general image generation | font/cost/rights, exact output paths, archive traversal |
| social_media_studio/legacy/{editorial_planning,production_os,plan_graph_bridge}.py | scene/shot editorial types, only applicable to some projects | expose via MediaComposition/ShotContract port; NOT universal article/short-copy plan | simple copy never constructs ShotContract |
| social_media_studio/legacy/{continuity,timeline,editorial_interchange}.py | video continuity, metadata timeline, external NLE interchange | keep optional MediaTimeline port; no generic content schema pollution | metadata roundtrip/source versions |
| social_media_studio/legacy/{media_graph,ip_identity}.py | media provenance, approved external IP bridge | retain provenance and IPOS Anti-Corruption-Layer; map to generic artifact IDs; leave canon in IPOS | missing approved identity blocks only canon-dependent work |
| social_media_studio/legacy/{business_objects,business_metrics,experiments}.py | integrated growth/commercial objective types | optional BusinessContext port with explicit owner activation | one-line caption no sponsor/finance needs |
| social_media_studio/legacy/{model_registry,engine_routing}.py | source-constrained shot/engine routing, not provider execution | convert capability metadata to checked ProviderOperationSnapshot; no fictitious access | unavailable provider and cost denied |
| social_media_studio/legacy/{programmatic_graphics,media_qa}.py | capable but narrower graphics/technical QA | keep scoped renderer; don't promote to cinematic original-video production | real frames, typographic clipping, target digest |
| social_media_studio/legacy/editorial_packaging.py (426) | hardcoded news×video satire and limited platform list | reclassify to HISTORICAL_NARROW_AUDIT; build separate neutral EditorialPackageContract and platform adapters | ordinary cat video, article, Headline vs Description |
| social_media_studio/legacy/{runtime,studio_agents,orchestrator,storage,models}.py | old fixed-stage 0.8 controller and file store | retire **active control authority**; preserve offline regression and transferable craft mechanisms; no simultaneous production scheduler | direct/installed CLI never imports old controller for owner workflow |
| social_media_studio/legacy/program_orchestration.py | old 4-workstream ProgramGraph | optional business semantic source, historical task graph retired | no fixed Program demands |
| social_media_studio/legacy/{roles,techniques,resources}.py | role prompt sections and static technique discovery | preserve knowledge reference and role labels; separate always-applicable methods from selectable actors, add version/validity | blind review is a method, not a "new agent" |
| social_media_studio/legacy/{reviewer_providers,execution_attestation,generation_guard}.py | isolated reviewer and generation preflight contracts, no guaranteed native tool use | optional assurance/provider ports with real execution evidence; no self-attested independence promotion | disconnected provider fails closed |
| social_media_studio/legacy/owner_behavior_admission.py | older domain root-scope style | preserve as historical method to compare against parent CAOS; no second cognitive controller | only actual parent selected governance applies |
| social_media_studio/legacy/data/{workflow,execution-plan,quality-rubric}.json | fixed video stages/lookdev; tempting global default | mark scope-limited historical methods; build DeliverableType- and risk-specific rubrics before any active replacement | one-line title no LOOKDEV or three reviews |
| social_media_studio/legacy/data/{capabilities,roles,agents,coordination-policy}.json | generic capability declarations plus historical references; 9 groups are categories | one registry per concept: exact operation vs role vs method vs team pattern, with cross-reference but no duplicate authority | 17+4 operation reflection; role prompt sync |
| social_media_studio/data/{studio_manifest,knowledge_catalog,business_feedback}.json | active authority/knowledge/business relations | keep one promoted manifest as current locator after design gate; stable IDs, scoped method state, no default task | exact-path readback, source dependency invalidation |
| skills/social-media-studio and docs/standalone_social_media_studio.md | possible duplicate entry rules | consolidate to one root entry/manifest and method-specific references; avoid copied contradictions | installed Skill vs source conformance test |
| projects/, examples/, historical audits | old tasks, outputs, prompts and regression data | leave source evidence intact; exclude from NEW route; use explicit migration/extraction with method applicability tests | no legacy current project from search or defaults |

**Extract rather than copy:** A narrowly successful method from a historical pilot is a METHOD_CANDIDATE with source/conditions. Do not copy project briefs, specific people, title ideas, brand identity, platform settings or completed task objects into a new demand.

## N. Target module responsibilities and ports (not a commitment to unnecessary files)

Choose the smallest source layout able to hold these **interfaces**. Directory examples are descriptive; a source file is created only when a real separation is justified and regression tests exist.

- \`social_media_studio/domain/contracts.py\`: pure models DemandContract, DeliverableContract, ContentIntent, Variant, SourceClaim, ReviewContract. No SQLite/network/provider import.
- \`social_media_studio/domain/decisions.py\`: Video-local decision dependency and effect-snapshot contract, never a copied CAOS parent runtime; support invalidation from source/goal/method changes.
- \`social_media_studio/domain/capabilities.py\`: operation typed metadata; keep old registries as adapters.
- \`social_media_studio/application/intake.py\`: compare direct vs durable, derive goal revision and bounded context plan, expose why a group is selected. No automatic task effect.
- \`social_media_studio/application/planning.py\`: typed deliverable-to-task decomposition, optional DAG; only real dependencies.
- \`social_media_studio/application/coordination.py\`: bounded consult/compete/review/adjudicate patterns, not permanent agent manager.
- \`social_media_studio/application/assurance.py\`: per-deliverable oracle assembly, artifact and evidence version checks, independent-review request/receipt verification.
- \`social_media_studio/ports/{readers,providers,media,platforms,knowledge,identity,review}.py\`: Protocol/ABC contracts with effect scopes, output evidence, idempotency and permissions. Adapter code depends on these ports; domain contracts never import external providers.
- \`social_media_studio/infrastructure/{sqlite,artifact_store,event_log}.py\`: keep existing public StudioEngine facade and transaction semantics; internally extract only after backward-compatibility proof.
- \`social_media_studio/adapters/\`: concrete mappings to existing 17 domain adapters, local four production operations, and CURRENT_AVAILABLE external tools. The old giant adapters.py is a compatibility entry until negative import tests pass.
- \`social_media_studio/knowledge/\`: scoped method/source retrieval + lifecycle and dependent decision invalidation. The existing knowledge_catalog is a locator, not an authority to change external files.
- \`social_media_studio/contracts_by_type/\`: first reusable neutral contracts for SHORT_COPY, LONG_ARTICLE, PLATFORM_PACKAGE, PROMPT_SPEC, PROMPT_SPEC, STATIC_IMAGE, MULTI_ASPECT_IMAGE_SET and MEDIA_TRANSFORM; add ORIGINAL_VIDEO quality methods separately after sample tests.
- \`social_media_studio/cli.py\`: only persistent CLI; direct ChatGPT session does not require calling it to prove CAOS.

### N1. Illustrative typed interfaces (design only; not exact future Python API)

\`DemandContract {id, revision, original_goal_ref, correction_refs, required_deliverables[], owner_constraints[], preferences[], prohibitions[], expected_business_outcome, authorization, unknowns}\`

\`DeliverableContract {id, demand_rev, type, content_intent_id?, locale?, platform?, shape?, aspect?, constraints, source_refs, expected_artifacts[], quality_oracles[], source_truth_policy, rights_policy}\`

\`CapabilityOperation {id, exact_operation, valid_input_types, output_types, applicability, forbidden_assumptions[], provider_snapshot?, effect_scope, permissions, cost_ceiling?, assurance_ceiling, known_gaps}\`

\`DecisionEffectBinding {decision_id, demand_rev, affected_task_revision?, relevant_source_digests[], method_version?, exact_operation, effect_grant?, falsifier, rollback, prior_event_anchor}\`

\`EvidenceReceipt {actual_executor, request_id, external_operation_id?, source_digests, result_artifact_id?, output_sha256?, measured_properties, test_environment, independent_reviewer?, confidence, open_issues[]}\`

\`QualityOracle {deliverable_type, target, required_properties[], test_method, observation_refs[], independent_assessor?, result, failure_scope, reentry_target}\`

Migration adapters translate existing brief \`goal,audience,deliverables[]\` to typed contracts only if the resulting output and permissions remain semantically equivalent; otherwise create a new explicit owner-scoped revision and invalidate dependents.

### N2. Contract evolution and concurrency
- Source and operation schema versions are explicit, with upgrade readers for old versions. Do not write over immutable old evidence or use a same-path copy to falsely pass provenance tests.
- Import from source→current scope requires source owner evidence, artifact ID+hash and rights. Cross-project import copies exact source version with transfer receipt and reverse invalidation.
- A revised DemandContract increments the goal event/revision; completed decisions based on that event become stale. A task revision does not alter unrelated tasks. Reverting text still has a new revision identity.
- Reclaiming expired leases, WAITING_EXTERNAL, retry exhaustion, provider response uncertainty and owner cancellation have separate machine-observable states. Idempotency keys and read-before-retry defend against duplicated external effects.
- Typed technical QA is reusable, but release/approval is the permission boundary. No "complete task" implicitly publishes, licenses or deletes.

## O. Design negative probes and acceptance strength

The 28 scenario pairs in \`docs/SOCIAL_MEDIA_STUDIO_ARCH_ACCEPTANCE_V2.json\` are architectural requirements. Every scenario must have both a positive oracle and an explicit forbidden implicit effect; none is a report of successful media generation.

Additional interface-level negative probes before code refactor:
1. Wrong deliverable type tries a video-only media QA or lookdev gate: FAIL architecture routing.
2. A method says "ACTIVE" but underlying source version moved or is historical: FAIL admission until revalidation.
3. An agent fills every decision receipt field but sources/alternatives are fabricated: DO NOT infer cognitive validity; require source evidence/independent challenge appropriate to risk.
4. A reusable role ID equals the current tool provider but no actual provider is connected: FAIL effect authorization.
5. Simulated "human review" from a renamed model role: FAIL independence where real separation is required.
6. A revision removes a premise then later restores the same string: old decision authorization remains invalid.
7. One parallel branch loses its lease or source: unrelated admitted branch proceeds, affected dependents stale.
8. A video effect changes the soundtrack while the owner specified BITSTREAM_IDENTITY: FAIL regardless of playback quality.
9. An external distribution action is attempted from a content-package "complete" event: FAIL without publication grant.
10. A single editorial task defaults to Program/Series/Episode or old creative director lookdev: FAIL.
11. User sends an irrelevant reference photo; no project/input relation grants it artifact status.
12. No native Skill-selection trace: assurance remains NOT_TESTED even if model prose looks CAOS-compliant.

**Architecture evidence tiers for this revision:** repo-path inventory READ; 40+ relevant original source modules' import/operations inspected; 28 scenario pairs structurally repaired and mapped; relevant AWS DDD, LangGraph, OpenAI Agents guardrail and FFmpeg originals researched; no independent native Skill trigger run; no complete semantic examination of every historical project; no independent owner-grade original media production. All missing proof stays OPEN.

## P. Ontology counterexample: prompt specification as a first-class deliverable

The owner's explicit prompt-only requests are not necessarily analysis reports or generated media. Negative probe S08 previously forced `ANALYSIS_REPORT`, hiding the no-generation boundary and prompt-specific craft oracle. Competing models: report subtype (wrong primary artifact), implicit static image (false generation obligation), or explicit PROMPT_SPEC. Select **PROMPT_SPEC** with creative-method evaluation and zero provider effects unless separately requested. This change crosses architecture source, acceptance scenarios, typed contract and tests. It must not change user authorization or imply prompt success without real generated-artifact trial.

## Q. Identity correction: multi-aspect outputs are variants, not one image with a ratio

Architecture negative probe S07 requires independent 3:4 portrait and 4:3 landscape deliverables under the same creative intent. The initial pure contract wrongly modeled one `shape` per deliverable and no variant identity; this could hide cropping and artifact lineage defects. The revised contract uses an explicit set DeliverableID with two or more VariantIDs and independently declared pixel dimensions, orientation and distinct ratios. Only the content intent may be shared, not the output bytes, composition, typography review, source digests or release evidence. Single STATIC_IMAGE has one primary shape; multi-aspect set cannot pretend one shape covers all. Further platform/localization variant behavior remains a separate bounded contract to validate.

## R. IPOS belongs INSIDE the content product; source custody stays independent

Owner correction: identity design, avatar, character construction, ongoing IP and eventual digital-human/video production are content-system professional abilities. IPOS must not be drawn as an unrelated peer product. **Product containment does not require moving its private canonical Library, changing its existing installed Skill, copying its personal creator goals, or installing a second scheduler.**

Confirmed original implementation: IPOS 1.4.2 is a skills-only professional workflow with its own user goal, active private checkpoint, authority and isolated rendering rules. Video already contains social_media_studio/legacy/ip_identity.py, IPOS Video Identity Bundle 1.0 Schema, five IPOS domain adapters, and identity-specific test coverage. These are downstream consumers, not the full IPOS creation/runtime engine.

Identity intent modes:

| Identity mode | Demand handling | Authorization and scope |
|---|---|---|
| TEMPORARY_CHARACTER | normal Visual Craft, one-off cover/avatar/fictional character | no personal IPOS state, no permanent canon claimed |
| PERSISTENT_IDENTITY_DESIGN | Original Identity / IPOS nested specialist context | proceed with research/design when allowed; owner alone approves permanent identity, and scoped render permission is separate |
| APPROVED_CANON_USE | any content task referencing persistent IP | read and independently verify current owner-approved exact-version IPOS bundle before a canon-dependent effect |
| IDENTITY_DERIVATIVE | approved identity to avatar variants, expression/motion parts | versioned approved source and allowed variation/rights constraints; output is a new artifact, not a canon mutation |
| NO_IDENTITY | text, media repair, non-character content | do not initialize persistent identity or block unrelated production |

The Video legacy projects/ai-self-media-commercialization/IPOS_INTEGRATION_STATE.json points to an old R39 checkpoint and locator, hence is historical evidence, not an active authority. Do not copy present private IPOS candidates or states to public GitHub. No current owner-approved visual canon bundle was independently verified in this audit; a test fixture cannot act as production permission.

The internal IPOS context has a **separate source-of-truth boundary**: installed Skill / current private canonical state -> explicitly approved, versioned export (bundle digest, canon ID, version, rights, approval and scope) -> Video local media graph/shot continuity consumers. Revocation or a source change invalidates only consuming assets, not unrelated content tasks. Canon creation/approval remains in IPOS and with the user; Video may call specialist work as an internal product responsibility, but must not create a competing identity master.

Counterexamples: a temporary avatar does not boot personal-IP work; a long-lived creator identity belongs to the content product; unapproved identity may be designed but not used as approved canon; stale R39 snapshot cannot prove current approval; one affected shot does not block unrelated tasks; no natural-language text or image-request mention grants render, IPOS state mutation, third-party processing or publication.

## S. Scoped actual video editing with verified original encoded audio

Registered tool ffmpeg_video_audio_copy offers three operations: PASSTHROUGH, CROP (bounded even geometry), and TRIM_END_ONLY (time from zero). It never alters audio through filters or transcoding, and independently hashes actual audio packet data in input/output. A full edit requires identical packet sequences; a shortened edit requires an exact source prefix and discloses the new length. This does not mean the whole container file is byte-identical; it does not demonstrate perceptual listening QA, video repair of blood, AI 4K enhancement, audio cleaning or creative quality. The existing ffmpeg_assemble continues to reencode audio and cannot satisfy this requirement. No audio-only or multitrack guarantee is inferred. Proof is a versioned receipt, candidate only; release is separately authorized.

## T. Neutral multilingual editorial and cross-platform package contracts

Long-form original articles are not a video stage, and platform titles, descriptions, hashtags and cover text serve distinct purposes. Added neutral pure data contracts (Article: body/optional section identities/factual refs/visual slots, variable length; Package: explicit platform and locale variants with distinct title/description/cover_copy and tag syntax). Platforms include X, TikTok, YouTube, Douyin, WeChat Channels, Toutiao, Xiaohongshu and Bilibili, but this is a field vocabulary, NOT a claim of current live publishing constraints. Editorial quality, semantic originality, factual truth, bilingual idiom, humor and real CTR remain independently unverified. A read-only CLI validator can check structural output without creating a Studio project or publishing. The narrow historical news-video satire audit remains a scoped optional method, not this universal editorial contract.

## U. Knowledge admission incident: self-attested VALIDATED is not independent

The current StudioEngine recorded a method as VALIDATED if the author supplied independent_replay_pass=true and any nonempty validation_evidence_refs and counterexample_trials (including fabricated review:// strings). This is a cross-task cognitive contamination risk: a formally valid receipt was being treated as independent method quality. The safe provisional policy is no automatic promotion from record_learning: it always registers CANDIDATE with original claimed evidence preserved. Existing project-local read and compare-and-swap retirement interfaces preserve the method and event history. A future VALIDATED_SCOPE promotion must verify actual external/owner source artifact identity, source versions, counterexample replay and real independent effect; until then no global method is conferred by the Studio ledger. Historic VALIDATED records are readable and may be explicitly retired by exact current status; their meaning is not retroactively upgraded. This is a product safety and lifecycle stage, not complete knowledge CRUD and independent scope validation.

## V. Recovery state contract: explicit wait vs missing file; retries vs re-admission

Original _refresh_in_tx treated all WAITING_INPUT as missing files; it automatically made an explicitly deferred task READY as soon as its declared input files existed. Original reopen() preserved attempts and could re-admit a FAILED task even when attempts were exhausted, bypassing the planned retry cap. Selected a unified engine state boundary: explicit_external_wait marker held until owner/worker confirms external dependency through reopen, while ordinary WAITING_INPUT remains auto-resolvable when declared artifact inputs arrive; exhausted READY tasks remain visible but cannot be claimed until a real task-contract revision resets attempts and binds any required new cognitive decision. Independent ready tasks remain callable. This is state/permission consistency, not proof of an actual owner response or cognitive reasonableness.

## W. Visual and image-prompt source-role interface

Read project-scoped image design research, GPT Image Prompting Method V2, positive morphology language rule, human core construction stack and benchmark/quality-gates/generation governance. These original methods have incompatible applicability: permanent creator morphology/identity restrictions belong only to the nested IPOS design task, while a one-scene X editorial illustration and a one-shot cover use different visual craft contracts. Selected a pure VisualDirection preview with explicit owner creative intent, one actual subject/story, optional prompt, candidate IDs and per-reference role/allowed/excluded influence, and no implicit injection of unrelated images. Prompt-only requests require a draft prompt but cannot invoke an image generator. Existing-image edits require an actual reference binding. The inspector NEVER claims pixels rendered, aesthetic quality achieved, source bytes verified or independent review passed. Real image generation/editing provider hookup, aspect-specific art direction and final pixel review are separate unfinished downstream operations. This method is not a forced multistage H0-H10 IPOS workflow.

## X. Non-universal quality review contracts
The old video-only lookdev and rough-cut scorecard cannot govern a one-line title, X longform, static image, image prompt or a bounded media trim. Added separate criteria per deliverable type and per aspect-ratio image variant, with owner acceptance and exact-source review obligations. A quality plan never self-certifies pixels, native language, independent craft, true identity approval or publication. Legacy benchmark methods remain scoped optional research, not universal stages. This is review-demand modeling; real output inspection remains OPEN.
