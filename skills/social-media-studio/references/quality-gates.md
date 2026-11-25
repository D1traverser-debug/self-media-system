# Quality Gates

> **Applicability contract:** This file is a reusable method library, not a universal stage checklist. Select criteria only when they apply to the owner's current deliverable and explicit brief. If a criterion does not apply, mark it N/A; do not invent work or fail a deliverable for not containing an unrelated medium, stage or asset. Current authority: `STUDIO_ENTRY.md`, the active owner brief and `social_media_studio/data/studio_manifest.json`.

## Cross-deliverable fidelity

- Preserve the exact requested outcome, destination, language, format, source, variants and hard constraints.
- Keep hard requirements separate from preferences and examples. A method may change; the requested outcome must not silently change.
- Every hard requirement must map to an observable check. Every check must map to an applicable requirement or risk.
- Inspect the exact final output, not only the prompt, plan, task graph, preview receipt or tool exit code.
- Never call a result PASS because it is better than a rejected draft. Compare it with the owner's acceptance bar and relevant references.

## Short copy and captions

- Match the requested language, platform voice, audience, intent and length.
- Lead with the actual hook, thought, joke, question or value the user asked for; do not turn a caption into news narration or an explanation unless requested.
- Give title, body/description, cover copy and hashtags distinct roles when multiple fields are requested.
- Check semantic redundancy, natural phrasing, factual boundaries and the exact requested call to action.
- Do not add a cover, article, script, research report or extra variants when the user asked for one short text.

## Long-form writing and articles

- Preserve the requested thesis, point of view, emotional progression, structure and reader value.
- Support material factual claims with current, traceable sources; separate fact, estimate, opinion, satire and fiction.
- Check causal reasoning, counterarguments, originality, useful implications and non-redundancy.
- Respect the requested heading/subtitle/body hierarchy, formatting, links, tags, image placement and publication conventions.
- Do not import video-production stages into an article workflow.

## Static images and image sets

- **Static images do not require camera motion, animation, a timeline, sound or video playback.** Add those only when the user requests a moving output.
- Check the single intended scene, focal hierarchy, composition, subject readability, material/light, typography and mobile-size legibility where relevant.
- Preserve reference roles: identify what may influence the result and what must not transfer.
- Use canonical dimensions as explicit width × height plus orientation. Normalized ratios are always WIDTH:HEIGHT.
- If the user explicitly supplies HEIGHT:WIDTH, reverse the axes when normalizing. For example, 4:3 HEIGHT:WIDTH becomes 3:4 WIDTH:HEIGHT and is portrait. If the axis order is genuinely ambiguous and changes the output, ask one concise clarification.
- For a multi-aspect set, preserve the shared concept but design each aspect ratio independently. Do not merely crop one composition into every ratio unless explicitly requested.
- Do not add collages, panels, UI, titles, slogans or extra images when prohibited or not requested.

## Motion, original video and animation only

Apply the following only when the deliverable actually contains motion:
- The opening should communicate a conflict, promise or curiosity without requiring prior context.
- Each major beat should introduce meaningful new information, composition, scale, tension or payoff; pace and rests should serve comprehension.
- Use motion to explain or direct attention. Avoid arbitrary movement, all-linear motion or fade-only entrances when they weaken the concept.
- Remove shots that add no comprehension, tension, emotion or payoff.
- Sound, music, effects and silence should map to narrative beats when audio is part of the requested output.
- Review full-speed playback and the actual final encode. Verify applicable stream duration, synchronization, frame count, resolution, frame rate, true peak, black frames and full decode.

## Media transformation and editing

- Identify the exact source asset and the precise time ranges, shots, tracks or properties the user permits changing.
- Preserve everything outside the requested change, including original audio when promised.
- Distinguish bitstream identity, PCM identity and perceptual similarity; never describe re-encoded audio as bit-identical.
- Compare source and output, inspect the actual affected frames/audio, verify synchronization and report any unavoidable loss or truncation.
- Do not upscale, crop, sharpen, denoise, recolor or alter unrelated material unless requested or explicitly approved.

## Quality scales and independent review

- Use a 1–5 scale only when a numeric rubric or quality-critical review is appropriate. The anchors are: 5 reference-level; 4 publishable and close to reference; 3 competent but below the bar; 2 template/demo quality; 1 broken or placeholder.
- Do not average away a failed hard requirement. A score is evidence only when tied to the exact artifact version, reviewer, rubric, observed findings and supporting evidence.
- The producer cannot independently approve their own output. Independent review must inspect the exact digest and disclose limitations.
- Do not claim a human review, blind review, semantic fact-check or independent acceptance unless it actually occurred.

## Benchmark, LOOKDEV and visual-preview methods

These methods are conditional tools for complex, long-form, high-cost or quality-critical motion/visual production when a benchmark or prototype is needed to test a material risk:
- A project-specific benchmark pack may compare format, craft and explanatory clarity. Extract observable traits and explicit `do_not_copy` boundaries.
- LOOKDEV hero frames and a representative motion preview may be useful before expensive production.
- Side-by-side comparison may reveal craft gaps against an approved benchmark.
- Do **not** impose three hero frames, a motion preview, a benchmark pack or a Creative Director scorecard on a short caption, article, prompt-only request, single static image, simple crop or routine edit.

## Release and commercial presentation

- Ask whether the team would publish under its own account or show the work to an advertiser only when public release or commercial presentation is actually in scope.
- A draft, private prompt, single still or internal edit is not automatically a release candidate.
- Public posting, paid promotion and third-party delivery require their own current authorization. A quality PASS is not permission to publish.
