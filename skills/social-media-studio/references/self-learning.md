# Self-Learning Protocol

> **Scope — task-neutral Social Media Studio:** Learning is continuous and evidence-triggered, not a fixed production stage or separate scheduler. CAOS remains the parent authority for decision quality and owner-level acceptance. The Studio records project-local candidates and locates shared knowledge; it never promotes candidates automatically. Current authority: repository-root `STUDIO_ENTRY.md` and `social_media_studio/data/studio_manifest.json`.

## 1. Trigger and classify before changing the system

Use this protocol when a quality gap, repeated failure, tool limitation, benchmark gap, source conflict or material ecosystem change appears.

Classify the cause before changing a global rule:

- **Local execution defect:** the project failed to apply an already-correct method. Repair the project; do not change global architecture.
- **Capability/tool gap:** the current method or tool cannot meet the required quality ceiling. Research alternatives and test the smallest material risk.
- **Quality-standard gap:** the team lacks an observable criterion, benchmark or evidence contract. Improve the standard.
- **Systemic architecture defect:** the workflow can repeatedly admit the same class of bad outcome. Only this category normally justifies a global runtime change.

Do not convert every failure into a new role, gate, prompt or permanent rule. Prefer replacing, simplifying or deleting weak mechanisms over stacking patches. A repeated material failure after an accepted fix is a reliability incident: preserve evidence and repair the enforcement/evaluation path before unrelated capability work.

## 2. Learning-source admission: default deny

Seeing content during a session does **not** make it a learning source. It does not become a durable learning source merely by appearing in the conversation. Conversation context, temporary research, user links, summaries, examples, transcripts and side tasks are outside the learning boundary unless explicitly admitted.

A source may enter a candidate only when it is:
1. internal project evidence produced by the declared workflow and present in the work packet; or
2. explicitly imported as an external learning source with affirmative learning authorization and a durable source reference.

If material is marked do not learn, do not persist, exclude from the system, or equivalent, exclude it before durable serialization. Do not create a topic/title/URL/fingerprint denylist for excluded material; that would itself persist a trace. If provenance or authorization cannot be proved, reject the candidate rather than guessing.

## 3. Candidate record

A candidate must preserve:

- the concrete problem and the original acceptance failure or measurable baseline;
- the proposed mechanism, not merely a tool/model name;
- the declared applicability and non-applicability boundaries;
- source references and exact supporting evidence;
- counterexamples and explicit failure conditions;
- replay references and the task contexts in which they were tested;
- a rollback/fallback path;
- owner burden and cost before/after, or a reasoned N/A.

The project learning table is a candidate ledger. `record_learning` always creates `CANDIDATE`. It is not a global method registry and it does not grant execution authority.

## 4. Evidence ladder for shared method promotion

A candidate becomes a shared `VERIFIED_OPERATION` only after the complete evidence chain is accepted:

1. **Real case:** demonstrate the method on an actual owner task with a measurable baseline or prior failure.
2. **Independent replay:** at least two replays on distinct task instances within the claimed applicability. A repeated run of the same unchanged fixture is not cross-task evidence.
3. **Counterexample:** at least one deliberate negative trial that exposes a boundary or failure condition. A valid counterexample does not mean the method should succeed outside its scope.
4. **Cross-task transfer:** demonstrate that the mechanism survives a different task context. Require cross-domain transfer whenever the method claims cross-domain applicability.
5. **Regression:** add a test that would detect recurrence of the original failure.
6. **Rollback:** preserve the previous accepted method and a clear fallback path.
7. **Owner burden/cost:** compare time, cost, credits, rework or coordination before and after; if not measurable, record why it is N/A.
8. **Independent readback:** the reviewer must not have produced the method, the tested outputs, the review report or the cited evidence.
9. **CAOS acceptance:** CAOS independently challenges the evidence, applicability, counterexamples, risk and owner outcome before shared promotion.
10. **Versioned change:** update the shared knowledge catalog and source method through a repository-versioned change containing the evidence, regression result and exact method revision.

No single success, Boolean self-assertion, opaque URI, provider marketing claim or model self-rating satisfies this ladder.

## 5. Knowledge states and authority

- `ACTIVE_REFERENCE`: a source locator that may be consulted; it is not proof that the described method works.
- `VERIFIED_OPERATION`: a method independently validated within its exact recorded applicability and version.
- `CANDIDATE_REQUIRES_REVALIDATION`: an unvalidated proposal; not execution authority.
- `LEGACY_REFERENCE_ONLY`: historical material retained for context; not current authority.
- `RETIRED_EVIDENCE_ONLY`: preserved history without active authority.

Project candidates remain `CANDIDATE`. Shared knowledge promotion requires a versioned repository change with evidence, independent replay, regression and CAOS owner-level acceptance. There is no automatic promotion command. A method that is deliberately task-specific remains project-local rather than being generalized. Cross-project reuse must respect the declared applicability and be revalidated when the target context materially differs.

## 6. Sample-first is conditional on the deliverable

Before expensive or quality-critical production, test the smallest sample that can falsify the highest-risk assumption:

- writing: one representative hook, section or argument;
- static image: one key composition or hero frame;
- video/motion: a short representative motion sample, often 3–12 seconds when appropriate;
- research: one source-backed claim and its counterargument;
- platform packaging: one representative platform variant.

A sample must be judged against the intended final acceptance bar, not merely technical execution. Do not impose motion, audio or video prototypes on text-only or static-image work.

## 7. Research and method selection

When scouting is relevant, compare at least two plausible approaches using primary documentation, inspectable outputs, source code or credible failure reports. Evaluate quality ceiling, repeatability, cost, licensing, observability, coordination burden and lock-in. Distill each promising method into problem, mechanism, evidence, transfer boundary and a falsifiable prototype. Tool names alone never become architecture.

## 8. Governance and execution boundary

Learning is a continuous responsibility, not a mandatory LEARN stage or fixed role pipeline. Roles such as method author, reviewer and owner are temporary responsibilities assigned only when the demand requires them; they are not permanent workers. The task graph is derived from the current goal, and only declared dependencies block parallel work.

A local correction stays local unless evidence proves a systemic defect. Shared rules change only through the versioned knowledge path above. Rejected approaches remain recorded with why they failed so the system does not rediscover them as if new. Revalidate volatile provider facts before reuse, and never let a learned preference override a new owner instruction.
