# Social Media Studio — Architecture Continuation Audit
**Date:** 2026-11-26  
**Audit baseline:** \`main @ 7cd1cff75fdb807cab8a23c8991dab793573c051\`  
**Scope:** Current authoritative architecture, core domain/runtime boundaries, and active PRs #48, #50, #52, #53.  
**Status:** Preliminary architecture review; **not an architecture promotion or production-readiness sign-off**.

## 1. Executive decision

Keep Social Media Studio as a **modular monolith** with one public \`StudioEngine\` facade, one project-scoped SQLite/event ledger, one scheduler/worker control plane, and one canonical CLI. Preserve both Direct Session and Durable Studio execution surfaces.

Do not introduce a second controller, database, scheduler, permanent agent manager, or framework replacement merely to address the current code coupling. The repository already has a dynamic task DAG, atomic claims, leases, bounded retries, artifact lineage, and invalidation. The unresolved problem is the quality of the domain/application/infrastructure boundaries and the completeness of the owner-demand contract.

**Do not merge PR #52 or #53 yet.** Keep PRs #48 and #50 as a separate review/assurance lane. Refresh and complete the architecture gate before promoting V2 or treating the current draft refactors as the final target architecture.

## 2. Authority and source reconciliation

- Current code authority: GitHub \`main\`, SHA \`7cd1cff75fdb807cab8a23c8991dab793573c051\`.
- Canonical product entry: \`STUDIO_ENTRY.md\`.
- Current architecture authority: \`social_media_studio/data/studio_manifest.json\`.
- Current subsystem ownership: \`social_media_studio/data/subsystem_catalog.json\` plus \`social_media_studio/subsystems.py\`.
- Runtime facade: \`social_media_studio.engine.StudioEngine\`.
- Current architecture V2 document: \`docs/SOCIAL_MEDIA_STUDIO_ARCHITECTURE_V2.md\`.
- V2 acceptance matrix: \`docs/SOCIAL_MEDIA_STUDIO_ARCH_ACCEPTANCE_V2.json\`.

The V2 acceptance matrix is still \`ARCHITECTURE_CANDIDATE_NO_RUNTIME_AUTHORITY\`, frozen at \`1cbc3acf0491ecaa297576372f80163d8c255606\`. It contains 35 scenarios, all with \`runtime_verified=false\`; all but the exact-shape scenario require independent design review. Its frozen source baseline predates the current main SHA. Preserve the historical baseline, but do not use it as a current implementation map until a new reconciliation is recorded.

The V2 document itself correctly says architecture promotion requires a current source map, no unresolved conceptual contradiction, a pinned revision, rollback evidence, and both conceptual and executable-mapping adversarial reviews. Those conditions are not yet evidenced.

## 3. What is already structurally sound

The current manifest and inspected source establish these existing strengths:

1. One canonical startup authority and one \`sms-studio\` CLI.
2. Direct-session work does not require an artificial project or task graph; durable work uses the existing Studio ledger.
3. One project-scoped SQLite WAL store, append-only events, versioned artifacts, SHA-256 identity, artifact-input lineage, and downstream invalidation.
4. Dynamic per-demand task DAGs, atomic claims, leases, bounded retries, and parallel execution only across independent dependencies.
5. Separate product/business axes, professional capability groups, reusable roles/methods, media-object hierarchy, and task dependency graph.
6. Typed \`DeliverableContract\` support for ten deliverable types, explicit variants and media shapes, and identity-scope validation.
7. Deliverable-specific quality criteria. The assurance planner explicitly returns \`PLAN_ONLY_NOT_AN_EVALUATION\`; it does not claim actual quality, independent review, or release authorization.
8. Editorial and visual inspectors explicitly limit themselves to structural validation. Research evidence inspection verifies source bytes and quoted excerpts, not semantic truth.
9. No automatic publication. External generative-provider execution is not connected by the repository and must be checked against the actual current session capability.
10. CAOS remains the read-only parent governance authority; SMS does not import or duplicate the CAOS runtime. Native CAOS selection/activation is not verified.

The current source inventory records 16 internal subsystems, 17 domain adapters, and six local production operations. These are not 17 generation engines or six complete creative capabilities.

## 4. Architecture gaps and findings

### A1 — P1: V2 architecture gate is stale and unpromoted

**Evidence:** V2 acceptance baseline \`1cbc3acf...\` versus current main \`7cd1cff...\`; 35/35 scenarios remain \`runtime_verified=false\`; document status is candidate/no runtime authority.

**Impact:** Later code changes cannot be evaluated against a current, pinned architecture map. Promoting the document now would convert stale assumptions into authority.

**Required action:** Create a current main/active-PR source reconciliation, map every scenario to its actual contract, code path, positive oracle and forbidden effect, then run the conceptual and executable-mapping adversarial reviews. Keep V2 unpromoted until those reviews close.

### A2 — P1: Deliverables are typed; the owner demand is not yet typed

**Evidence:** \`domain/contracts.py\` defines \`DeliverableContract\`, \`DeliverableVariant\`, and \`MediaShape\`. \`scope.py\` still binds a general-purpose brief with a goal and deliverable list; it validates optional typed deliverable specs but has no \`DemandContract\` for original-goal identity, correction chronology, hard constraints, soft preferences, prohibitions, expected outcome, authorization, and unresolved unknowns.

**Impact:** The system can type what must be produced more precisely than it types why it is being produced and how later owner corrections supersede earlier premises. That weakens revision propagation and decision/effect binding.

**Required action:** Implement a pure, versioned demand contract before further planner refactors. Preserve the original owner goal and ordered correction references; distinguish hard constraints from preferences; keep authorization explicit and non-inferred; bind deliverables by stable IDs. Do not make a typed demand automatically create tasks or authorize effects.

### A3 — P1: PR #52 is a successful extraction, but not yet a one-way application boundary

**Evidence:** PR #52 head \`c37830242f44a37ce9075c9f42c99ee6b21579c4\`; exact-head CI succeeded with 457 tests. The extracted \`application/project_tasks.py\` is 650 lines. The remaining \`engine.py\` is 2,496 lines (3,135 on current main). \`ProjectTaskEnginePort\` exposes 15 methods; the service calls 16 methods on the engine, including project/task methods that the facade delegates back to this same service. The service also contains 29 \`connection.execute\` calls.

**Impact:** This is useful mechanical separation and preserves the public facade, but the service still relies on a broad engine-shaped port and re-enters the facade for operations it now owns. It is not yet a clean application-to-infrastructure boundary. Future extractions could reproduce the same coupling.

**Required action:** Before merge, make the dependency direction one-way. The application service should call its own project/task logic directly and depend only on the smallest explicit persistence, workspace, and event ports it needs. Keep one ledger, schema, transaction semantics, event ordering, CLI, scheduler, and public \`StudioEngine\` contract. Add parity and invalidation tests for the extracted boundary.

### A4 — P1: PR #53 is not merge-ready; the registry is not yet an enforceable operation contract

**Evidence:** PR #53 head \`ccc8c78797f88c04169421902a73028c554ad001\`; exact-head CI failed in \`system_audit.py\` at the call to \`supports_domain_adapter\`, which is not imported or defined in that module. A second call exists later in the same audit. The run stopped before topology audit, tests, and runtime smoke.

The proposed \`DomainAdapterSpec\` is a useful metadata record, but:
- \`required_config\`, \`output_contract\`, \`effect_scope\`, and \`assurance_ceiling\` are descriptive fields not enforced by the dispatcher;
- the handler type remains \`Callable[..., tuple[dict, dict]]\`, not a per-operation typed input/output contract;
- \`DOMAIN_ADAPTERS\` is a mutable dict while \`SUPPORTED_DOMAIN_ADAPTERS\` is a frozen snapshot;
- \`public_record()\` overwrites effect/promotion/publication fields with \`False\`, rather than reflecting the registered spec;
- handlers receive the full engine object rather than a narrow adapter context.

**Impact:** The source has been modularized, but the registry is not yet the single enforceable authority its name and PR description imply. The CI failure is the immediate blocker; the metadata/dispatch mismatch is the architectural blocker.

**Required action:** Use one registry object as the membership authority in the audit; make the registry immutable; preserve declared effect values; add operation-specific config validation and output contracts at dispatch; and expose only the minimum project-local context required by handlers. Then run the full exact-head audit, tests, and smoke.

### A5 — P1: High-assurance review is fail-closed, but no production reviewer is trusted yet

**Evidence:** PR #48 head \`744cfb0eff6a02140ececaf08159418ce58b0f38\` passed 464 tests. PR #50 head \`48260be28bf44d51eb912024a254839b2462e8ce\` passed 468 tests. PR #48 adds signed DSSE/in-toto Ed25519 execution evidence, exact artifact/report/input binding, an immutable per-project nonce ledger, and release-time re-verification. The production \`review_executors.json\` trust registry is intentionally empty.

**Impact:** High-assurance review is correctly blocked until a reviewer/executor is independently assessed and registered. A reviewer name, model label, or ordinary metadata review must not be presented as independent execution proof.

**Required action:** Keep #48 and #50 separate from the core extraction. Review their code and merge only when the relevant review, exact-head CI, rollback and acceptance gates are satisfied. Do not populate the production trust registry without real executor evidence.

### A6 — P1: Repository tests do not prove owner-grade creative output

**Evidence:** The current editorial, visual, research and quality modules explicitly disclaim semantic/creative proof. Quality plans require actual outputs to be examined, but report \`quality_verified=false\`, \`independent_review_verified=false\`, and \`owner_outcome_verified=false\`. The provider-generation boundary remains disconnected. PR #50 tests content-specific gate routing; its deterministic image/video fixture bytes are not visual or media-quality evidence.

**Impact:** Green tests prove structural behavior, not that writing sounds like the owner's intended voice, an image works at mobile size, a video tells the intended story, or a platform package achieves its actual communication goal.

**Required action:** Add owner-outcome trials for short copy, long article, platform package, static/multi-aspect image, media transform with the exact audio promise, original video, and research report. Inspect actual outputs and keep structural, technical, creative, independent, and owner acceptance as distinct results.

### A7 — P2: The capability split is useful, but must not become a second capability authority

The main branch still has a 1,091-line \`adapters.py\` with a large conditional dispatcher. PR #53's domain package is directionally useful. Preserve one source of truth per concept: domain operation, production operation, role, method, provider availability, and reviewer trust are different registries and must not be collapsed or duplicated. Manifest references must be read back against the actual executable registry.

## 5. Adversarial review summary

**Conceptual/product review:** The target is coherent if SMS remains task-neutral and owner-outcome driven. Direct and durable surfaces are both necessary. Content-specific gates must prevent a short post or article from inheriting video-only stages. CAOS cognition must remain the parent authority rather than a copied child controller. IPOS canon must remain separately custodied. Publication and provider effects must remain separately authorized.

**Executable-mapping review:** The gate does not pass yet. The V2 source baseline is stale; the demand model is incomplete; PR #52's service boundary remains engine-shaped; PR #53's registry is descriptive rather than enforceable and its exact-head CI fails; high-assurance production trust is empty; and real creative owner outcomes remain untested.

These are model-authored adversarial reviews based on the inspected repository sources. They are not external independent sign-off and do not promote V2.

## 6. Selected architecture and implementation order

1. **Freeze and reconcile authority:** preserve current main and PR SHAs; refresh the V2 source map without overwriting the historical frozen baseline.
2. **Complete M2 — typed demand:** add \`DemandContract\` and revision/correction identity alongside the existing \`DeliverableContract\`; add positive and negative tests; no task or effect side effects.
3. **Complete M3 — capability contracts:** make the domain registry immutable and executable-contract aware; keep domain adapters separate from production executors and provider snapshots.
4. **Complete M4 — decision/effect binding:** bind local Studio task effects to exact demand revision, task revision, current source/input digests, falsifier and rollback. CAOS remains external parent governance; do not claim native activation.
5. **Rework M5 — project/task service:** make the PR #52 extraction one-way and port-based, preserving one StudioEngine facade and the existing ledger.
6. **Review M7 — independent assurance:** assess PR #48/#50 separately; high assurance remains blocked until a real trusted executor is registered.
7. **Run real owner-outcome trials:** validate actual deliverables, not only JSON structures or fixture files.
8. **Only then consider promotion/cutover:** exact-head CI, source ownership audit, independent code/design review, rollback, real deliverable inspection, and owner acceptance must all be read back.

Do not start by replacing the scheduler or splitting every file into a new package. Create a boundary only when a real contract and regression oracle justify it.

## 7. Acceptance and rollback rules

- No public API, CLI, schema, task status, event ordering, lease, retry, artifact lineage, or release behavior changes without a pinned compatibility test.
- No second scheduler, ledger, workspace authority, CAOS runtime, IPOS canon, or automatic publisher.
- No adapter may infer provider availability, external permission, candidate promotion, publication, or creative quality from registration metadata.
- A changed demand invalidates only the decisions/tasks/artifacts that depend on the changed revision; unaffected branches remain valid.
- A failed exact-head check reopens the root cause and the selected boundary; it is not repaired by stacking another local special case.
- Roll back the isolated PR/branch if behavior, authority, state custody, or acceptance changes unexpectedly.

## 8. Work performed in this audit

- Read the canonical entry, current manifest, subsystem catalog, deliverable contracts, assurance/editorial/visual/research/identity contracts, intake boundary, and relevant runtime/registry source.
- Read the V2 architecture proposal and all 35 acceptance scenario declarations.
- Inspected exact heads, changed files, CI status, and review state for PRs #48, #50, #52, and #53.
- Inspected the failing PR #53 workflow log and the relevant dispatcher/registry/audit code.
- No runtime source, manifest, CAOS, IPOS, project data, provider, or publication state was modified.
- No PR was merged. This report records a preliminary architecture decision and the remaining open gates; it is not a claim that the full system audit or production acceptance is complete.
