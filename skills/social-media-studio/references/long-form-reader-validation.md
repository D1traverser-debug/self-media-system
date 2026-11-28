# SMS Long-form Reader Validation Protocol

> Status: `CANDIDATE_REQUIRES_REVALIDATION`  
> Owner: `Social Media Studio / editorial_writing / long_form_editorial`  
> Version: `2026-11-28 / R01`  
> Scope: formative, independent reader evaluation of substantial articles, essays, explainers, tutorials and X Articles.  
> This protocol distinguishes comprehension, usefulness, trust, task success, preference and distribution. It is not a universal sample-size formula, a popularity predictor, a factual verifier or a publication certificate.

## 0. Purpose and authority

R01 operationalizes the reader-side review obligation in F12. Use it when the article is consequential, its intended value depends on reader understanding, the audience/genre is unfamiliar, competing drafts need comparison, or the owner explicitly requests independent reader validation.

Do not run a formal reader study for every short post or low-risk draft. A lightweight self-read may be enough for a simple task, but it must not be described as independent validation.

Authority order: owner brief and target-reader definition > CAOS governance > domain/source verification > F12 editorial method > A01 argument engineering / M01 microcraft where relevant > this protocol. R01 cannot authorize unsupported claims or publication.

## 1. First decide what must be validated

“Does the article work?” is not a testable research question. Select the outcome that matters for this article.

| Validation target | What to observe | What it does not establish |
|---|---|---|
| **Comprehension** | Can the reader accurately restate the central idea, mechanism, distinction or instructions? | Factual truth or agreement |
| **Argument understanding** | Can the reader identify the thesis, major grounds, reasoning bridge and material limitation? | That the thesis is correct |
| **Explanation transfer** | Can the reader apply the model to a new but relevant example? | Broad learning retention or long-term behavior change |
| **Procedural usability** | Can the reader complete the intended task, identify prerequisites and recover from a foreseeable failure? | That the procedure is safe or technically correct without expert verification |
| **Narrative coherence** | Can the reader follow the sequence, stakes, actors and payoff without invented explanation from the author? | That every reader must feel the same emotion |
| **Reader value** | Can the reader name what is newly understood, decided or made possible? | Commercial success or virality |
| **Trust / credibility** | Which claims feel unsupported, overbroad or unclear, and why? | Objective source accuracy; fact-checking remains separate |
| **Preference / resonance** | Which version or element the reader prefers and what they respond to | Comprehension, truth or representative audience preference |
| **Distribution outcome** | Observed opens, completion, sharing, saves, replies or other platform events | Causal proof of writing quality or reader understanding |

Choose one primary outcome and only the secondary outcomes needed to explain it. Do not collapse these dimensions into a single quality score.

## 2. Define the reader and the test boundary

Before recruiting or reviewing, state:

- **Reader segment:** who the article is actually for, including relevant prior knowledge and context.
- **Reader job:** what they came to understand, decide, feel, compare or do.
- **Starting state:** what they are likely to know, misunderstand or assume before reading.
- **Expected state change:** the specific understanding or capability the article should produce.
- **Out-of-scope reader:** who the article is not designed for, where relevant.
- **Critical misunderstanding:** the misunderstanding that would make the article fail even if the prose sounds polished.

Recruit readers who reasonably match the intended segment. An expert can assess domain precision but may not represent a novice reader. A novice can reveal unexplained concepts but may not assess specialist validity. A skeptical reader can test the argument but should not be treated as the whole audience. These roles are complementary, not interchangeable.

Do not recruit only colleagues, fans or people already persuaded by the thesis. Do not claim audience representativeness from a convenience sample.

## 3. Choose the evaluation mode

### 3.1 Silent cold read + retrospective recall

Use when the goal is to observe a relatively natural first reading and test what the reader actually understood.

1. Give the reader the actual draft in the intended reading format. Do not explain the thesis, outline, intended emotion or “important points” first.
2. Ask them to read normally. Do not interrupt to teach or defend the article.
3. After reading, remove the draft from view where practical and ask for an unaided restatement before asking specific questions.
4. Then return to exact passages and ask what they understood there.

This mode is usually preferable when concurrent narration would interrupt reading rhythm or alter attention.

### 3.2 Think-aloud review

Use when the specific question concerns where a reader becomes confused, what they expect from a heading, how they interpret a diagram, or how they navigate a procedural explanation.

- Explain that the draft is being evaluated, not the reader.
- Invite spontaneous thoughts; do not demand an explanation for every reaction.
- Use minimal neutral prompts such as “What are you thinking?” only when the reader falls silent.
- Record the exact passage and the reader's words or observed action.
- Recognize that speaking aloud can change the reading experience and that participants may rationalize or give socially desirable answers.

If natural reading rhythm is the main target, prefer silent reading followed by retrospective probing. Think-aloud and silent reading answer different questions; neither is universally superior.

### 3.3 Task-based review

Use for tutorials, guides, explainers that promise practical capability, or articles that lead to a concrete decision.

- Give a realistic scenario that does not reveal the intended answer.
- Ask the reader to perform the task using only the article.
- Observe success, hesitation, wrong turns, missing prerequisites and recovery behavior.
- Separate article-caused failure from missing tools, external constraints or participant unfamiliarity.
- Verify any technical, legal, financial, medical or safety-critical procedure independently with qualified domain review.

### 3.4 Variant comparison

Use only when there is a real decision between materially different drafts or openings.

- Define the comparison question before showing variants.
- Keep irrelevant conditions stable where practical.
- Counterbalance or randomize order to reduce order effects.
- Do not tell participants which version the author prefers.
- Compare the same reader outcome, not vague preference alone.
- A small qualitative comparison can reveal why one variant works better for those readers; it cannot establish a population-wide lift or statistical significance.

## 4. Use neutral prompts

Start with unaided, open questions. Do not reveal the thesis and then ask the reader whether they understood it.

### Core post-read prompts

1. “What do you think this piece was mainly trying to explain, show or argue?”
2. “What, if anything, changed in your understanding after reading it?”
3. “Which part most influenced that understanding? What did you take from it?”
4. “Was there any point where you were unsure what the writer meant or why it mattered?”
5. “What do you still disagree with, doubt or want evidence for?”
6. “If you were explaining the useful part to someone else, what would you say?”

### Argument-specific prompts

- “What is the main claim, in your own words?”
- “What evidence supports it, and how do you think that evidence connects to the claim?”
- “What is the strongest alternative explanation you can see?”
- “What does the article explicitly not establish?”

### Explanation-specific prompts

- “Can you explain how the mechanism works without using the article's wording?”
- “What would happen in this new example?”
- “Which condition would make the explanation stop applying?”

### Tutorial / procedural prompts

- “Using only this guide, show me how you would complete this task.”
- “What would you do if this expected result did not appear?”
- “Which prerequisite or warning did you need before starting?”

### Avoid leading questions

Do not ask:

- “Did you understand the author's point that X?”
- “Wasn't the example helpful?”
- “Did the ending feel inspiring?”
- “Would you share this?” as a proxy for comprehension.

Do not paraphrase the reader's response into the answer you hoped to hear. Ask for clarification without suggesting the preferred interpretation.

## 5. Capture evidence, not impressions

For every material observation, record:

| Field | Meaning |
|---|---|
| Reader / segment ID | Anonymized identifier and relevant prior-knowledge profile |
| Test objective | The specific reader outcome being examined |
| Draft identity | Exact article version/hash and rendered format |
| Location | Paragraph, heading, image or task step |
| Observation | Verbatim statement, action, hesitation or task result |
| Reader interpretation | What the reader believed the passage meant |
| Intended meaning | The meaning supported by the actual article and evidence |
| Gap type | Missing context, ambiguous referent, hidden warrant, weak transition, jargon, overload, false expectation, unsupported claim, task prerequisite, or value mismatch |
| Severity | Critical, major, minor or preference-only—with a reason |
| Alternative explanation | Could the issue arise from audience mismatch, prior knowledge, device, task wording or facilitation? |
| Proposed root | Earliest article dependency likely responsible |
| Revision / disposition | Change, narrow, clarify, retain with reason, or defer |
| Re-test | Whether the changed version resolves the original problem without creating a new one |

Preserve exact quotations only with appropriate consent and privacy controls. Otherwise anonymize and paraphrase carefully without changing meaning.

## 6. Interpret findings without overclaiming

Separate these outcomes:

- **Comprehension failure:** the reader cannot accurately reconstruct the intended point or mechanism.
- **Reasonable alternative interpretation:** the text permits more than one plausible reading; likely an ambiguity to resolve or intentionally preserve.
- **Disagreement:** the reader understands the claim but rejects its grounds, warrant, values or scope. This may be a healthy challenge, not a writing failure.
- **Knowledge gap:** the reader lacks background the article reasonably assumes, or the article failed to supply necessary context. Decide against the target-reader contract.
- **Value mismatch:** the reader understands the piece but does not need what it offers. Revisit audience and promise, not sentence polish.
- **Preference:** the reader likes a tone, example or structure. Preference matters only if it supports the intended reader job and does not compromise truth or clarity.
- **Factual challenge:** the reader identifies a source, definition or inference problem. Return to research and expert review; do not treat reader confidence as proof either way.
- **Facilitation artifact:** the task or question unintentionally primed the response. Repair the test before changing the article.

One reader's confusion is a signal to investigate, not automatic proof of universal failure. Repeated independent observations at the same point increase confidence that a material issue exists, but a small qualitative sample does not estimate population prevalence.

Do not average away a critical misunderstanding. Do not count every preference as a defect. Do not force a rewrite when the reader is outside the intended audience or the interpretation is factually unsupported.

## 7. Sample size and evidence strength

There is no universal number of readers for every article. Choose the sample according to:

- number and diversity of intended reader segments;
- consequence of misunderstanding;
- whether the goal is exploratory diagnosis or quantitative comparison;
- variability in prior knowledge;
- whether new sessions continue to reveal materially new failure modes;
- available time and review burden.

Small formative sessions can uncover important issues but cannot establish population-wide comprehension, preference or impact. Do not copy a usability-testing sample-size heuristic into every editorial task. If quantitative claims are required, design a separate study with a defined population, comparison, sampling strategy, measures, sample-size rationale and analysis plan before collecting data.

## 8. Separate reader validation from other assurance

| Assurance question | Appropriate reviewer / evidence | Not a substitute |
|---|---|---|
| Is the claim factually supported? | Primary-source check, domain expert, reproducible calculation | Reader comprehension |
| Is the inference valid? | A01 argument audit, qualified subject review, counterexample | A reader saying “sounds convincing” |
| Can the target reader understand it? | Independent cold reader, task-based comprehension evidence | Author self-review or another model's agreement |
| Can the reader use the procedure? | Observed task completion and failure recovery, plus technical verification | “Looks clear” comments |
| Does the platform distribute it? | Actual platform analytics under observed conditions | A writing-quality score |
| Does it create long-term value? | Appropriate longitudinal outcome evidence | Immediate likes, clicks or one interview |

A second LLM is not automatically an independent reviewer. It may be useful as an adversarial assistant, but it shares many model-family and prompt-context risks. Label it as auxiliary model review, not cold-reader evidence.

## 9. Revision and recursive re-entry

For each major finding:

1. Bind it to the exact draft and passage.
2. Determine whether the failure is in audience, promise, research, warrant, structure, paragraph, sentence, visual, translation or task design.
3. Reopen the earliest contradicted dependency rather than patching only the visible sentence.
4. Preserve unaffected sections and their evidence.
5. Make the smallest revision that actually addresses the root.
6. Re-test the same reader outcome on the revised version; add a new reader where prior exposure could bias the result.
7. Check for regressions in factual scope, author voice, article value and other reader segments.
8. Record unresolved disagreements and limits; do not manufacture consensus.

## 10. Decision and reporting

A reader-validation report should contain:

- objective and intended reader segment;
- method selected and why;
- exact draft version and delivery format;
- participant selection limits;
- neutral prompts / tasks used;
- observations with passage-level evidence;
- comprehension, value, trust, task-success and preference findings kept separate;
- root-cause decisions and revisions;
- re-test results;
- remaining unknowns and assurance gaps;
- whether the evidence supports a scoped revision, a broader study or no change.

Allowed dispositions:

- `COMPREHENSION_SUPPORTED_FOR_TESTED_SEGMENT` — readers in the tested segment reconstructed the intended meaning under the tested conditions; not a universal guarantee.
- `MATERIAL_CONFUSION_FOUND` — one or more consequential misunderstandings require investigation or repair.
- `VALUE_MISMATCH_FOUND` — readers understood the piece but it did not serve the tested reader job.
- `TASK_FAILURE_FOUND` — the tested task could not be completed reliably from the article under the test conditions.
- `PREFERENCE_DIFFERENCE_ONLY` — preference varies without a demonstrated comprehension or task failure.
- `INSUFFICIENT_EVIDENCE` — the test cannot support a confident disposition.
- `NOT_TESTED` — no independent reader evidence was collected.

Never convert one successful session into `QUALITY_VERIFIED`, `AUDIENCE_APPROVED`, `HIGH_RETENTION` or `PUBLISHING_AUTHORIZED`.

## 11. Privacy, consent and reader burden

- Explain the purpose and whether notes, audio, video or screen recordings will be retained.
- Obtain consent before recording; provide a non-recorded alternative where feasible.
- Collect only information relevant to the reader segment and test question.
- Anonymize notes and do not expose private article drafts or participant identities beyond the authorized workspace.
- Keep sessions proportionate; do not make a reader complete a long survey when a focused read and a few neutral questions answer the research question.
- Do not pressure participants to agree, praise the author or finish an article they no longer wish to read.

## 12. Relationship to F12, A01, M01 and CAOS

- **CAOS** defines the objective, uncertainty, evidence threshold, competing explanations, decision authority and acceptance boundary.
- **F12 Long-form Editorial** owns the overall article and its reader contract.
- **A01 Argument Engineering** tests whether claims and warrants withstand evidence and serious alternatives.
- **M01 Microcraft** repairs material sentence-, paragraph-, transition-, detail-, voice- and payoff-level problems.
- **R01 Reader Validation** tests what an intended reader actually understands or can do under stated conditions.

The modules are complementary, not a fixed sequence. Reader confusion may reveal a sentence problem, an argument gap, a missing piece of research or a wrong audience promise. Re-enter the earliest contradicted dependency. A reader's disagreement does not automatically falsify the claim; a writer's explanation does not automatically repair a reader's confusion.

## 13. Research references and evidence limits

- Nielsen Norman Group, [Usability Testing 101](https://www.nngroup.com/articles/usability-testing-101/) — realistic participants/tasks, observation and neutral facilitation. This is a UX method adapted cautiously for editorial comprehension, not a claim that reading is identical to interface usability.
- Nielsen Norman Group, [Checklist for Moderating a Usability Test](https://www.nngroup.com/articles/usability-checklist/) — setting expectations, think-aloud use and open follow-up questions.
- Nielsen Norman Group, [Avoid Leading Questions to Get Better Insights](https://www.nngroup.com/articles/leading-questions/) — how question wording can prime or distort participant feedback.
- Nielsen Norman Group, [Writing Tasks for Quantitative and Qualitative Usability Studies](https://www.nngroup.com/articles/test-tasks-quant-qualitative/) — qualitative exploratory tasks differ from controlled quantitative tasks; pilot task wording.
- UK Government Office for Health Improvement and Disparities, [Think aloud study: qualitative studies](https://www.gov.uk/guidance/think-aloud-study-qualitative-studies) — benefits and limitations of think-aloud, including social-desirability effects and the fact that it cannot establish downstream outcomes.

These references inform a candidate protocol. They do not prove that this exact protocol improves article quality. Editorial comprehension, factual accuracy, reader preference, distribution and long-term outcomes remain distinct.

## 14. Promotion requirements

Status: `CANDIDATE_REQUIRES_REVALIDATION`.

Promotion requires real use on materially different long-form tasks, at least one deliberate negative case, independent reader evidence from appropriately selected target segments, passage-level observation, revision and re-test, owner burden/cost comparison, privacy-safe records, regression, rollback and CAOS acceptance. A same-model simulation, author self-review, one friendly reader, platform metrics alone or a successful software test cannot promote R01.