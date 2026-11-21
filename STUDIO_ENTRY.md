# Video Production Studio — Canonical Entry

**Status:** `REBUILD_IN_PROGRESS`  
**Startup authority:** this file  
**Agent instructions:** `skills/video-growth-agent/SKILL.md`  
**Operating contract:** `docs/standalone_video_studio.md`  
**Runtime:** `video_studio.engine.StudioEngine`  
**CLI:** `vga-studio`  
**Manifest:** `video_studio/data/studio_manifest.json`

## Mission

Turn the owner's actual media goal into the requested finished media package. The primary acceptance oracle is the exact delivered media and its independently inspected evidence—not a plan, task graph, prompt pack, renderer declaration or green CI run.

## Product boundary

Video production is the primary product. Each project chooses its own production family, visual grammar, format, tools and quality rubric. Media growth, original digital IP and commercialization are optional workstreams; include them only when the owner's brief creates a real dependency.

IPOS remains the sole authority for original-character identity canon, likeness and identity rights. Video may consume only exact owner-approved, versioned IPOS exports. Video must not create a competing character canon.

Generic video-production intent has no default business Program. Resume an existing project only when the owner supplies its exact ID/name/alias or the current task clearly continues that project. Otherwise compile the new outcome brief and create a project-specific workspace. The AI self-media commercialization Program is an optional business project, not the default destination for every video request.

## Governance boundary

The Video runtime is standalone: it does not import, call, require or wait for a CAOS runtime, API, parent task ID or parent lease. This is runtime independence, **not permission to bypass CAOS governance**. When the active ChatGPT session is CAOS-governed, follow CAOS's parent-level decision loop, execution loop and independent acceptance externally. Do not modify the CAOS repository, files, branches, pull requests, configuration or installed skills.

## Authority order

1. Current explicit owner request and corrections.
2. The explicitly selected project's owner-approved brief and revision history.
3. Verified source facts, asset bytes, rights, consent and provenance.
4. Approved IPOS identity bundle when original identity is involved.
5. Exact artifact digests and independent review/release evidence.
6. Candidate hypotheses and recommendations.

A lower authority cannot silently override a higher one. Preserve hard requirements separately from preferences, examples, assumptions and unknowns.

## New-task startup

1. Recover the complete outcome, prior corrections, prohibitions, deliverables and acceptance conditions. Do not ask the owner to repeat known context.
2. Classify the request as system maintenance, a new media job, continuation of an explicitly selected project, or an optional business-workstream task.
3. Inspect the selected project's current state, exact assets, task graph, event history, failures, open reviews and artifact digests. Do not infer state from filenames or stale chat notes.
4. Compile an outcome contract: audience, content promise, production family, deliverables, format, craft expectations, hard constraints, preferences, budget, rights, disclosure, quality rubric and unknowns.
5. Build the smallest project-specific DAG that represents real dependencies. Parallelize independent research, concepts, rights checks, shot tests, sound tests and packaging work.
6. Verify the exact execution capability before dispatch. A declared provider, model, role or executor is not execution proof.
7. Prototype the highest-risk quality assumption with a near-final sample before expensive/full production.
8. Execute through the current session, a verified local tool, an explicitly connected external provider or a named human. Register exact output bytes, SHA-256, provenance and rights.
9. Independently inspect the actual final media and package. Run technical, editorial, visual/motion, audio, subtitle, rights and platform checks required by the brief.
10. Release-check the exact final artifact and persist failures, decisions and reusable learning with evidence.

## Executor classes and capability assurance

- **agent:** work performed by the current agent session or a separately verified worker. The local CLI does not auto-spawn an LLM worker.
- **tool:** deterministic local code with a registered operation, declared inputs/outputs and passing tests.
- **external:** a connected provider or service. Check the exact current operation, input roles, output limits, rights/terms, availability and price. Paid or externally consequential actions require explicit owner approval.
- **human:** owner decision, independent human review or other named human action.

Session tools (image/video/audio generation, editing or transcription) are not persistent repository integrations. Check their availability in the current session and register their actual outputs into the Video project. Do not claim a persistent provider adapter merely because a ChatGPT tool is available.

Assurance vocabulary: `DECLARED_ONLY < HARNESS_WIRED < SESSION_EXECUTABLE`. A session tool call proves only that operation in that session. It does not prove durable repository integration, independent review or release approval.

## Safety and production rules

- No paid credits, subscriptions, GPU rental, upload, publication or owner-device action without explicit authorization.
- No fabricated source footage, measurements, provider runs, artifact paths, rights evidence, review receipts or publication status.
- No arbitrary project-supplied Python execution without a genuine OS-level sandbox and explicit authorization. A config boolean is not a sandbox.
- Keep generated candidates, promoted assets, final release and publication as separate states.
- Technical QA cannot substitute for visual craft, editorial truth, audio quality, rights or owner acceptance.
- A contact sheet or prompt pack supports review; it does not replace inspecting the actual image/video bytes at normal viewing size/speed.

## Quick start

```bash
python -m pip install -e .
vga-studio --root ./studio-work init episode-001 --title "Episode 001" --brief examples/technology-explainer.brief.json
vga-studio --root ./studio-work plan episode-001 examples/technology-explainer.tasks.json
vga-studio --root ./studio-work status episode-001
vga-studio --root ./studio-work audit episode-001
```

## Completion rule

The project is complete only when every requested deliverable exists as the exact expected file/type, the editable source/dependencies required by the brief are included, all applicable independent reviews and technical checks pass against the exact digests, rights/consent/disclosure are cleared, and the final package is reproducible. Unavailable subjective checks and unresolved unknowns must be disclosed. No automatic publication.
