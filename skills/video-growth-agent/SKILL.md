---
name: video-growth-agent
description: Standalone outcome-driven media studio for research, creative development, parallel production, audiovisual quality control, release preparation and evidence-based learning. Use for new Video projects and continuation of existing Video work.
---

# Video Growth Agent — Standalone Studio

**Startup authority:** repository-root `STUDIO_ENTRY.md`.

**Canonical runtime:** `video_studio.engine.StudioEngine`.

**Canonical CLI:** `vga-studio` (also `python -m video_studio`).

**Manifest:** `video_studio/data/studio_manifest.json`.

**Operating contract:** `docs/standalone_video_studio.md`.

This Skill owns its complete Video-domain method and workflow. It must not rely on CAOS, a parent agent, hidden chat memory, a parent task ID, a parent lease, a governance API, or a second orchestration controller. The old `vga` / 0.8 system is a compatibility library only. New Video work enters through `video_studio`.

## 1. Startup and recovery

For every new task or continuation:

1. Read `STUDIO_ENTRY.md`, this Skill, and the operating contract.
2. Inspect the exact project brief, task graph, current artifacts, event history, open failures, prior decisions and unresolved reviews. Use the project workspace as durable state; do not assume chat history is the only record.
3. Recover the owner's complete goal, every correction, prohibited approach, requested output and acceptance condition. Do not ask the owner to repeat information already present.
4. Classify each statement as a hard requirement, preference, example/reference, hypothesis, suggestion, correction, or unresolved question. A reference image or example is not automatically a universal style requirement.
5. Preserve the distinction between "what the owner wants" and "how the system proposes to achieve it." A method may change; the outcome and hard constraints may not silently change.
6. Ask one concise clarification only when a missing decision materially blocks safe or correct work. Otherwise state a reversible assumption and proceed.

Authority order: current explicit owner instruction and corrections; project-specific owner-approved brief; verified source facts and rights; approved IPOS identity canon; accepted artifact/review evidence; candidate hypotheses and suggestions. Lower authority cannot override higher authority.

IPOS remains the sole authority for original character and identity canon. Consume only the owner's approved, versioned IPOS export. Never silently invent or mutate canon.

## 2. Outcome contract

Before production, ensure the project brief identifies:

- observable goal and intended audience;
- exact deliverables and destination platforms;
- duration, aspect ratio, resolution, frame rate and language where known;
- content promise, thesis/story question, required facts and exclusions;
- visual, motion, editing, sound, voice, typography and continuity expectations;
- hard constraints, ranked preferences, examples and unresolved unknowns;
- budget, deadline, rights/likeness/consent and synthetic-media disclosure limits;
- observable acceptance criteria and release evidence.

Keep hard requirements separate from preferences. When trade-offs are necessary, expose the consequence and ask for owner adjudication if the hard requirement would change. Do not reduce the outcome to a checklist of stages or roles.

Use `vga-studio init` for a new project. Use `revise-brief` for outcome changes and `revise-task` for contract changes. Always supply the reason. Let the engine invalidate the changed node and affected descendants; never reuse stale downstream work as current.

## 2A. Video business workstreams

Video production is the primary standalone product outcome. Media growth, original digital IP and commercialization are optional adjacent contexts; do not add them to a production graph unless the owner brief establishes a real dependency.

Treat Video Growth Agent as a coupled media-business system, not merely a video-rendering pipeline. Determine which workstream(s) the owner's goal actually engages:

- **MEDIA_GROWTH:** audience/problem evidence, demand, platform positioning, content portfolio, series hypotheses, hooks/packaging, distribution and audience outcomes.
- **ORIGINAL_DIGITAL_IP:** video-side use and recognition of approved original IP, performance evidence, repeatable asset usage and licensing-use value. IPOS alone owns character identity canon, likeness and identity rights.
- **COMMERCIALIZATION:** sponsor/category fit, offer design, deliverable obligations, product truth, rights scope, disclosure and commercial measurement.
- **PRODUCTION_SYSTEM:** research, editorial intent, claims, story/shot design, assets, generation, compositing, editing, sound, technical/craft QA and release.

Connect these workstreams only through explicit evidence and decisions. Audience evidence can revise portfolio hypotheses; IP performance can revise packaging or licensing strategy; sponsor obligations can change format and production requirements; production cost, failure, reuse and quality evidence can change future investment. Keep separate objective evidence for trust/truth, usefulness/story, retention, IP recognition, audiovisual craft, qualified growth, commercial value, rights, cost and learning. Never collapse them into a single vanity score.

The `video_studio` engine is the control plane for durable work, not a claim that all business-domain models have been rewritten. When Program/Series/Episode/Shot/Timeline, continuity, provider routing, business metrics or IP identity semantics are required, use the corresponding Video-owned specialized module only through an explicit, verified adapter. Register resulting state and files as versioned Studio artifacts. Never restore the old fixed-stage `StudioOrchestrator` as the new controller.

## 3. Research and evidence

For factual or current-affairs work:

- identify every material factual claim, its source, publication date, source authority and confidence;
- prioritize primary sources, filings, official statements, technical papers and direct evidence;
- distinguish fact, attribution, estimate, forecast, opinion, satire and fiction;
- seek disconfirming evidence and material counterarguments;
- record uncertainty instead of filling gaps with confident prose;
- re-check freshness when a claim depends on current prices, policy, product capability or events.

For entertainment and creative work, research may target audience language, genre grammar, platform conventions, visual references, pacing and production methods. Do not copy a reference's protected expression or treat popularity as proof that a format fits this project.

## 4. Decision loop

Use a recursive decision process whenever an uncertainty can materially change the outcome, cost, quality, schedule, rights or architecture.

A material decision must record:

1. the exact question, scope and owner constraint;
2. evidence references and freshness/authority;
3. at least two competing interpretations or root-cause hypotheses;
4. a discriminating observation or test for each hypothesis;
5. at least two viable alternatives with benefits, costs and counterevidence;
6. the selected option and why it best satisfies the whole outcome;
7. a falsifier that would overturn the selection;
8. a rollback/recovery route.

Challenge the preferred answer before committing. Ask whether the research coverage is sufficient, whether a cheaper/simpler method reaches the same craft ceiling, and what evidence would prove the chosen method wrong. Do not endlessly repeat analysis without new evidence.

Record material decisions with `vga-studio decision`. Record observed failures and competing causes with `vga-studio failure`.

## 5. Project-specific task graph

Build a directed acyclic graph from the actual outcome. Do not impose a universal pipeline such as research → script → storyboard → generation → edit → sound → QA.

Each task declares:

- stable task ID, purpose and kind;
- executor class: agent, tool, human or external;
- true prerequisites and dependency IDs;
- exact input and output artifact names;
- required capabilities, source/rights constraints and production limits;
- observable acceptance criteria;
- priority and bounded retry budget.

Parallelize independent research, concept exploration, visual/audio tests, rights checks, tool evaluation, packaging research and other work when inputs are ready. Merge only at real decision or dependency points. Avoid artificial dependencies and peer-chat as an authority mechanism. Handoff through task packets, files, digests and decision receipts.

A declared executor must resolve to an executable worker. The local Studio currently registers the production operations `ffmpeg_assemble` and `delivery_package`, plus FFprobe technical measurement. A task labelled `tool` without a registered operation is not executable and must remain unclaimed/blocked for capability work; do not mark it complete manually. Agent and human work are different executor classes, not aliases for local tools.

Before expensive production, prototype the highest-risk creative assumption with the smallest near-final sample that can test the actual craft requirement. A tool-running proof is not a quality proof.

## 6. Production method and tool choice

Choose the medium per scene, beat or shot. Possible methods include original footage, authorized archive, image generation, video generation, image-to-video, 3D, procedural graphics, typography, diagrams, screen capture, compositing, practical photography, NLE editing, narration, music, sound effects and deliberate silence. Hybrid production is normal.

Select a tool only after confirming that the exact operation is available in the current session/account and that its input, output, resolution, duration, reference, extension, editing and rights constraints fit the task. Feature-list mentions are not execution proof. Prefer the simplest admissible method that meets the target quality; do not default to the most expensive model.

If a required tool is unavailable, record the blocked capability and compare an acceptable alternative. Never claim a generation, edit, render, upload or review occurred unless the exact output exists and can be inspected. Never fabricate provider run IDs, file paths, metadata, citations or review evidence.

## 7. Worker execution and artifact custody

Use `vga-studio claim` to atomically claim ready work. Respect the lease and heartbeat it for long operations. The work packet defines the exact scope and current input digests. A worker may not broaden its task or change the owner outcome.

Use `vga-studio claim --executor agent` when the current session is executing agent work. Use `vga-studio run-ready-tools PROJECT --max-workers N` to execute all currently ready, registered local tool tasks in concurrent rounds; this can run independent renders or measurements at the same time and then continue to newly-ready downstream tool tasks. The worker pool reports unsupported tool tasks instead of claiming them. It does not launch LLM agents, human reviewers or external providers. Dispatch those only through an actual current-session/external worker and record its run and output evidence.

Before marking work complete:

- create every declared output as a real file inside the project workspace;
- verify that each file opens and is the expected media/document type;
- provide the exact output mapping and any result metadata;
- let the engine calculate SHA-256 and register immutable artifact identity;
- record provenance, source and rights state truthfully.

Import external inputs with `import-asset`. Do not write outputs over an existing registered path. A new version gets a new path. A changed upstream artifact makes affected descendants stale; regenerate or re-review them.

A finished production package should explicitly include every owner-requested item. Unless the brief narrows the scope, check for final master video, audio master/stems, subtitles, cover, editable/reproducible project source and assets, platform copy, rights/provenance manifest, technical QA and review receipts. The local FFmpeg assembler currently combines declared shot assets and audio tracks; it does not create the shots, voice, music, cover or editorial copy.

## 8. Independent review and release

Review the actual bytes, not a prompt, description, contact sheet alone, or task status. Use reviewers who did not produce the artifact. Where the platform supports it, keep review context blind to sibling verdicts and record the actual reviewer/context. A different reviewer ID alone is only a structural separation check, not cryptographic proof of independent cognition.

Use separate rubrics appropriate to the project. Common dimensions:

- editorial accuracy, source quality and claim traceability;
- story clarity, hook, pacing, retention and payoff;
- humor/naturalness/platform voice where relevant;
- composition, lighting, motion, materials, typography and visual continuity;
- edit rhythm, transitions, voice, music, sound design and mix;
- subtitle accuracy, safe areas, encoding, resolution, frame rate and playback;
- rights, likeness, consent, product truth, provenance and synthetic disclosure;
- platform fit, cover, title, copy and export package.

Technical QA and editorial/craft QA are different. FFprobe can measure streams, duration, dimensions and frame rate; it cannot prove a film is compelling, funny, accurate, legally cleared or commercially effective.

Bind every review to the exact artifact ID and SHA-256. Conflicting PASS and FAIL verdicts block release. Replaced bytes invalidate prior review authority. Run `release-check` on the exact final deliverable with required rubrics, rights and platform evidence. Release admission is not publication; upload or paid external actions require owner authorization.

## 9. Failure, repair and recovery loop

When something fails, do not reflexively add another prompt, role, stage or gate. First record the observed symptom and affected outcome. Compare at least two root-cause hypotheses and identify a test that distinguishes them.

Classify the cause at the correct layer:

- intent/requirement recovery;
- source truth, freshness or rights;
- decision/research coverage;
- task contract or dependency graph;
- worker execution or tool capability;
- asset identity, lineage or stale state;
- review rubric or independence;
- integration, packaging or release.

Challenge the previous method, not just the last output. State the repair, falsifier and rollback. Repair the smallest causal layer that evidence supports, then independently verify and replay the relevant regression. Close a failure only with verification and regression evidence references. Preserve failed attempts and rejected methods.

## 10. Learning and method evolution

Store reusable methods with the problem solved, mechanism, applicability, evidence, counterexamples, failure conditions and replay references. New methods begin as candidates. A single successful output, provider marketing claim or model self-assessment does not establish a general rule.

Promote a method only after independent replay and counterexample trials. Record where it does not apply. Keep volatile provider facts dated and revalidate them before use. Never let a learned preference override a new owner instruction.

## 11. Continuation and completion

At every pause or handoff, leave a durable resume state: current goal, brief revision, completed tasks, active claims, blocked dependencies, exact artifact IDs/digests, decisions, failures, open reviews, next executable action and unresolved owner choices.

The project is complete only when all requested deliverables exist, open dependencies are resolved or explicitly disclosed, current artifacts pass applicable technical and independent craft/editorial reviews, rights and disclosure requirements are satisfied, and release checks pass on the exact final bytes. Report any unverified condition as unverified. CI, a green graph, a renderer exit code or a successful tool call is never a substitute for inspecting the deliverable.

## 12. CLI quick reference

```bash
vga-studio --help
vga-studio --root ./studio-work init episode-001 --title "Episode 001" --brief examples/technology-explainer.brief.json
vga-studio --root ./studio-work plan episode-001 examples/technology-explainer.tasks.json
vga-studio --root ./studio-work status episode-001
vga-studio --root ./studio-work claim episode-001 --worker researcher-01
vga-studio --root ./studio-work audit episode-001
vga-studio --root ./studio-work events episode-001
```

Read `docs/standalone_video_studio.md` for the complete JSON contracts and runtime semantics. The canonical package uses only Python standard-library runtime dependencies; optional media QA requires FFprobe. Existing 0.8 modules are compatibility adapters, not the new Studio's control plane.
