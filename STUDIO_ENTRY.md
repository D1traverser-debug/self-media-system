# Video Studio — Standalone Entry

Status: `ACTIVE_CANDIDATE`
This file, `STUDIO_ENTRY.md`, is the standalone startup authority for new Video work.
Runtime: `video_studio.engine.StudioEngine`
CLI: `vga-studio`
Manifest: `video_studio/data/studio_manifest.json`
Operating manual: `docs/standalone_video_studio.md`

## Mission

Turn the owner's actual media goal into a finished, independently checked deliverable. The system is outcome-driven, not stage-driven. Each project gets a task graph derived from its brief; independent tasks can run concurrently, and only declared dependencies block work.

## Independence

The current Studio owns its own requirement interpretation protocol, decision receipts, task graph, execution leases, artifact history, review evidence, failure diagnosis, recovery and learning admission. It covers MEDIA_GROWTH, ORIGINAL_DIGITAL_IP usage (without owning canon), COMMERCIALIZATION and PRODUCTION_SYSTEM through explicit task graphs and verified domain adapters. It does not import, call, require, or wait for CAOS, a CAOS Skill, a CAOS runtime, a parent task ID, or a parent lease. The legacy `CAOS_VIDEO_ENTRY.md` and the 0.8 runtime are historical/compatibility material, not startup dependencies for new Studio work.

IPOS remains the sole authority for the owner's original character/identity canon. The Studio consumes approved, versioned IPOS exports; it does not create a competing canon.

## New-task startup

1. Recover the complete owner goal and every correction, constraint, prohibition and requested deliverable. Separate hard requirements, preferences, examples, assumptions and unknowns.
2. Inspect current project state and exact source assets. Do not infer ownership, rights, media content or tool availability from filenames or declarations.
3. Create/update an outcome brief with audience, purpose, format, platform, deliverables, success criteria, constraints, budget/time limits and unresolved questions. A changed brief must be revised through the CLI so affected work is invalidated rather than silently reused.
4. Build a project-specific dependency graph. Revise the brief with `vga-studio revise-brief` and task contracts with `vga-studio revise-task` when new evidence changes the plan. Do not copy a fixed stage template. Split independent research, creative, asset, sound, production and distribution work where parallel execution is safe.
5. For material creative or architectural decisions, record competing hypotheses, discriminating evidence, alternatives, counterevidence, selected option, falsifier and rollback.
6. Prototype the highest-risk quality assumption before expensive full production. Use the smallest sample that can represent the intended final craft.
7. Execute through `vga-studio` task claims and actual available media tools. Never mark a task complete without its exact declared files and digests.
8. Review the actual artifacts independently. Reopen upstream decisions when evidence contradicts them; invalidate only dependent descendants.
9. Release-check the exact final artifact against configured review, rights and disclosure evidence.
10. Persist reusable learning only with applicability, counterexamples, failure conditions, source evidence and independent replay.

## Quick start

```bash
python -m pip install -e .
vga-studio --root ./studio-work init episode-001 --title "Episode 001" --brief examples/technology-explainer.brief.json
vga-studio --root ./studio-work plan episode-001 examples/technology-explainer.tasks.json
vga-studio --root ./studio-work status episode-001
vga-studio --root ./studio-work claim episode-001 --worker director-01
```

A claim returns a bounded work packet, exact input asset digests and a lease token. Complete the task only after the declared output files have been written inside the project workspace:

```bash
vga-studio --root ./studio-work complete episode-001 research --worker researcher-01 --token CLAIM_TOKEN --outputs research.outputs.json
```

Use `vga-studio qa-media` for a claimed technical-measurement task and `vga-studio --help` for the complete command set. The existing `vga` command remains the 0.8 compatibility CLI; new standalone projects use `vga-studio` or `python -m video_studio`. The canonical implementation is the `video_studio` package; `video_growth_agent.studio_*` imports are compatibility shims only.

## Completion rule

A project is not complete because a plan exists, a task graph is green, a renderer ran, or CI passed. Completion requires the requested final files, exact artifact identity, all applicable independent reviews, technical QA, rights/truth/disclosure checks, and an owner-visible list of any remaining unknowns.