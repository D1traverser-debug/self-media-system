# Standalone Video Studio — Integrated Program and Production Contract Audit

Date: 2026-11-17
Owner: DOMAIN:video
Candidate: V-20261117-01-STANDALONE-VIDEO-STUDIO-INTEGRATED-PROGRAM
Branch: `refactor/video-production-integrated-20261117`
Verified code head before continuation-record updates: `3e823be92de41d9642a40292863689a7a68a0fd6`
Exact-head CI: [run 44006872263](https://github.com/D1traverser-debug/video-growth-agent/actions/runs/44006872263)

## 1. Decision

The standalone Video Studio is now the default generic Video execution entry. The new native `video_studio` package owns the standalone control plane and `vga-studio` CLI. The historical `vga` command remains a compatibility interface. The runtime has no CAOS runtime/API/Skill dependency and does not modify CAOS.

The integrated Program is `ai-self-media-commercialization`, a 50-task graph spanning media growth, original digital IP, commercialization and production. It imports repository-owned context through immutable SHA-256-bound artifacts and leaves missing owner-controlled inputs explicitly blocked.

## 2. Root-cause findings addressed

### 2.1 Claimed artifact packets omitted producer provenance

The rights-clearance validator could identify the claimed artifact but could not establish who produced it or which task produced it. A reviewer-name string alone was insufficient evidence.

**Change:** claimed work packets now expose `producer_id` and `produced_by_task`. Render rights clearance requires the reviewer ID to match the artifact producer, the producer task to be a completed human task, and the exact clearance artifact to appear in that task's completed outputs. The clearance document must match every consumed source by artifact ID, SHA-256, rights status and registered evidence references.

**Verification:** positive case plus negative cases for agent-produced clearance, reviewer mismatch, producer mismatch, wrong source digest, wrong source artifact ID, wrong rights status, uncleared source rights and unregistered evidence references.

### 2.2 Re-importing unchanged source assets could invalidate valid consumers

A repeated import of the same file could create a new artifact version and stale downstream tasks even though source bytes and metadata had not changed.

**Change:** exact re-imports are idempotent when source digest, kind, media type, rights status and metadata match and the stored file still verifies against its digest. A real source or metadata change still creates a new immutable version and invalidates consumers.

### 2.3 Multi-file context setup lacked a single preflight boundary

A user needed to import several context files before planning. Repeated single-file commands were cumbersome and could leave a partially imported context set if a later path or metadata entry failed.

**Change:** `vga-studio import-manifest` validates the complete manifest, unique artifact names, path existence, regular-file status, metadata and rights enums, and task-output name collisions before the first mutation. Relative paths resolve from the manifest directory. The manifest import is idempotent through the engine's artifact identity rules.

### 2.4 Program authority references were descriptive rather than execution-bound

A path in a brief or task authority reference did not itself guarantee that the worker received the exact bytes as a verified input.

**Change:** the integrated context manifest imports the exact existing Video/IPOS reference files; the 50-task graph declares corresponding artifact names as actual inputs. Claim packets therefore bind immutable artifact IDs, versions and SHA-256 values. Contract tests reject missing manifest mappings or unbound authority references.

The context manifest intentionally does not fabricate the Jensen/Alice source video or an owner-approved IPOS bundle. IPOS remains the sole identity authority.

### 2.5 The repository lacked one honest, executable system-level readiness audit

Individual tests and smoke commands did not provide one stable command distinguishing structural integrity from actual production readiness.

**Change:** `vga-studio system-audit --repo-root .` checks standalone entry/governance, runtime dependency boundaries, adapter registration, local production executors, digest-bound Program authority inputs, example graph execution/readiness and hard release gates. It performs no paid provider call and mutates no user workspace.

The audit returns:
- structural status: PASS;
- production readiness: PARTIAL;
- missing repository-registered generative-video executor;
- missing owner-supplied Jensen/Alice source video;
- missing owner-approved IPOS READY_FOR_VIDEO bundle.

This is intentional fail-closed behavior, not a green production-release claim.

## 3. Default Program workflow

The documented default entry now initializes the integrated Program, imports its context manifest, plans the canonical 50-task graph and exposes task readiness:

```bash
python -m pip install -e .
vga-studio --root ./studio-work init ai-self-media-commercialization --title "AI Self-Media Commercialization" --brief examples/ai-self-media-commercialization.brief.json
vga-studio --root ./studio-work import-manifest ai-self-media-commercialization examples/ai-self-media-commercialization.context.json
vga-studio --root ./studio-work plan ai-self-media-commercialization examples/ai-self-media-commercialization.tasks.json
vga-studio --root ./studio-work status ai-self-media-commercialization
vga-studio --root ./studio-work tasks ai-self-media-commercialization
vga-studio system-audit --repo-root .
```

Independent growth, advertiser, production-economics, provider-benchmark and Jensen fact-research tasks can run without waiting for unavailable media or identity assets. Tasks that require exact owner-controlled media remain WAITING_INPUT. IPOS import remains dependency-gated behind the MediaGraph bootstrap and exact approved bundle.

## 4. Exact verification

CI run `44006872263`, exact tested head `3e823be92de41d9642a40292863689a7a68a0fd6`:

- pytest: **343 passed**;
- standalone Video Studio system audit: PASS;
- standalone Video Studio CLI smoke: PASS;
- integrated Program context/readiness smoke: PASS;
- installed agentic CLI smoke: PASS.

The system-audit regression also verifies that production readiness is PARTIAL and that no CAOS dependency, paid provider call or automatic publication is asserted.

## 5. Release and authority boundaries

- No CAOS repository, source, Skill, configuration or PR was modified.
- IPOS canon was not modified; IPOS remains the sole identity authority.
- No owner-supplied Jensen/Alice source media was invented or substituted.
- No owner-approved IPOS identity bundle was fabricated.
- No paid provider call, media generation, promotion or publication was performed in this integration pass.
- Generated media and graph registration remain subject to exact rights, evidence, technical QA, human review, Red Team, platform disclosure and release gates.
- A structural audit PASS is not a finished video, a production-readiness PASS or release authorization.

## 6. Remaining production work

1. Run independent Program research lanes and persist their evidence-backed outputs.
2. Obtain the exact owner-supplied Jensen/Alice source video and inspect its bytes, digest, provenance, identity/likeness and rights.
3. Obtain an owner-approved IPOS READY_FOR_VIDEO bundle; validate and import it without changing IPOS canon.
4. Perform a current-session provider capability handshake before any generative-video operation; verify model/operation, availability, cost, rights and output constraints.
5. Execute a real episode through editorial planning, shot contracts, timeline, technical QA, human cold-read, Red Team, platform disclosure and release evidence.
6. Keep no-auto-publish and candidate-only behavior until all mandatory gates pass.

## 7. PR status

The integrated branch contains the prior standalone hard-gate work plus 42 additional commits that close the context, provenance, default Program and system-audit gaps. It is intended to supersede the earlier PR #36, not to merge around its hard gates. The consolidated PR is #37. Mainline merge and post-merge verification remain separate from the branch CI evidence above.
