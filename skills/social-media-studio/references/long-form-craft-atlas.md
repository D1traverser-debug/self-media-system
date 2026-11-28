# Long-form Craft Atlas — Domain-Independent Editorial Methods

> Status: `CANDIDATE_REQUIRES_REVALIDATION`  
> Owner: `Social Media Studio / editorial_writing / long_form_editorial`  
> Scope: substantial essays, X Articles, explanatory writing, narrative nonfiction, case studies, analysis and other long-form editorial work.  
> This is a method-selection atlas, not a mandatory checklist, fixed article template, style imitation guide or proof of writing quality.

## 0. Purpose and authority

This atlas expands the existing `long_form_editorial` route with craft mechanisms recovered from three sources:

1. `D1traverser-debug/novel-writing-agent` — especially `NOVEL_MASTERY_MODEL.md`, `MASTERWORK_DISTILLATION_PROTOCOL.md`, `NARRATIVE_EVIDENCE_SCHEMA.json`, and the `SHIRI_ZHONGYAN` distillation passes 01–04. These are learning evidence for fiction and narrative craft, not automatically validated nonfiction rules.
2. `D1traverser-debug/financial-writing-agent` — especially `references/editorial.md`, `hooks.md`, `reader_value.md`, `style.md`, `research.md`, `story_quality.py`, and the writing-kernel pass contracts. These are useful article-production candidates, but the repository's own general writing audit leaves cross-topic independent quality validation open.
3. External craft and research references listed at the end: Harvard College Writing Center, Nieman Storyboard, The Open Notebook, Reuters/SPJ standards and a meta-analysis of narrative versus expository comprehension.

Authority order remains: current owner brief and deliverable > CAOS governance > SMS manifest/Skill and existing editorial/assurance contracts > this candidate atlas > external craft references. The atlas cannot change the owner's goal, fabricate facts, grant publication permission or certify an article.

The Novel repository's current masterwork campaign is separate and remains untouched. Its study state identifies `GUI_CHUI_DENG` as the sole active work, paused at source line 3913 with line 3914 as the next location. No novel checkpoint, corpus, Canon, rulebook or project state is modified by this SMS adaptation.

## 1. Governing principle: reader job and material determine form

A long article is not a long thread, a report with more headings, or a novel with its names removed. First determine what the reader needs the piece to do and what the available material can honestly support. Then select only the craft modules that serve that job.

Every substantive article should be able to answer:

- **Reader:** Who is the intended reader, and what do they already know or believe?
- **Reader job:** What are they trying to understand, decide, reconsider, feel or do?
- **Promise:** What specific value will this article deliver that a competent reader does not already have?
- **Question/tension:** What unresolved problem, contradiction, choice or information gap makes the piece worth entering?
- **Authorial contribution:** What is the author's actual interpretation, observation, synthesis or argument—not merely a topic summary?
- **Payoff:** What will the reader be able to understand or do by the end that they could not at the beginning?

Do not confuse topic importance with article value. “AI is changing work” is a topic. A valuable article identifies a specific question about how, for whom, under what conditions, with what evidence and what consequences.

## 2. Genre and task router

Choose the dominant form from the reader job and the evidence. Mixed forms are allowed; identify the dominant engine and add only the necessary secondary modules.

| Form | Primary reader job | Dominant engine | Required craft emphasis | Common failure |
|---|---|---|---|---|
| Argument / opinion essay | Reconsider a belief or judgment | Tension → arguable thesis → warrant/evidence → rival explanation → refined conclusion | Thesis scope, claim hierarchy, warrant, counterargument, author stance | Strong opinion with weak bridge from evidence to conclusion |
| Explainer | Understand a difficult mechanism | Question → minimum necessary model → worked example → consequence → boundary | Prior knowledge, sequencing, analogy, chunking, terminology control | Lecture-shaped article that explains everything except why it matters |
| Narrative nonfiction / reported feature | Understand an issue through real people/events | Verified scene(s) + chronology + context + meaning | Reporting, scene/summary/exposition balance, character agency, ethical detail | Invented scene, decorative character, or unreported interior thought |
| Investigation / accountability piece | Determine what happened and who/what is responsible | Question → evidence trail → competing accounts → corroboration → finding/unknown | Source evaluation, chronology, fairness, contradiction, uncertainty | One-source certainty, insinuation, or chronology mistaken for causation |
| Case study | Understand how a real case worked and what transfers | Context → constraint → decision/action → result → mechanism → boundary | Decision sequence, actor incentives, evidence, counterfactuals, limits | Turning one success into a universal recipe |
| Personal essay / reflection | Understand an experience and its wider meaning | Concrete lived moment → reflection → contradiction → revised understanding | Truthful first-person perspective, self-implication, selective memory, resonance | Fake vulnerability or an anecdote that proves too much |
| Tutorial / practical guide | Complete a task correctly | Prerequisite → steps → example → verification → failure recovery | Precision, reproducibility, edge cases, reader feedback | Forced story arc or motivational padding around missing instructions |
| Synthesis / comparative analysis | See a pattern across sources/cases | Competing models → comparison design → convergence/conflict → bounded synthesis | Comparison criteria, dependence/confounds, negative evidence | Source catalogue or superficial “common themes” |

A genre label is not sufficient by itself. A piece called an “analysis” may actually be a tutorial, a personal essay or a reported feature. Route by the work the reader needs, not the author's first label.

## 3. Three scales of craft: Macro / Meso / Micro

The Novel system's Macro/Meso/Micro distinction is useful beyond fiction, provided the units are translated.

### Macro — the whole article

- reader contract, central question and thesis/premise;
- dominant editorial engine and why this form fits the evidence;
- opening promise, central progression and final payoff;
- major information/argument debts and their resolution;
- overall emotional/intellectual movement and publication context.

### Meso — sections and sequences

For each section, specify:

- the reader question it handles;
- what is newly learned or reconsidered;
- which evidence, case, mechanism or example earns the section;
- the counterpoint or limitation that matters here;
- the reader-state change;
- the section payoff and why the next section is now useful.

A section that cannot name its distinct contribution is a candidate to merge, reorder, compress or remove.

### Micro — paragraphs, sentences and details

- paragraph function and one dominant move;
- focus, evidence, inference and transition;
- concrete detail, analogy, quote or image where it performs work;
- sentence/paragraph rhythm suited to the thought;
- diction, syntax, voice, precision and originality.

Do not polish Micro when Macro is broken. A beautiful paragraph cannot rescue an unsupported thesis or a missing reader promise.

## 4. Sixteen craft dimensions adapted from the Novel evidence ontology

The Novel system separates 16 narrative dimensions rather than reducing writing to “logic, rhythm and prose.” SMS should retain that diagnostic breadth but reinterpret the dimensions for nonfiction. These are selectable review lenses; mark irrelevant dimensions `N/A` with a reason rather than forcing them into every article.

| ID | Novel dimension | Nonfiction / X Article adaptation | Use when | Do not force when |
|---|---|---|---|---|
| N01 | Story / fabula / causal engine | Argument progression, causal chain, case sequence, decision logic and state change | The piece explains change, cause, strategy, conflict or consequence | A reference guide only needs accurate ordered instructions |
| N02 | Discourse / temporal order | Chronology versus reveal order; scene, summary, exposition, flashback/context and repetition | Time sequence, investigation, history or a case matters | A conceptual essay is clearer when organized by logic rather than time |
| N03 | Narrator / POV / focalization | Author stance, observer/analyst position, source access, perspective limits and reliability | Personal essays, profiles, reported features, first-person analysis | A neutral technical reference has no meaningful narrator-centered device |
| N04 | Character construction / agency | Real actors' goals, beliefs, capabilities, constraints, choices and observable behavior | Case studies, profiles, institutions and decision analysis | No human actor is central to the explanation |
| N05 | Relationship network / arcs | Power, trust, incentives, obligations, dependency, conflict and stakeholder relationships | Organizations, markets, teams, politics, communities | A simple mechanism has no meaningful relational structure |
| N06 | World / setting / institutions | Systems, rules, institutions, resource flows and second-order consequences | Policy, technology, business, culture and social analysis | The setting adds no explanatory value |
| N07 | Information / mystery / revelation | Question-answer ladder, evidence disclosure, uncertainty reduction, reframe and payoff debt | Investigation, discovery, complex explanation and narrative analysis | Withholding information would obstruct a simple task or safety-critical instruction |
| N08 | Emotion / tension / reader affect | Stakes, uncertainty, conflict, human cost, emotional contrast and aftershock | Narrative nonfiction, cultural essays, consequential analysis | The piece is intentionally neutral or task-focused and emotion would distort it |
| N09 | Pacing / rhythm / page-cost | Information density, scene/exposition ratio, paragraph rhythm, compression, rests and reader effort | All long-form pieces, with intensity scaled to complexity | A rigid beat pattern or arbitrary paragraph length would damage clarity |
| N10 | Dialogue / voice / subtext | Verified quotations, stakeholder language, disagreement, evasion and social power | Interviews, profiles, transcripts, documented exchanges | No authentic dialogue exists; never invent it to enliven an article |
| N11 | Prose / stylometry / surface | Syntax, diction, imagery, cadence, paragraph shape, register and author voice | All prose, especially style-sensitive work | A checklist or detector score is being mistaken for authorship |
| N12 | Serial engine / escalation / payoff | Recurring series promise, multi-part progression, repeated motifs and long-horizon payoff | An explicitly serialized article series or continuing column | A one-off article; do not manufacture sequel hooks |
| N13 | Acquisition / product / platform | Title, cover, first screen, teaser, X Article body, distribution and platform fit | Publishing on X or another specific platform | The user requested private/internal copy with no packaging |
| N14 | Theme / value conflict | Competing values, incentives, trade-offs, moral costs and the consequences of positions | Essays, policy, culture, business and social questions | A straightforward factual guide does not require a moral thesis |
| N15 | Space / environment / action | Real locations, process topology, physical constraints, interface state and observable action | Reported scenes, walkthroughs, product/process case studies | Physical scene detail is not evidenced or not material |
| N16 | Reader memory / cognitive load | Term load, concept chunking, recall cues, reactivation, working-memory burden and information hierarchy | Technical, multi-concept or long articles | It becomes a pretext for repetitive summaries or overexplaining |

### Dimension interactions

Do not assess each dimension in isolation. Examples:

- N07 information revelation affects N16 memory load and N09 pacing.
- N04 actor agency and N05 power relations can make N08 stakes concrete.
- N06 institutional rules become meaningful when they change N01 choices or consequences.
- N03 focalization determines which N02 details are available and which N11 language feels earned.
- N13 acquisition must promise the same value that N01/N07/N14 actually deliver.

The same device can help one dimension while damaging another. A dense technical explanation may improve local precision but slow the narrative engine; a dramatic opening may increase curiosity but damage factual framing. Record the trade-off instead of averaging it away.

## 5. Reader-state progression and question turnover

Adapt the Novel mechanism `question -> evidence -> partial answer -> reframe -> more consequential question` carefully. The invariant is not suspense; it is meaningful change in the reader's model.

For each major section, track:

- **Before:** what the reader currently knows, assumes, doubts or expects;
- **Input:** the new fact, example, mechanism, scene, argument or contradiction;
- **Update:** what belief, distinction or explanation should change;
- **Answer debt:** which earlier promise/question is now resolved or narrowed;
- **Next question:** what new question is now worth asking and why;
- **Payoff:** what the reader can now understand, judge or do.

A new question is earned only when the preceding answer changes the model. Repeatedly saying “there is another layer” without resolving prior questions creates mystery debt, not depth.

### Section card

Use only when a substantial article benefits from explicit planning:

- section purpose / reader question;
- prior reader assumption;
- new information and source/evidence refs;
- mechanism or reasoning bridge;
- strongest relevant counterexample or boundary;
- reader-state change;
- local payoff;
- transition relation to the next section;
- page-cost justification.

## 6. Scene, summary and exposition

Narrative nonfiction has three different tools. They are not interchangeable.

- **Scene:** a bounded, reported moment with a specific time/place, actors, observable action, verified dialogue/details and a meaningful turn. Use it when the reader benefits from experiencing the decisive moment rather than hearing a compressed account.
- **Summary:** compresses time, recurring behavior or background to bridge between important moments. It prevents the article from dramatizing every step.
- **Exposition:** explains the mechanism, history, context or meaning the reader needs to interpret what happened.

Nieman Storyboard's scene craft guidance emphasizes choosing a camera angle and alternating scene with summary rather than depicting every event. Its reporting guidance is explicit that nonfiction scenes must be reported, not fabricated. A novel can invent; an article cannot borrow that permission.

### Scene selection test

Use a scene only if it materially adds at least one of:

- orientation or access to a real event;
- a consequential choice or action;
- a change in relationship, power, risk or knowledge;
- a revealing observed detail;
- a concrete demonstration of the article's mechanism;
- emotional meaning that cannot be honestly conveyed as efficiently in summary.

If the moment is not verified, use a bounded summary, attributed account or explicit uncertainty. Do not invent dialogue, internal thoughts, weather, gesture, chronology, sensory detail or composite characters. Do not imply the author witnessed an event they did not witness.

### Camera-angle discipline

Choose the relevant distance: wide (system/context), medium (actor and setting), close (specific action/detail). Do not inventory a room or a person's appearance. Select details because they reveal the situation, not because they look cinematic.

## 7. Actors, agency and perspective

Novel craft research treats characters as independent agents rather than exposition terminals. In nonfiction, transfer this as a method for understanding real actors, not fictionalizing them.

For a material actor, ask:

- What goal or problem is directly evidenced?
- What resources, authority, knowledge and constraints do they have?
- What did they actually choose or do?
- What alternatives were available, and what evidence supports that?
- Who benefits, bears cost, carries risk or loses leverage?
- What changes in their relationship to other actors or institutions?
- What is known about their stated reasoning, and what remains inference?

A case study should not turn a person into a prop that merely confirms the author's thesis. A profile should reveal agency through consequential choices, observed conduct, authentic speech and carefully selected backstory—not a resume or decorative hardship.

### Perspective and interiority boundary

Separate:

- direct observation;
- the person's own stated account;
- contemporaneous documentary evidence;
- third-party account;
- the writer's interpretation;
- unknown internal motive.

Never write an unobserved thought as fact. Where the person's motive is uncertain, attribute the account or present competing explanations. The author's perspective is allowed in an essay; it must not be disguised as an omniscient report.

## 8. Argument engineering

For argumentative, analytical, predictive, causal or normative writing, use the argument tools; do not force them onto a neutral how-to.

### Claim structure

For each material claim, distinguish:

- **Claim:** what exactly is asserted?
- **Grounds:** what evidence directly supports it?
- **Warrant:** what connects that evidence to the claim?
- **Backing:** why should the reader accept that warrant?
- **Qualifier:** how far does the claim hold, and under what conditions?
- **Rebuttal / rival:** what is the strongest reasonable alternative or counterexample?

A useful adversarial test: construct a case in which the cited evidence is true but the conclusion is false. If that case survives, the argument needs a better warrant, a narrower claim or more evidence.

### Thesis quality

A thesis should be arguable, appropriately scoped and consequential. A descriptive thesis merely repeats what the reader can already see. A broad thesis may be arguable but impossible to support. The thesis should answer an analytical question and show what the article adds to the existing conversation.

### Counterargument quality

Do not append a decorative “on the other hand” paragraph. Identify the strongest plausible alternative answer, the assumption it challenges, what evidence would support it, and whether it defeats, qualifies or refines the thesis. If it defeats the thesis, change the thesis. Harvard's writing guidance treats counterargument as part of reasoning, not a ritual section.

### Causal discipline

Correlation, sequence, stated motive, mechanism and causal identification are different claims. A timeline is not proof of cause. A quote is not proof of audience consensus. A single case is not a population-level result. Match the wording and confidence to the actual evidence.

## 9. Explanation and cognitive load

The Open Notebook's science-writing guidance identifies two opposite errors: assuming the reader already knows what the writer knows, and burying the reader under every detail the writer knows. The correct target is the minimum explanation required to follow the article's main argument or story.

Use these methods selectively:

- identify the reader's prerequisite knowledge;
- define a term only when the article needs it;
- introduce concepts near the moment they become useful;
- chunk a complex mechanism into causal steps;
- use an analogy only if it preserves the important structure and does not imply false equivalence;
- distribute a large explanation across the article when the reader needs it in stages;
- reactivate a key term or prior result when the reader must use it again;
- remove detail that does not change understanding, choice or interpretation.

A term count is not a quality metric. The question is whether the reader can maintain the relevant mental model without repeatedly stopping to reconstruct it.

## 10. Emotion, tension and aftershock

The Novel system distinguishes emotional range from tension and treats aftershock as part of consequence. For nonfiction, use emotional craft to clarify human stakes, not manufacture them.

A useful diagnostic chain is:

`verified event or pressure -> observable response / stated account -> consequence -> changed relationship or choice -> aftershock / longer-term implication`

The article may use contrast, uncertainty, loss, humor, relief or moral conflict when supported by the material. Do not exaggerate harm, assign feelings without evidence, or force a tragedy-to-hope arc. A technical essay may have intellectual tension rather than emotional drama.

## 11. Dialogue, quotations and voice

Dialogue can reveal competing goals, social power, avoidance, uncertainty and subtext. In nonfiction it must remain authentic and contextualized.

- preserve the source's meaning and tone;
- attribute accurately;
- do not stitch separate remarks into a misleading exchange;
- do not invent or silently improve quotations;
- paraphrase when exact wording is unreliable or unnecessary;
- distinguish a source's stated view from the author's interpretation.

Distinctive voice is not catchphrases. It emerges from what a speaker notices, values, refuses, jokes about, treats as evidence and does after being challenged. In an essay, the author's voice similarly emerges from stance, selection, judgment, attention and rhythm—not from forced slang or random short sentences.

## 12. Prose, paragraph economics and transitions

For claim-heavy reasoning, use the optional companion `long-form-argument-engineering.md` when the article depends on a thesis, interpretation, causal explanation, comparison or recommendation. For deep sentence- and paragraph-level execution, use the optional companion `long-form-microcraft-playbook.md` when a specific microcraft problem warrants it. It expands the diagnostics below into actionable mechanisms, counterfactuals and selective revision passes. It is not a mandatory checklist; the exact owner-accepted article's retrospective mapping is `long-form-microcraft-replay-01-the-rug-became-the-ad.md`.

### Paragraph economics

A paragraph should perform a real job: introduce a fact/scene, explain a mechanism, advance a claim, compare, challenge, qualify, show a consequence, change perspective or deliver/open a payoff. A paragraph that only announces importance, repeats the prior point or narrates the outline must justify its space.

### Transitions

A transition should reveal the relationship between ideas: continuation, contrast, concession, cause, example, elaboration, consequence or shift in scale. Reusing old information briefly before adding new information can help readers connect the chain. Words such as “therefore” should be used only when the logic is genuinely causal; they cannot repair a missing inference.

### Rhythm

Vary paragraph and sentence lengths when the thought changes. Strong rhythm often comes from alternating informational jobs—fact, mechanism, example, counterexample, consequence, reflection—not cosmetic randomization. Avoid fixed short-sentence quotas, punctuation tricks, repeated rhetorical scaffolds and universal phrase blacklists.

### Voice-first anti-generic review

Draft from the actual material, author stance, article blueprint and strongest available owner-approved voice evidence. Treat “AI-like” language as a diagnostic symptom, not a generation style. Look for clusters where generic staging, abstract summary, repeated contrast constructions or platform caricature displace material-specific thinking. Repair the smallest evidenced defect; do not globally humanize sound prose.

### Original expression

Research provides evidence, not a sentence template. Normalize sources into claims, relationships, numbers and notes; draft from understanding; compare distinctive wording and structure back to source material; rewrite patchwriting. Do not imitate a novelist's or journalist's signature phrasing, characters, scene, imagery or unique arrangement.

## 13. Ending and payoff design

Design the ending while planning the article, not only after drafting. A strong ending should complete the reader contract by delivering one or more of:

- a clear answer to the central question;
- a revised mental model;
- an implication the evidence genuinely supports;
- a decision distinction or practical test;
- a meaningful consequence or human aftershock;
- a bounded uncertainty that tells the reader what remains unresolved.

Do not end merely because the material ran out. Do not bolt on generic optimism, a checklist, a call to action or a final question unless the article earns it. The ending need not tie every issue into a neat bow; it must leave the reader with an intentional final understanding.

## 14. X Article packaging as separate products

When the user requests X publication assets, give each item a distinct job:

- **Title:** truthful acquisition promise.
- **Opening / first screen:** orientation, reason to care, thesis/question and early proof of value.
- **Article body:** full argument, narrative and payoff.
- **Cover:** central visual promise; not a duplicate of the title.
- **Inline images:** distinct explanatory or narrative functions attached to precise article anchors.
- **Teaser post:** reason to enter the article, not a duplicate opening paragraph.
- **Thread / pinned reply / CTA:** only when requested and useful; do not assume an X Article is a long thread.

Review semantic redundancy across all assets. Verify the actual mobile rendering/copy handoff when it matters. A local preview does not prove the X composer preserves the same formatting or crop.

## 15. Review and revision order

Review the actual current draft, not the writer's intention or the outline alone. Select applicable lenses from the 16 dimensions plus these hard editorial questions:

1. **Goal / reader contract:** does the article do the requested job for the intended reader?
2. **Thesis / contribution:** is there a real insight beyond topic summary?
3. **Evidence / truth:** are factual, causal, predictive, normative and interpretive claims correctly distinguished and supported?
4. **Argument / narrative movement:** does each section change the reader's model or experience?
5. **Reader retention:** are questions, payoffs and transitions honestly earned?
6. **Cognitive load:** can a cold reader follow the concepts without the writer filling gaps from memory?
7. **Voice / originality:** does the prose sound like a situated author rather than a template or source paraphrase?
8. **Ending:** does the piece pay off its promise?
9. **Platform / delivery:** do the requested title, body, images, translation and publishing handoff work as separate products?

### Root-first repair

Locate the earliest defect that makes downstream work invalid:

`reader / purpose -> topic contribution -> research -> thesis / warrant -> macro structure -> section sequence -> paragraph logic -> scene / explanation -> sentence / style -> platform packaging -> rendered delivery`.

This is a dependency guide, not a mandatory linear workflow. If a new fact defeats the thesis, reopen research and all dependent sections. If a paragraph is merely repetitive, do not restart the whole research stage. Preserve unaffected work and recheck the exact revised version.

### Reverse outline

After drafting, write one sentence for each paragraph or section describing what it actually does. Then test order, gaps, duplicate functions, overloaded paragraphs, missing transitions and conclusions that appear too late. The reverse outline must describe the manuscript, not the original plan.

### Independent review boundary

A separate model prompt or named role is not automatically independent. Same-session criticism is useful for revision but remains self-review. Use a cold reader, qualified subject reviewer or independently executed review when the stakes justify it; bind findings to the exact draft version. Never claim a real reader, expert review or publication acceptance that did not occur.

## 16. Anti-patterns and counterfactual tests

| Failure | Counterfactual test | Repair direction |
|---|---|---|
| Topic report with no thesis | Hide the title: what does the article actually argue? | Return to reader problem and competing explanations |
| Hook without payoff | Remove the title/opening: does the body answer the promise? | Rebuild promise or body; do not add more suspense |
| Endless open loops | List every major question and its answer/payoff status | Pay old debts before creating larger ones |
| Encyclopedic exposition | Remove a technical explanation: does the central argument become harder to follow? | Keep only the minimum needed; distribute the rest or omit |
| Decorative case/person | Remove the case: does the reader lose a distinct inference? | Give the case a specific function or remove it |
| Invented scene/interiority | Can every quoted word, action and detail be traced to a real source? | Attribute, summarize or remove unsupported detail |
| Fake causal certainty | Could the same evidence be true while another cause explains the result? | Add warrant/evidence, qualify or narrow |
| Mechanical paragraph rhythm | Do several paragraphs perform the same rhetorical job? | Change informational function, not punctuation randomly |
| AI-humanizer rewrite | What exact span is generic, inaccurate or repetitive? | Minimum semantic repair from source facts and author stance |
| Decorative counterargument | Does the alternative actually threaten the thesis? | Strengthen, refine or replace the thesis |
| Generic conclusion | What new understanding does the final paragraph leave? | Close the reader contract with a real implication or boundary |
| Forced novel structure | Would scene, character, emotion or suspense improve this specific reader job? | Mark N/A; use direct explanation or instructions |

## 17. Learning and promotion protocol

The Novel repository's masterwork process provides a strong learning discipline: source identity and coverage, cold-read trace, structural annotation, microcraft annotation, positive/negative comparison, ablation/counterfactual, closed-context reconstruction, claim-conditioned cross-work comparison, transfer experiment, adversarial review and bounded promotion.

Adapt that discipline to editorial work:

1. Select a specific writing problem/dimension, not “learn to write better” as an unbounded goal.
2. Study several high-quality examples and at least one counterexample; preserve source/version/genre/context.
3. Distill the functional mechanism, not the surface wording or story subject.
4. State where the mechanism should work, where it should fail and what competing mechanism could explain the same effect.
5. Run an ablation: remove or replace the device and predict what reader value changes.
6. Transfer it into a materially different article genre or topic.
7. Review the actual before/after artifact and reader evidence when available.
8. Keep the method as `REFERENCE` or `CANDIDATE` until independent replays, negative evidence, cross-task transfer, regression, rollback and owner acceptance support promotion.

A novel's successful device is not proof of a universal nonfiction method. A synthetic writing exercise is not a real reader test. A CI pass proves code contracts, not literary quality.

## 18. Professional and research references

- Harvard College Writing Center, [Thesis](https://writingcenter.fas.harvard.edu/thesis): arguable, appropriately scoped thesis built from analysis of evidence.
- Harvard College Writing Center, [Tips for Organizing Your Essay](https://writingcenter.fas.harvard.edu/tips-organizing-your-essay): decompose thesis into claims; use provisional subheadings; reverse-outline the actual draft.
- Harvard College Writing Center, [Counterargument](https://writingcenter.fas.harvard.edu/counterargument): treat serious alternatives as competing answers; revise the thesis when a counterargument survives.
- Harvard College Writing Center, [Transitions](https://writingcenter.fas.harvard.edu/transitions): use old-to-new information and name the relationship between ideas; do not use causal transitions without causal logic.
- Nieman Storyboard, [Six Writing Tips for Crafting Scenes](https://niemanstoryboard.org/2005/03/24/six-tips-for-crafting-scenes/): camera angle, scene/summary choice and selective detail.
- Nieman Storyboard, [Reporting and Writing Scenes](https://niemanstoryboard.org/2023/04/20/narrative-journalism-reporting-writing-scenes/): reported scenes are built through observation, questioning and reporting; journalists do not fabricate them.
- Nieman Storyboard, [Character: The Beating Heart of Narrative](https://niemanstoryboard.org/2023/05/11/profiles-character-development-reporting-sources/): agency, observed behavior, carefully chosen detail and the boundary against invented interior thoughts.
- Nieman Storyboard, [Endings](https://niemanstoryboard.org/2023/05/19/narrative-writing-story-structure-endings/): plan and craft the ending rather than stopping when material runs out.
- The Open Notebook, [Explaining Complexity](https://www.theopennotebook.com/2015/07/07/explaining-complexity/): explain the minimum necessary model and distribute complex explanations when appropriate.
- Mar et al., [Memory and comprehension of narrative versus expository texts: A meta-analysis](https://doi.org/10.3758/s13423-020-01853-1), *Psychonomic Bulletin & Review* (2021): across more than 75 samples and 33,000 participants, narrative texts showed an average comprehension/recall advantage over expository texts (Hedges' g = .55). Effects varied substantially; this supports considering narrative as one useful information form, not forcing every article into a story.
- [Reuters Standards and Values](https://reutersagency.com/about/standards-values/) and [SPJ Code of Ethics](https://www.spj.org/spj-code-of-ethics/): accuracy, attribution, no fabrication/plagiarism, correction and contextual fairness. These are ethical constraints for reporting, not a demand that every opinion essay adopt a newswire voice.

## 19. Transfer boundaries and current assurance

- Novel system dimensions are a useful diagnostic ontology; they are not a ready-made article template.
- Fiction may invent scenes, thoughts, dialogue, settings and causal events. Nonfiction may not.
- Financial-writing methods are domain-specific where they depend on company universes, value chains, market roles, financial metrics or investment compliance. Transfer only general reader-value, evidence, editorial and style mechanisms.
- The Financial Writing repository's own 2026-11-16 stability audit reports that historical self-reviewed samples do not establish independent quality acceptance across topics/products. Keep its writing methods as candidates, not universal proof.
- The Novel repository's current masterwork mechanism registry keeps distilled mechanisms at `REFERENCE`; its mastery model requires materially different transfer and real reader/editor/platform outcome before claiming transfer verification.
- This atlas is therefore a candidate method. It may guide scoped trials but must not be promoted to `ACTIVE_REFERENCE` or treated as proven until SMS completes real, materially different article replays, counterexamples, independent readback, regression, rollback and owner acceptance.