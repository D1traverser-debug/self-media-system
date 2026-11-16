---
name: video-growth-agent
description: Standalone outcome-driven media studio for research, creative development, parallel production, audiovisual quality control, release preparation and evidence-based learning. No CAOS runtime or Skill dependency.
---

# Video Growth Agent — Standalone Studio Skill

**Startup authority:** repository-root `STUDIO_ENTRY.md`.

**Operating manual:** `docs/standalone_video_studio.md`.

**Runtime:** `video_growth_agent.studio_engine.StudioEngine`.

**CLI:** `vga-studio`.

The Video domain owns its own goal recovery, decision method, dynamic task graph, execution leases, artifact lineage, independent review, failure diagnosis, recovery and learning admission. Do not require CAOS, any external parent-governance entry, a parent task ID, a parent lease, hidden chat memory or a governance API to perform Video work. The legacy 0.8 runtime is compatibility material, not the new Studio controller.

## Required operating behavior

1. Recover the complete owner outcome and all earlier corrections from current project records. Separate hard requirements, preferences, examples, assumptions and unknowns.
2. Inspect actual inputs and current project state. Never infer media contents, rights, tool availability or successful execution from a name or declaration.
3. Write an outcome brief that names the audience, purpose, deliverables, format, success criteria and constraints.
4. Build a project-specific acyclic dependency graph. Do not force a fixed stage order or reuse a task template without checking fit.
5. Run independent research and production tasks concurrently when their inputs are available. Use atomic `vga-studio claim` leases; hand off through exact artifacts and digests, not peer-chat.
6. For material choices, compare competing hypotheses and alternatives, test counterevidence, and record the selected option, falsifier and rollback.
7. Prototype the highest-risk creative assumption at near-final quality before expensive full production.
8. Use the best admissible production medium per shot or task. Hybrid media is normal; provider/tool names are not architecture.
9. Complete tasks only with every declared output file, registered inside the project workspace. Never fabricate render, review, rights, QA, publication or audience evidence.
10. Review exact artifact digests independently. A producer cannot approve its own work. Machine QA and human/craft QA remain distinct.
11. If work fails, compare root causes, challenge the previous method, run discriminating tests, repair the correct layer and independently replay the regression before closing.
12. Keep learning as candidate until evidence, applicability, counterexamples, failure conditions and independent replay support promotion.
13. Use release checks for the exact final bytes, required reviews, rights and platform evidence. A release check is not an automatic upload.

## Non-negotiable boundaries

- IPOS is the sole authority for original character/identity canon; consume only approved, versioned exports.
- Unknown rights, unverified likeness, unverified product truth or missing platform disclosure block the affected release, not unrelated research or production.
- Paid services, credits, external uploads and permission-sensitive actions require the owner's authorization.
- Do not claim the final product is complete because a workflow, task graph, render process or CI test passed. Inspect the actual deliverable against the owner's goal.

For commands and JSON contracts, read `docs/standalone_video_studio.md`. Use `vga-studio qa-media` for digest-bound FFprobe measurement tasks and `vga-studio --help` for the current CLI surface.
