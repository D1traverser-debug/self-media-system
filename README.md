# Video Growth Agent

CAOS-governed Video Production Studio for research, creative development, parallel media production, audiovisual QA, release preparation and evidence-based learning. When Video is selected in a CAOS-governed session, CAOS parent governance is mandatory; the Video runtime remains technically independent.

## Current authority

- `STUDIO_ENTRY.md` — only startup and operating entry for new Video work.
- `docs/standalone_video_studio.md` — Video-owned goal, decision, dynamic DAG, execution, artifact, review, failure and learning method.
- `video_studio/data/studio_manifest.json` — canonical runtime and parent-governance contract; no CAOS runtime/API dependency.
- `video_studio/engine.py`, `cli.py`, `media.py` — canonical standalone project state, concurrent task claims, artifact lineage and deterministic FFmpeg/FFprobe QA.
- `video_studio/adapters.py` — explicit, task-bound adapters for EditorialPlan, ShotContract, IPOS shot binding, IPOS continuity, MediaGraph bootstrap, Timeline, continuity, shot routing, business metrics, supplementary audio QA and deterministic local graphic rendering.
- `skills/video-growth-agent/SKILL.md` — self-contained Video-owned agent operating instructions.
- `domain_manifest.json` and `capabilities.json` — Video-owned domain identity and capability contracts consumed by the canonical Studio.
- `docs/product_requirements.md` — historical 0.8 product-requirements baseline; new operating authority is the standalone contract.
- `docs/media_business_os.md` — 0.8 media-business domain reference; new execution/governance authority is standalone Video Studio.
- `docs/architecture.md` — historical 0.8 architecture reference.
- `docs/agent_operability_scenarios.md` — historical 0.8 operability scenarios; standalone operating rules live in the new Skill and contract.
- `docs/provider_benchmark_protocol.md` — owner benchmark method for volatile provider quality/cost evidence.
- `projects/PROJECT_INDEX.json` — child-owned project/program discovery authority.
- `video_studio/data/business_feedback.json` — task-neutral growth/IP/commercial/production feedback relations.
- `audits/EVOLUTION_INDEX.json` — canonical Video evolution-evidence entrypoint.
- `video_growth_agent/` — Video-owned domain logic and data consumed only through the explicit Studio adapter boundary; it is not a second runtime.
- binary/media stores — evidence only when bound by stable refs/digests; never business authority by presence alone.

The `video_studio` package is the sole Video runtime: it owns Video project briefs, task DAGs, leases, artifact history, review receipts, failure recovery and domain execution. CAOS governs session-level requirement interpretation, material decisions, root-cause investigation, cross-domain authorization and independent acceptance when the owner selects Video from CAOS. The Video runtime has no CAOS API, runtime, task-ID or lease dependency. Video domain modules are imported only through the explicit `video_studio.adapters` boundary; the old fixed-stage controller is not an active execution path.

## Video domain model and production architecture

Video 0.8 makes the media-business system operable from natural-language/editorial intent through production and learning rather than starting mechanically at the Shot layer.

The current executable chain is:

`EpisodeIntent -> ClaimSpec -> BeatSpec -> ShotIntent -> EditorialPlan -> ShotContract -> ModelRoutingDecision -> CandidateTake -> ContinuityAssessment -> Promotion -> Timeline -> Editor handoff/roundtrip -> PlatformVariant -> Release -> Experiment/Outcome -> LearningCandidate`

Linked state surfaces remain distinct:

1. **Media-business Program graph** — portfolio/growth/IP/commercial/production tasks and decisions.
2. **Editorial decision state** — episode intent, claims, beats, shot intents and immutable plan versions.
3. **Media context/asset graph** — `Program -> Series -> Episode -> Sequence -> Scene -> Shot -> Take`, versioned assets, references, lineage, evidence and promotion.
4. **Continuity relations** — dimension-level preserve/expect/allowed-change state across shots.
5. **Editorial timeline/interchange** — non-destructive temporal assembly, platform variants and external-editor handoff/return identity.
6. **Experiment/outcome state** — pre-registered tests and typed growth/production/commercial observations.
7. **Operator projection** — recomputable current-Agent view of outcome, ready/blocking actions, stale evidence and recovery refs; never authority.

The fixed-stage work-order engine is not an active controller. New projects use the project-specific dynamic task graph in `video_studio`; domain logic is called through the single adapter boundary.

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
- `owner_behavior_admission.py` — Video-domain recovery, root-scope analysis, typed evolution and repair-closure rules.

## Reusable business domains, no default task

The four business domains remain selectable capabilities, connected by generic evidence feedback in `video_studio/data/business_feedback.json`. A new request creates a new demand-specific brief and graph; no old project, task, subject, platform, IP or source asset is implicitly selected. `projects/PROJECT_INDEX.json` records only retired historical identities. `examples/` contains isolated regression fixtures, not active work. For real work use `STUDIO_ENTRY.md` and `vga-studio intake REQUEST.json`.

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

CAOS parent governance governs the session-level decision and execution discipline: recover the real outcome; compare competing hypotheses and methods; use discriminating tests and counterevidence; inspect exact artifact bytes; diagnose failures at the causal layer; independently replay repairs; and promote learning only with applicability, counterexamples and regression evidence. Video Studio owns the domain task graph and execution records; no CAOS runtime/API call is made.

The standalone release contract now records immutable input lineage, invalidates consumers on source replacement, requires rights evidence across used media lineage, enforces exact-digest FFmpeg/FFprobe QA (full decode, stream timing, true peak and black frames), supports attested human cold reads and requires three evidence-backed Red Team findings when configured. See `docs/standalone_video_studio.md` and the three outcome/task examples.\n\nThe Video domain capability catalog describes verified domain operations; the Studio manifest is the sole runtime authority.


### Isolated regression examples

The examples below exist only to test reusable capabilities; do not resume them or substitute them for an owner demand.

### Run the standalone domain-adapter proof

This sample produces a silent, candidate-only title card with the real local renderer, then binds canonical FFmpeg/FFprobe QA to the exact registered MP4. It requires a local font file and evidence that the font may be used:

```bash
vga-studio --offline-fixture --root ./studio-work init adapter-demo --title "Standalone adapter demo" --brief examples/standalone-domain-adapters.brief.json
vga-studio --offline-fixture --root ./studio-work plan adapter-demo examples/standalone-domain-adapters.tasks.json
vga-studio --offline-fixture --root ./studio-work import-asset adapter-demo rights-clearance ./font-license-evidence.txt --kind document --media-type text/plain --rights-status OWNED
vga-studio --offline-fixture --root ./studio-work import-asset adapter-demo font-asset ./DejaVuSans.ttf --kind font --media-type font/ttf --rights-status LICENSED --metadata examples/adapter-demo-font.metadata.json
```

Claim and complete the authoring task with the exact EditorialPlan JSON, then use `run-adapter` for validation/materialization/rendering and `qa-media` for canonical technical QA. The renderer's receipt explicitly states that the output is silent, candidate-only and not release-authorized.

## Validation

After `pip install -e .`:

```bash
vga-studio --help
vga-studio system-audit --repo-root .
pytest -q
```

The Video Studio system audit checks the canonical runtime, parent-governance boundary, adapter registry, project/task graph integrity, artifact lineage, release gates and known production-readiness gaps. It fails closed when the active runtime contract drifts.

CI success is validation evidence, not branch-protection enforcement unless GitHub separately reports branch protection/rulesets as enabled.

## IP Studio OS integration

The personal-IP character canon is owned by the independent IP Studio OS (IPOS); IPOS does not require a CAOS runtime/API call. The standalone program plan models the owner-approved IPOS Video Identity Bundle as an external versioned input and keeps identity-dependent tasks waiting until G2/G7/G8 and rights/provenance pass. The current `video_studio.adapters` bridge exposes IPOS inspection, import, exact-version shot binding and continuity operations; identity-dependent work remains blocked until an owner-approved bundle exists. Historical IPOS state is evidence only; recover the current approved export from its actual owner when the demand requires identity.
