# 自媒体系统（Social Media Studio）

The source package, command and product identity have been migrated; the GitHub remote address requires a separate administrative rename. This is a CAOS-governed **general digital content system**, not a mandatory video-production pipeline. Its on-demand professional capabilities include original Chinese/English writing and X Articles, platform-native titles/descriptions/tags/cover copy, static/multi-aspect images and prompts, multimedia understanding and editing, exact audio preservation, audiovisual production, and nested Original Identity/IPOS. Each user goal activates only relevant capabilities. The Social Media Studio runtime remains technically independent of the CAOS codebase; CAOS governs the user's selected work at every material decision/effect.

**Current launch authority:** `STUDIO_ENTRY.md` + `social_media_studio/data/studio_manifest.json`. **Detailed candidate architecture:** `docs/SOCIAL_MEDIA_STUDIO_ARCHITECTURE_V2.md` (not automatically promoted). **No repository project, campaign or 50-task plan is active by default.** Read only specific historical sources if they are relevant; do not treat a task sample as a current owner goal.

## Durable work: one goal, one ledger, bounded cycles

Use `sms-studio intake REQUEST.json` to identify only the owner's current demand. For a persistent project, bind the exact brief/deliverables, register task dependencies and current CAOS-governed decisions, then inspect `sms-studio work-cycle PROJECT --plan-only`. This projects currently admitted parallel lanes (tool/agent/human/external), exact-input handoff packets and decision/input blockers without claiming external authorization. `sms-studio work-cycle PROJECT --max-workers 2` executes **only locally registered, admitted tool operations** in finite concurrent rounds and then reads actual outcomes back. Revisions invalidate dependent work; failures require cause and method challenge; registered artifacts and independent review precede release. Learned methods remain candidates until independently tested and accepted.

Owner project initialization requires the explicit `--owner-task` flag; this binds the current scope but does not prove CAOS activation. Offline regression roots are created only from an empty, separate directory and receive a `.sms-offline-fixture.json` isolation marker. They cannot reuse the configured owner workspace or any project carrying an owner scope epoch.\n\nFor a project carrying the previous scope epoch, use `sms-studio --root WORKSPACE migrate-scope PROJECT --reason "approved current goal"` once before RESUME. This preserves events and artifacts, supersedes earlier action decisions and revokes running claims; it never auto-resumes retired example projects.

The research subsystem has a deterministic `source_evidence_audit` tool operation for an immutable claim manifest and declared UTF-8 source artifacts. It verifies exact source digests and quoted passages; it **does not** perform live research, semantic factual verification, automatic publication, or independent content acceptance.

## Current authority

- `STUDIO_ENTRY.md` — only startup and operating entry for new self-media work.
- `docs/standalone_social_media_studio.md` — self-media-owned goal, decision, dynamic DAG, execution, artifact, review, failure and learning method.
- `social_media_studio/data/studio_manifest.json` — canonical runtime and parent-governance contract; no CAOS runtime/API dependency.
- `social_media_studio/engine.py`, `cli.py`, `media.py` — canonical standalone project state, concurrent task claims, artifact lineage and deterministic FFmpeg/FFprobe QA.
- `social_media_studio/adapters.py` — explicit, task-bound adapters for EditorialPlan, ShotContract, IPOS shot binding, IPOS continuity, MediaGraph bootstrap, Timeline, continuity, shot routing, business metrics, supplementary audio QA and deterministic local graphic rendering.
- `skills/social-media-studio/SKILL.md` — self-contained self-media-owned agent operating instructions.
- `domain_manifest.json` and `capabilities.json` — self-media-owned domain identity and capability contracts consumed by the canonical Studio.
- `docs/product_requirements.md` — historical 0.8 product-requirements baseline; new operating authority is the standalone contract.
- `docs/media_business_os.md` — 0.8 media-business domain reference; new execution/governance authority is standalone Social Media Studio.
- `docs/architecture.md` — historical 0.8 architecture reference.
- `docs/agent_operability_scenarios.md` — historical 0.8 operability scenarios; standalone operating rules live in the new Skill and contract.
- `docs/provider_benchmark_protocol.md` — owner benchmark method for volatile provider quality/cost evidence.
- `projects/PROJECT_INDEX.json` — retired historical project/program index; not current task or owner-context authority.
- `social_media_studio/data/business_feedback.json` — task-neutral growth/IP/commercial/production feedback relations.
- `audits/EVOLUTION_INDEX.json` — canonical historical Social Media Studio evolution-evidence entrypoint.
- `social_media_studio/legacy/` — self-media-owned domain logic and data consumed only through the explicit Studio adapter boundary; it is not a second runtime.
- binary/media stores — evidence only when bound by stable refs/digests; never business authority by presence alone.

The `social_media_studio` package is the sole Social Media Studio runtime: it owns self-media project briefs, task DAGs, leases, artifact history, review receipts, failure recovery and domain execution. CAOS governs session-level requirement interpretation, material decisions, root-cause investigation, cross-domain authorization and independent acceptance when the owner selects Social Media Studio from CAOS. The Social Media Studio runtime has no CAOS API, runtime, task-ID or lease dependency. specialist content-domain modules are imported only through the explicit `social_media_studio.adapters` boundary; the old fixed-stage controller is not an active execution path.

## Historical media-domain 0.8 models (not a universal execution chain)

The following historical video-specific structures remain callable only where an explicit Social Media Studio media adapter declares the corresponding work. They do not describe the current general-content workflow. New user content demands route through typed contracts; `social_media_studio.engine.StudioEngine` is the only durable scheduler, and direct conversational tasks need no project.

Historical example chain (not a current default or mandatory production order):

`EpisodeIntent -> ClaimSpec -> BeatSpec -> ShotIntent -> EditorialPlan -> ShotContract -> ModelRoutingDecision -> CandidateTake -> ContinuityAssessment -> Promotion -> Timeline -> Editor handoff/roundtrip -> PlatformVariant -> Release -> Experiment/Outcome -> LearningCandidate`

Linked state surfaces remain distinct:

1. **Media-business Program graph** — portfolio/growth/IP/commercial/production tasks and decisions.
2. **Editorial decision state** — episode intent, claims, beats, shot intents and immutable plan versions.
3. **Media context/asset graph** — `Program -> Series -> Episode -> Sequence -> Scene -> Shot -> Take`, versioned assets, references, lineage, evidence and promotion.
4. **Continuity relations** — dimension-level preserve/expect/allowed-change state across shots.
5. **Editorial timeline/interchange** — non-destructive temporal assembly, platform variants and external-editor handoff/return identity.
6. **Experiment/outcome state** — pre-registered tests and typed growth/production/commercial observations.
7. **Operator projection** — recomputable current-Agent view of outcome, ready/blocking actions, stale evidence and recovery refs; never authority.

The fixed-stage work-order engine is not an active controller. New projects use the project-specific dynamic task graph in `social_media_studio`; domain logic is called through the single adapter boundary.

Core 0.8 runtime surfaces:

- `media_graph.py` — stable Context/AssetVersion/Task/Evidence/Decision identities, promotion pointers, persistence, lineage and downstream invalidation;
- `editorial_planning.py` — EpisodeIntent/Claim/Beat/ShotIntent/EditorialPlan and explicit materialization into production contracts;
- `plan_graph_bridge.py` — editorial-plan versions as MediaGraph upstream assets so revisions stale only affected descendants;
- `production_os.py` — editorial-traceable shot/reference/take contracts and generation/promotion/release admission;
- `continuity.py` — cross-shot dimension-level continuity contracts and assessments;
- `model_registry.py` — provider-neutral operation-profile legality plus rubric/calibration-bound, uncertainty-aware Pareto routing;
- `timeline.py` — editor-neutral non-destructive master/variant timeline metadata bound to promoted asset versions;
- `editorial_interchange.py` — external editor/NLE handoff and roundtrip receipts bound to timeline/project/composition identity;
- `experiments.py` — pre-registered hypothesis/variant/metric/guardrail/stop-rule contracts and causal-attribution boundaries;
- `business_objects.py` — typed content-portfolio, distinctive-asset, commercial-fit, rights-package, offer and business-decision objects;
- `business_metrics.py` — platform, production and commercial outcome receipts without one vanity score;
- `operator_view.py` — non-authoritative CURRENT_AGENT projection;
- `owner_behavior_admission.py` — self-media-domain recovery, root-scope analysis, typed evolution and repair-closure rules.

## Reusable business domains, no default task

The four business domains remain selectable capabilities, connected by generic evidence feedback in `social_media_studio/data/business_feedback.json`. A new request creates a new demand-specific brief and graph; no old project, task, subject, platform, IP or source asset is implicitly selected. `projects/PROJECT_INDEX.json` records only retired historical identities. `examples/` contains isolated regression fixtures, not active work. For real work use `STUDIO_ENTRY.md` and `sms-studio intake REQUEST.json`.

## Candidate -> promotion -> release

Safe exploration is not the same as approval.

- Candidate generation requires current capability, rights/consent, truth-policy and budget admission.
- An output remains `CANDIDATE` until explicit promotion evidence/owner decision exists.
- HIGH/HERO/BRAND_TRUTH promotion can require independent/attested review.
- Release remains fail-closed on final-media identity, technical QA, rights, claim/product truth, provenance, disclosure/platform validation and release authority.

## Provider/model strategy

No vendor is permanent architecture. Current provider/model facts are dated observations.

Capability is expressed by operation profile so a model cannot be treated as supporting every combination merely because its feature list separately mentions references, resolution or extension. Production quality evidence must bind compatible rubric/calibration scope and uncertainty. After hard capability/rights/terms/budget floors, production selection uses non-dominated quality vectors and explicit shot priorities rather than a hidden weighted-average authority.

Official vendor documentation establishes capabilities/limits/terms, not our quality ranking. Production observations require the stable benchmark pack in `docs/provider_benchmark_protocol.md` or exact production evidence.

## IP, growth, experiments and commercialization

IP is a reusable distinctive asset system, not only character aesthetics. Canon is versioned and can include structural identity, expression, wardrobe/props, color/material/light, voice/performance, gesture, world grammar and distinctive audio/visual motifs.

Platform derivatives preserve master lineage but re-author hook, packaging, pacing and conclusion for the destination platform. Material packaging/content/IP tests are pre-registered where causal learning matters; `NO_CLEAR_WINNER` and `INCONCLUSIVE` are valid outcomes and multivariable tests cannot masquerade as single-variable causality.

Commercial planning may begin before production when rights, sponsor deliverables, product-truth media or measurement alter the work. Sponsorship never overrides factual/editorial truth. Pricing learns from audience evidence, production cost, rights scope and real outcomes rather than a single static rate card.

## Capability and assurance boundary

Before generation/edit/review/QA/release, handshake the exact current-session capability required by the action. Repository declarations are ceilings, not execution proof.

`DECLARED_ONLY < HARNESS_WIRED < SESSION_EXECUTABLE`; `CHAT_BRIDGED` does not mean independent verification; true isolated assurance requires `ATTESTED_ISOLATED` evidence.

Missing a high-assurance reviewer blocks only operations that require that tier. Missing a real generation provider blocks the affected shot or activates its declared degradation path; it never authorizes fabricated execution.

## CAOS-governed cognition, dogfood and evolution

CAOS parent governance governs the session-level decision and execution discipline: recover the real outcome; compare competing hypotheses and methods; use discriminating tests and counterevidence; inspect exact artifact bytes; diagnose failures at the causal layer; independently replay repairs; and promote learning only with applicability, counterexamples and regression evidence. Social Media Studio owns the domain task graph and execution records; no CAOS runtime/API call is made.

The standalone release contract now records immutable input lineage, invalidates consumers on source replacement, requires rights evidence across used media lineage, enforces exact-digest FFmpeg/FFprobe QA (full decode, stream timing, true peak and black frames), supports attested human cold reads and requires three evidence-backed Red Team findings when configured. See `docs/standalone_social_media_studio.md` and the three outcome/task examples.\n\nThe self-media capability catalog describes verified domain operations; the Studio manifest is the sole runtime authority.


### Isolated regression examples

The examples below exist only to test reusable capabilities; do not resume them or substitute them for an owner demand.

### Run the standalone domain-adapter proof

This sample produces a silent, candidate-only title card with the real local renderer, then binds canonical FFmpeg/FFprobe QA to the exact registered MP4. It requires a local font file and evidence that the font may be used:

```bash
sms-studio --offline-fixture --root ./studio-work init adapter-demo --title "Standalone adapter demo" --brief examples/standalone-domain-adapters.brief.json
sms-studio --offline-fixture --root ./studio-work plan adapter-demo examples/standalone-domain-adapters.tasks.json
sms-studio --offline-fixture --root ./studio-work import-asset adapter-demo rights-clearance ./font-license-evidence.txt --kind document --media-type text/plain --rights-status OWNED
sms-studio --offline-fixture --root ./studio-work import-asset adapter-demo font-asset ./DejaVuSans.ttf --kind font --media-type font/ttf --rights-status LICENSED --metadata examples/adapter-demo-font.metadata.json
```

Claim and complete the authoring task with the exact EditorialPlan JSON, then use `run-adapter` for validation/materialization/rendering and `qa-media` for canonical technical QA. The renderer's receipt explicitly states that the output is silent, candidate-only and not release-authorized.

## Validation

After `pip install -e .`:

```bash
sms-studio --help
sms-studio system-audit --repo-root .
pytest -q
```

The Social Media Studio system audit checks the canonical runtime, parent-governance boundary, adapter registry, project/task graph integrity, artifact lineage, release gates and known production-readiness gaps. It fails closed when the active runtime contract drifts.

CI success is validation evidence, not branch-protection enforcement unless GitHub separately reports branch protection/rulesets as enabled.

## IP Studio OS integration

The personal-IP character canon is owned by the independent IP Studio OS (IPOS); IPOS does not require a CAOS runtime/API call. The standalone program plan models the owner-approved IPOS Video Identity Bundle as an external versioned input and keeps identity-dependent tasks waiting until G2/G7/G8 and rights/provenance pass. The current `social_media_studio.adapters` bridge exposes IPOS inspection, import, exact-version shot binding and continuity operations; identity-dependent work remains blocked until an owner-approved bundle exists. Historical IPOS state is evidence only; recover the current approved export from its actual owner when the demand requires identity.
