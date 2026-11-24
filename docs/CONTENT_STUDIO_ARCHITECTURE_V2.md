# Universal Content Studio — Architecture Contract v2 (DESIGN CANDIDATE)

**Status:** ARCHITECTURE_CANDIDATE / NOT_PROMOTED / NO_RUNTIME_AUTHORITY  
**Owner:** VIDEO_GROWTH_AGENT (repository name retained for compatibility)  
**Frozen implementation baseline:** PR #40, commit 1cbc3acf0491ecaa297576372f80163d8c255606; 370-test exact-head CI 45416359779 PASS.  
**Governance authority:** owner intent + corrections; CAOS parent Skill and private owner original, read-only; child domain decisions and execution remain Video-owned.  
**External canon:** original persistent characters belong only to IPOS.  
**Scope:** design all architecture dimensions before runtime implementation; no change to CAOS source; no old task reactivation, automatic publication or provider authorization.

## A. Product boundary and invariants

The product is a **general digital content creation, transformation and multi-platform delivery capability**, not a mandatory video production pipeline. The historical repository name is an address, not a domain restriction. Accept one-line text, X long-form articles, Chinese/English and other-language platform titles/descriptions/tags/cover copy, images, aspect variants, avatars, prompt development, visual edits, brief video trims, restoration, audio preservation, QA, original audiovisual work, audience/growth and optional commercial work. A request may activate none, one or many of these capabilities. Every demand is interpreted from the current owner goal, not a previous project or title.

Non-negotiable architecture properties:
1. **One goal authority:** the owner's original demand plus ordered corrections; an example, past project, viral trend or prior assistant plan does not acquire authority.
2. **One parent cognition authority:** read-only CAOS guidance across all levels and every substantive decision/effect, including routing, diagnosis, method research, tool choice, code change, review and learning. The Video runtime cannot certify native ChatGPT Skill selection or mental quality. No copied CAOS Host.
3. **One Video durable task ledger:** StudioEngine's current per-project SQLite and append-only event history; no second planner/controller for the same project. Direct session work needs no artificial project.
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
- A. Rebuild a monolithic CAOS+Video all-purpose controller: reject duplicate authority, excess coupling and unverifiable native enforcement.
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
- Local original implementation: video_studio/engine.py, scope.py, adapters.py, production/{registry,worker_pool,ffmpeg_assembler}.py, video_growth_agent/{editorial_packaging,roles,quality-rubric}. All verified against the frozen baseline, with limits noted below.

## C. Multiple architectural VIEWS (never present as one sequential chart)

### C1. Authority and responsibility
- USER: original goal, constraints, preferences, effect authorization, owner acceptance, corrections.
- CAOS parent: recurring, recursively re-enterable cognitive and execution governance, root-cause diagnosis, source qualification, method challenge, independent overall goal assessment. **Read-only source; no child state ownership.** Native first-mile activation NOT_TESTED.
- CONTENT STUDIO domain: demands, deliverables, craft judgement, planning, local evidence, asset custody, quality/acceptance and optional platform distribution preparation.
- IPOS: exclusive authority for permanent original identity canon; Studio may import an owner-approved versioned bundle but cannot rewrite canon. Ordinary one-off avatars/temporary visuals do not imply permanent IPOS involvement.
- PROVIDER/PLATFORM: actual operations and state, available only through current checked interfaces, not inferred from documentation.
- INDEPENDENT REVIEWER: distinct actor/context where required, with actual artifact readback; an arbitrary reviewer string is not proof of independence.

The existing L0–L6 labels are **responsibility scopes**, never an execution ordering. CAOS crosses every applicable scope, including itself being challenged as a method and the adequacy of its evidence. Child authority is not a grant from a parent configuration string.

### C2. Product bounded contexts
1. **Demand & Portfolio** — current goal, correction sequence, typed deliverables, versioned acceptance, platforms/locales/constraints, optional program context; owns no generated media.
2. **Research & Understanding** — source media and text, transcription/scene or claim understanding, evidence/fact provenance, intellectual context, epistemic uncertainty.
3. **Editorial & Language** — argument, structure, original viewpoint, narrative, long-form article, concise copy, jokes, natural Chinese/English, translation/localization.
4. **Visual & Identity Craft** — composition, visual hierarchy, art direction, cover/portrait, prompt specification, revision, image generation/edit interfaces; respects separate IPOS canon.
5. **Motion, Sound & Media Operations** — video concept/shot planning, rendering, editing, clips, crop/reframe, enhancement, restoration, strict audio handling, subtitles.
6. **Platform Packaging & Growth** — platform-specific variant, title/description/tags/cover copy, publication specifications, packaging hypotheses, analytics and experimental learning.
7. **Evidence, Asset & Knowledge** — immutable source/output versions, lineage, rights, knowledge status, index, search, import/transfer/invalidation, durable episodes.
8. **Planning, Execution & Effect** — direct mode or existing StudioEngine, dynamic task dependencies, workers, leases, idempotency, actual tool ports and authorization.
9. **Quality & Independent Acceptance** — typed oracles, technical and craft reviews, owner-goal evaluation, release/admission separation, failure re-entry.

These are **bounded responsibility contexts**, not nine servers, nine compulsory phases or nine permanent workers. A one-sentence task may require only Demand, Editorial, relevant Quality and direct outcome verification.

### C3. Orthogonal graphs
- **Cognition/justification graph:** question → hypotheses/alternatives → sourced decision → dependent conclusions/effects; can cycle via falsification/research. CAOS parent governs; Video stores local evidence for Video effects. This is NOT the task DAG.
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
- DeliverableID / DeliverableType / DeliverableRevision: exactly requested output, independent contract. Types: SHORT_COPY, LONG_ARTICLE, PLATFORM_PACKAGE, STATIC_IMAGE, MULTI_ASPECT_IMAGE_SET, MEDIA_TRANSFORM, ORIGINAL_VIDEO, IDENTITY_ASSET, ANALYSIS_REPORT, plus extensible typed families; no default video final.
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

**Operations are typed.** A format transformation is not AI upscaling; FFprobe success is not semantic video understanding; a story prompt is not a good scene; an image rendering interface is not aesthetic direction. Current four production operations and seventeen domain adapters keep their exact scope. Legacy 0.8 orchestrator is evidence only.

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
- STATIC_IMAGE / MULTI_ASPECT: pixel inspection, story in one glance, composition, hierarchy, subject/reference fidelity, typography accuracy, safe regions, originality, art quality, per-ratio re-layout, visible QA at intended mobile thumbnail size. Prompt elegance alone is irrelevant.
- MEDIA_TRANSFORM: exact source event understanding, specified change-only scope, no accidental scene or time change, original audio mode guarantees, technical stream/codec/sync evidence, full or representative-frame perceptual review; verify real output bytes.
- ORIGINAL_VIDEO: genuine audiovisual narrative, coherent visuals and motion, sound, editing, continuity, art direction, truth/rights, playback QA, final human/independent creative quality. Frame count and FFmpeg success alone insufficient.
- IDENTITY_ASSET: distinct temporary concept vs approved long-lived canon; external authority grants for persistent IP.
- REPORT/ANALYSIS: source coverage, reproducible reasoning, correct limits and auditable conclusions.

Evidence tiers: INVENTORIED; SOURCE_BYTES_READ; STRUCTURALLY_VALIDATED; EXECUTED_ON_FIXTURE; REAL_ARTIFACT_READ_BACK; INDEPENDENT_CRAFT_REVIEWED; OWNER_OUTCOME_VERIFIED. Never roll these up to a fictitious single "completed" grade. Conditional release gates selected by exact type, risk and owner instructions; no video-only red-team/minimum-finding requirement on a one-line text response.

Review independence is an evidence claim: distinct task/context or actual human/provider readback where available; separate role names in one model call cannot establish independence. User satisfaction and live performance remain distinct from internally predicted craft.

## H. Sources, knowledge, skills and lifecycle

- **Source strata:** owner original and corrections (goal), CAOS private source/installed Skill (parent governance), Video exact main/PR/test (implementation), active owner Project ledger (state), relevant private assets (raw evidence), external platform/provider sources (volatile capability), historical examples (training/regression only). Never merge strata into one "current" search index.
- **Memory strata:** working context; episodic events; semantic source-versioned facts; procedural independently tested methods; invalidated/superseded history.
- **Knowledge states:** DISCOVERED → SOURCE_VERIFIED → CANDIDATE → TRIALLED → VALIDATED_SCOPE → ACTIVE_SCOPE, with QUARANTINED, SUPERSEDED and RETIRED branches. Transitions require evidence, conditions, negative trials, decision owner and readback; no model self-asserted independent replay.
- **CRUD:** exact ID/path, owner/permissions, prior version/hash, dependency graph, prospective effect, no-op detection, transaction/backup/recovery, independent provider readback. Retire authority separately from irreversible deletion. No CAOS write; no cross-system file auto-mutation.
- **Discoverability:** skill/method applicability and scope tags, explicit matcher/falsifier, trigger criteria and provenance; choose relevant methods per decision rather than injecting the whole corpus. Historical project-specific prompts do not become default global standards.
- **Evolution:** method failures produce knowledge candidates; independent trials against held-out content types and opposite cases before promotion. An old success does not override current owner preferences.

## I. Operational reliability, security and observability

- State machines are scoped: Demand ACTIVE/REVISED/CLOSED; Task PENDING/READY/RUNNING/WAITING_EXTERNAL/BLOCKED/FAILED/COMPLETED/STALE/CANCELLED; Artifact CANDIDATE/ACCEPTED/REJECTED/STALE; Method CANDIDATE/VALIDATED_SCOPE/SUPERSEDED/RETIRED. Never conflate current legacy statuses with target design without migration.
- Append-only events; monotonic revisions; exact CAS or equivalent concurrency control; leases and retry budgets; cancellation; isolated temp files and atomic promotion; multiple workers never double-complete the same effect.
- Input and prompt injection boundaries: web/plugin text and user assets are data, not policy. Rights/consent/likeness and disclosure are separately checked. Imported assets never imply an external publication grant.
- Read-only CAOS and IPOS integration adapters; video code must not access their private source through a generic "knowledge CRUD" write path.
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

The accompanying \`docs/CONTENT_STUDIO_ARCH_ACCEPTANCE_V2.json\` encodes representative scenarios and forbidden side effects. Gate design when:
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
