# NVIDIA / CNN — X Satirical Illustration Recovery Brief

**Task ID:** `V-20261117-01-NVIDIA-CNN-X-ILLUSTRATION-SERIES`  
**Status:** `OPEN__PRIOR_8_IMAGE_BATCH_REJECTED__RESEARCH_AND_REDESIGN_REQUIRED`  
**Owner authority:** current owner corrections in the 2026-11-17 conversation  
**Project:** `ai-self-media-commercialization` / Video Studio  
**Workstreams:** `MEDIA_GROWTH + PRODUCTION_SYSTEM`  
**Scope:** eight standalone English-language X satirical illustrations based on the cited CNN report, with platform-native X copy.  
**Not in scope:** changing personal-IP canon, producing the creator avatar, publishing, or modifying CAOS/IPOS.

## 1. Owner outcome — hard requirements

The owner wants eight genuinely different, funny, immediately legible editorial/meme illustrations. The owner does **not** want to supply or preselect the creative ideas. The assistant must independently read the source, discover the most interesting satirical angles, research relevant visual-art methods, and make the creative decisions.

Each image must work as a standalone post. A viewer with no chat history or prior explanation should understand the central visual joke quickly. The picture must express a specific point, not merely contain relevant objects.

The eight images must be developed **one at a time**, each through its own complete creative and QA cycle. Do not generate a batch of eight from one shared prompt, reuse one scene template, or treat eight prompt variations as eight concepts.

Required deliverables:
- Eight accepted, distinct English X illustrations (one image per accepted concept).
- One X-native post copy for each illustration, written to complement rather than explain the picture.
- A concise text-only production/QA record for each image, including the final concept, art direction, prompt version, observed result, verdict and any correction history.

## 2. Source and factual boundary

Primary supplied source:
- CNN, Ramishah Maruf, “Lies, spies and sex are just one part of the Nvidia story. The real stakes are much bigger,” published/updated 2026-11-16.
- URL: https://edition.cnn.com/2026/11/16/tech/nvidia-sex-spies-serious-problems?Date=20261117&Profile=CNN&utm_content=1794885951&utm_medium=social&utm_source=twitter

The article's substantive lanes to investigate and verify before selecting jokes:
1. Export controls and the reported risk of advanced Nvidia chips being diverted to China through Singapore-based intermediary/cloud businesses, including Megaspeed.
2. The distinction between alleged diversion, ongoing investigations, company denials and established facts.
3. The reported disagreement inside the US administration over whether/when to place Megaspeed on an export-control blacklist, and the public dispute between Treasury and Commerce officials.
4. The separate Super Micro Computer case: its founder was charged in March over an alleged server-smuggling scheme; do not conflate that company, its indictment or its actors with Megaspeed or Nvidia.
5. The AI infrastructure financing loop: Nvidia and major financial institutions participating in large-scale lending for AI infrastructure, alongside Nvidia's separate investment/commitment to an OpenAI data-center project.
6. The article's central editorial distinction: sensational personal allegations risk distracting from the larger chip-export, governance, policy and capital-structure questions.

**Fact discipline:** the intelligence/spying claims and alleged wrongdoing must remain attributed and unproven unless independently verified. Megaspeed's denial must not be omitted when relevant. Do not depict an allegation as a proven crime, do not invent a real-world conspiracy, and do not transfer facts from the Super Micro case to Megaspeed. Prefer satire of systems, incentives, bureaucracy, policy contradictions and financial structures over private sexual conduct or unsupported claims about named individuals.

## 3. Previous batch — rejection and retained evidence

The owner supplied eight prior image candidates. They are **not accepted artwork and must not be used as visual references for new generations**. Their only retained value is failure evidence.

Owner-observed failures:
- The first composition had incorrect spatial logic.
- The second had a more promising direction, but the national/route symbolism was not sufficiently explicit; if the joke concerns Singapore-to-China movement, the relevant visual symbols must make that route understandable rather than using arbitrary cute animals.
- The remaining images did not make their central joke clear enough when viewed individually, without explanation or conversation memory.
- Earlier iterations also exhibited duplicate-person/duplicate-Jensen problems and other basic visual-logic errors.
- The owner explicitly requires the assistant to discover and correct additional defects without waiting for the owner to enumerate them.

Do not preserve the prior image titles or metaphors as mandatory concepts. Re-derive the strongest eight ideas from the source and the intended audience effect. A prior idea may be reconsidered only if it independently wins the new concept review.

## 4. Creative-method requirements

Before writing any image prompt, establish for that image:
1. **Thesis:** the exact editorial observation or contradiction being satirized.
2. **Joke mechanism:** e.g. visual analogy, role reversal, scale inversion, absurd literalization, juxtaposition, caricature, bureaucratic understatement, visual pun, recursive loop, impossible-but-readable physical metaphor, or sequential reveal.
3. **Instant-read test:** what should a viewer understand in the first glance, and which single visual relation communicates it?
4. **Audience prior knowledge:** what the viewer must already know; remove unnecessary dependence on niche context.
5. **Visual sentence:** subject + action + consequence, expressed as one coherent scene.
6. **Art direction:** choose the visual language that best expresses this particular joke. The eight should have meaningful stylistic variety, not arbitrary decoration or a common template.
7. **Composition plan:** foreground/midground/background, camera angle, perspective, spatial relationships, scale, focal hierarchy, negative space and safe margins.
8. **Acting plan:** exact character count, identity/role, body orientation, gaze, expression, gesture and hand use.
9. **Object logic:** exact object counts, physical contact, attachment, support, occlusion, direction of movement, arrow/flow direction and cause-and-effect.
10. **Light and material:** motivated key-light direction, shadow direction/contact, contrast, palette, texture and any special effects that reinforce the joke rather than obscure it.
11. **Typography decision:** default to no text. Add only the minimum English words needed when lettering is itself part of the joke; specify exact wording, placement, hierarchy and legibility.
12. **Factual and ethical boundary:** what the image asserts, what it only alludes to, and what it must not imply.

Prompts are execution specifications, not substitutes for editorial judgment or art direction. Each prompt must be self-contained and materially unique to its concept. Positive, observable scene instructions take priority over long generic negative-prompt lists.

## 5. Per-image execution protocol — mandatory, sequential

For each image (i = 1..8), complete the following before moving to image (i+1):

- **A. Source/angle check:** verify the relevant article facts and choose one distinct satirical thesis.
- **B. Concept challenge:** generate competing concepts, compare their clarity, originality, fairness, visual potential and dependence on explanation; reject weak or overlapping concepts.
- **C. Art research:** choose and study the most relevant visual grammar for this concept. Research Chinese simple-line comics/caricature and major editorial/cartoon satire traditions as well as other fine-art approaches. Extract transferable principles; do not imitate a living artist or copy a specific artwork.
- **D. Visual design:** write a one-scene visual brief with exact staging, object relations, gestures, expression, composition, lighting, palette, style and typography decision.
- **E. Prompt compilation:** produce one complete prompt for this image only. Do not reuse another image's scene description, style block or object layout.
- **F. Generation:** generate exactly one candidate image for this concept.
- **G. Direct visual QA:** inspect the actual image against the brief. Check immediate joke readability, semantic precision, focal hierarchy, anatomy/hand count, duplicate people, object count, perspective, spatial continuity, contact/occlusion, scale, light/shadow, arrow/flow direction, text spelling/layout, style integrity and clutter.
- **H. Blind-read challenge:** ask whether an uninformed viewer could infer the intended joke from this image alone. If not, reject or redesign; do not rescue it with a long caption.
- **I. Root-cause correction:** if it fails, identify the earliest failing layer (idea, visual metaphor, staging, prompt, generation or craft QA), challenge the diagnosis, then revise that layer. Do not merely add adjectives or append more negative constraints.
- **J. Acceptance:** record PASS / REWORK / REJECT with evidence. Only a PASS image advances to the final eight-image set. Then proceed to the next image.

A single image must not be called complete because the prompt is detailed, the rendering is attractive, or the tool returned an image.

## 6. Minimum acceptance criteria

An image passes only when all applicable conditions hold:
- Its satirical thesis is specific to this article or a clearly identified issue in it.
- Its joke is understandable without chat history, a verbal explanation or a long caption.
- The main visual relationship is coherent and physically readable.
- It has one dominant focal point and a clear visual hierarchy.
- The chosen art style strengthens the joke and differs meaningfully from the other accepted images.
- Character anatomy, number of people, limbs, fingers, props and object counts are correct.
- Perspective, scale, spatial placement, occlusion, contact, gravity and movement/arrow directions are coherent.
- Lighting is motivated; shadows and reflections agree with the scene.
- Typography, if any, is minimal, correctly spelled and legible.
- No unsupported allegation is represented as established fact.
- The image has no unexplained decorative elements, accidental duplication, random collage or conflicting visual metaphors.
- Its X copy adds a second layer of wit rather than narrating the obvious or explaining a failed picture.

## 7. Learning agenda

Before and during production, research and extract reusable methods from:
- Chinese cartooning and simple-line comic traditions: economy of line, silhouette, gesture, exaggeration, social observation, visual shorthand and the timing of a punchline.
- Editorial/political cartooning: caricature, symbolic substitution, visual analogy, scale, juxtaposition, labels, negative space and institutional satire.
- Fine-art and print traditions suitable for satire: caricature, grotesque, etching/engraving, woodcut, poster art, surrealism, absurdism and conceptual illustration.
- Contemporary editorial illustration and internet meme grammar: first-read clarity, thumbnail legibility, remixability and platform-native copy.

Study the method and visual grammar, not merely artist names or surface style. Do not ask the image model to combine every influence at once. Select the style per concept and record why it is suitable.

## 8. Authority boundaries and continuity

- **Video Studio** owns this non-character editorial illustration task, its brief, concepts, image candidates, review evidence and X packaging.
- **CAOS** may guide the active chat's recursive diagnosis, root-cause challenge, research coverage, alternative comparison and method critique. This does not authorize changes to the CAOS repository, code, Skills, configuration or releases. No CAOS runtime call or background work is implied.
- **IPOS** remains the sole authority for the owner's personal avatar/character identity. This task does not create, select, edit or approve the personal avatar. No IPOS identity bundle is currently approved; identity-dependent video remains separate and blocked. These non-character news illustrations do not need to wait for the avatar.
- Do not use the creator's unfinished personal avatar as a substitute for a news subject or as an unapproved recurring character.
- Keep persistent project records text-only unless a separate, explicit media-asset registration task is authorized. The rejected candidate images are not to be copied into the prompt/reference set.

## 9. Current checkpoint and next action

- Eight prior candidates: `REJECTED_AS_A_SET`; no image is accepted.
- New concepts: `NOT_YET_REDERIVED`.
- Eight independent art directions: `NOT_YET_RESEARCHED_OR_SELECTED`.
- Eight final prompts: `NOT_YET_COMPILED`.
- New image generation: `NOT_STARTED_IN_THIS_RECOVERY_STEP`.
- X copy: `NOT_YET_DRAFTED`.
- Release/publication: `NOT_AUTHORIZED`.

**Next action:** re-read and fact-check the CNN report and relevant primary/independent sources; then build a diverse, ranked concept slate. For each selected concept, run the complete per-image protocol above, one image at a time. Do not ask the owner to supply the ideas or repeat the corrections already recorded here.


## 10. Owner correction — diagnosis of the failure (2026-11-17, supersedes any contrary assistant summary)

The assistant previously described the problem as needing to **rebuild the X visual-creation subsystem's creative and acceptance capability**. The owner corrected this diagnosis:

> The prompts the assistant wrote were poor, and the assistant's preparatory work was poor.

This is an **assistant execution-quality failure**, not evidence that the existing visual-creation subsystem lacks the required capabilities or needs architectural reconstruction.

The correction must govern the next execution:

1. **Do not initiate a subsystem rebuild, architecture redesign, new orchestration layer, or documentation expansion merely because the previous images failed.** Use the existing available workflow and image-generation capability.
2. **Own the prompt-writing failure.** The assistant is responsible for translating the selected idea and approved visual design into a clear, model-executable prompt. Do not shift this burden to the owner or imply that the owner must repair the prompt.
3. **Own the preparation failure.** Before generation, the assistant must actually complete the relevant work: read the source report carefully; verify and separate facts, attributed claims and unknowns; identify the article-specific contradiction; compare possible satire angles; research and inspect relevant visual references/artistic methods; choose the visual joke; design the scene and spatial logic; decide whether text is needed; and preflight the final prompt against the intended image.
4. **Do not mistake a written checklist for completed preparation.** Research must contain inspected sources/references and a reasoned selection. Art direction must contain an actual designed scene. Prompt QA must test the concrete prompt. A list of intended actions is not evidence that those actions occurred.
5. **Do not mistake prompt length for prompt quality.** The prompt is a final translation of resolved visual intent. It should express the necessary visible decisions precisely, without redundant style labels, decorative prose, or a pile of generic negative constraints.
6. **Do not diagnose a failed render as a subsystem defect by default.** Trace the earliest actual failure: source understanding, editorial angle, concept, visual metaphor, art direction, scene construction, prompt translation, generation variance, or inspection. Attribute it to the correct layer using evidence.
7. **Keep the user's required outcome unchanged:** eight distinct, funny, standalone English X illustrations; each image is developed and checked individually; the joke must be legible without conversation context; the assistant, not the owner, develops and selects the creative concepts.

The earlier phrase “rebuild the visual-creation subsystem” is withdrawn. The accurate task is: **improve the assistant's own preparation, creative judgment, art-direction decisions and prompt execution while using the existing subsystem.**

No subsystem rebuild has been authorized. No new image has been generated by this correction. The eight-image task remains open and publication remains unauthorized.
