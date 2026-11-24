# CAOS architecture decision receipt — Universal Content Studio v2

Status ARCHITECTURE_CANDIDATE_NOT_PROMOTED (2026-11-24). This is a scoped design record, not a new controller or business task, and does not override the currently operating Video manifests. CAOS and IPOS source were read, not changed.

## Goal and exact evidence
Owner: first establish a whole-system architecture with all upper/lower domain, organization, task, method, knowledge and effect boundaries; only after architecture is valid, perform systematic refactor. Earlier user corrections: all decisions and effects are governed by recursive CAOS, not a fixed sequence; keep reusable methods/capabilities but retire all old task instances; support bilingual original long-form, platform packaging, static image/cover/ratio, media comprehension/edit/restoration, audio identity and original video. Source: current owner request plus CAOS private operating manual / installed Skill; code at Video candidate 1cbc3acf0491ecaa297576372f80163d8c255606, CI 45416359779 PASS (370 tests), main 6fac8f58227e8a9bf7f59707895692ade06b8806; CAOS main 9686cedeb3fd8171ecf70eab33aaea641217b04a.

## Rival root causes and differentiators
H1 absence of scheduler: disproven by actual StudioEngine claims/leases, immutable versions, four production operations, seventeen adapters and worker pool.
H2 weak prompt alone: existing CAOS original/Skill already contain recursive challenge, making execution lapse a separate observed problem.
H3 domain/authority/role/method/task conflation: supported by four old media-business workstreams, fixed-stage visual rubric, case-specific editorial packaging module, prior retired task references and native-session soft boundary.
H4 all downstream media failures are provider deficits: not enough; prior outputs and tests demonstrate that rendering fidelity, direction and real craft oracle are distinct.
H5 new LangGraph/Temporal/Agents SDK will enforce native ChatGPT cognition automatically: original docs/source contradict universal interception; new orchestration alone does not prove creative outcome.

## Considered routes
A replace entire product with a new controller: preserves few existing proofs and risks duplicate parent/child truth; reject pending specific falsifier.
B permanently instantiate nine groups/agents: undesired overhead and autonomy illusion; reject.
C patch each platform/media failure locally: reproduces overfit and authority drift; reject.
D modular domain-centered contracts/ports/adapters, one optional StudioEngine runtime, direct session surface, current CAOS read-only governance: **selected design candidate**.
E third-party workflow platform: optional future substrate if real workload demonstrates a deficiency and tests justify migration; no current requirement to add it.

## Original-source research and transfer caution
Read actual Video engine, registries, local FFmpeg assembly, roles, narrow news-video editorial module, quality-rubric, manifest/capability/knowledge and task/readiness models. Studied original LangGraph StateGraph/graph API for conditional dependencies and idempotency, original OpenAI Agents SDK guardrail source and its uncovered handoff/hosted-tool boundaries, AWS DDD/hexagonal domain ports, and Temporal versioning principles. These are mechanism comparisons, not mandatory dependencies. No proof that third-party framework quality transfers to owner-facing art outcomes.

## Pre-execution rechallenge and falsifier
Architecture is invalid if short copy starts a compulsory video pipeline; an image ratio variant only crops; FFmpeg AAC mixing passes a strict untouched-audio promise; any new task loads retired project/IP scope; an unconnected provider is treated as available; task success is mistaken for independent content quality; native CAOS selection is falsely claimed; or a resumed task uses a stale goal/method. The 28-scenario design matrix explicitly covers these cases. Architecture review must verify semantics, not simply JSON schema validity.

## Effect, rollback and remaining gates
Only new **design candidate documents** added under docs/ and audits/. No runtime code, no manifest/Skill/CAOS/IPOS/provider/mutable task changes in this phase. This design can be abandoned by reverting its own doc-only commit. Before runtime refactor: independent contradiction review, source-map coverage, 28-scenario design classification, exact HEAD readback. Later implement M0–M8 under the single promoted authority; exact CI and true artifact/owner outcome remain separate gates. All professional quality, native skill auto-selection and unknown provider support remain NOT_TESTED.

## Architecture counterexample: lost forbidden-effect conditions (2026-11-24)
Independent readback of the candidate acceptance JSON showed that all 28 scenario entries accidentally used a two-element array in the positive oracle property and had no separate forbidden_implicit_effect field. A simple scenario-count test missed this. The wrong matrix would under-specify absence-of-side-effect proof and could falsely admit a fixed video workflow. Repaired the source model to separate positive and forbidden conditions, added schema invariants and retained REQUIRES_INDEPENDENT_REVIEW. This is design-contract repair only; no Video runtime or CAOS change. If a future schema change again drops either oracle, fail architecture admission.

## Source-level module mapping and architecture rehearsal
Read the source imports and public operations of video_studio core, handlers, registry, worker pool, CLI, media and scope, plus the original video_growth_agent business, original IP, media, quality, prompt/roles, experimentation, technical generation and legacy controller modules at the frozen head. Determined that old 0.8 modules must remain regression/source references, not active parallel scheduling. Added sections M–O to the single design candidate: exact source-to-target mapping, typed contract sketches, version and concurrency contracts, and twelve additional negative probes. These add implementation precision, not a new runtime authority. Independent source/call-path replay and fresh-user media outcomes remain OPEN.

## Architecture classification counterexample: prompt-only outputs
A first-party user demand explicitly requests prompt design without generation. Previously the scenario matrix classified it as ANALYSIS_REPORT. This misclassified a standalone deliverable and could cause invalid QA or unwanted provider effects. Compared report subtype, unfulfilled STATIC_IMAGE and PROMPT_SPEC. Selected PROMPT_SPEC, updated architecture, scenario S08, pure type enum and negative test. Existing source and rights checks remain applicable; generation is not inferred or authorized.
