# Video Production Studio

**Status: REBUILD_IN_PROGRESS**  
**Canonical entry:** `STUDIO_ENTRY.md`  
**Runtime:** `video_studio.engine.StudioEngine`  
**CLI:** `vga-studio`

Video Production Studio turns an owner's brief into actual media deliverables, then verifies the exact output files. Its success measure is the finished work and its evidence—not the number of agents, prompts, stages, adapters or passing structural tests.

## One authority path

- `STUDIO_ENTRY.md` — the only startup entry for new Video work.
- `skills/video-growth-agent/SKILL.md` — agent operating instructions.
- `docs/standalone_video_studio.md` — detailed product, runtime and quality contract.
- `video_studio/engine.py` — durable project state, dynamic task DAG, claims, artifacts, reviews, failures and learning.
- `video_studio/image_set.py` — concept/prompt diversity contract for multi-image jobs; it does not prove visual diversity in generated pixels.
- `video_studio/media.py` — FFprobe technical measurement only.
- `video_studio/data/studio_manifest.json` — machine-readable runtime boundary and capability status.

New generic production requests do not silently resolve to the AI self-media business Program. Resume a project only when the owner names it or its exact alias; otherwise create a project from the current outcome brief. The AI self-media growth/IP/commercialization Program remains available as an optional, explicitly selected business workspace.

## Product boundary

Video production is the primary product. A project may attach these optional workstreams only when the brief establishes a real dependency:

- **MEDIA_GROWTH** — audience research, positioning, packaging, distribution and audience outcomes.
- **ORIGINAL_DIGITAL_IP** — approved IP use and performance evidence. IPOS remains the sole authority for original-character identity canon and identity rights.
- **COMMERCIALIZATION** — sponsor fit, deliverable obligations, product truth, rights scope and commercial measurement.

## Execution truth

The runtime distinguishes `agent`, `tool`, `human` and `external` tasks. A declared executor is not proof that work ran. An agent task is handled by the current session or an explicitly connected worker; a local tool task requires a registered, tested executor; an external task requires a current capability/rights/cost check; a human task requires the named human action. No worker pool or provider integration is claimed unless it is actually implemented and verified.

Current foundation: standalone project control plane, dynamic DAG, durable events, artifact digests, independent review records, release checks, failure/learning records, FFprobe measurement and an image-set concept/prompt contract.

Not yet release-ready: complete shot/image generation integration, general scene rendering, full audiovisual assembly, provider-neutral execution adapters, automated local-tool scheduling, recursive rights-evidence validation and end-to-end craft acceptance. The rebuild must close these gaps with real output-level dogfood, not more declarations.

## Governance and safety

The Video runtime is independently operable and has no CAOS runtime/API dependency. When the active ChatGPT session is CAOS-governed, CAOS supplies parent-level decision and execution governance externally; the Video system remains the owner of its domain state. **The CAOS repository, branches, files, configuration and installed skills are read-only and must not be modified.**

No paid generation, GPU rental, subscription, external upload, publication or owner-device action is authorized by a tool declaration. Obtain explicit owner approval for separately chargeable or externally consequential actions. Never execute arbitrary project-supplied Python as if a boolean flag were a sandbox. Never fabricate media, provider runs, rights, reviews, CI results or publication.

## Compatibility boundary

The `video_growth_agent` 0.8 domain modules, fixed-stage controller, old `vga` CLI and historical pilot records remain compatibility/history surfaces. They are not the controller for new Video Studio projects. Reuse a specialized legacy module only through a reviewed, tested, evidence-bound adapter. Do not restore the old 20-stage/56-work-order controller as the product architecture.
