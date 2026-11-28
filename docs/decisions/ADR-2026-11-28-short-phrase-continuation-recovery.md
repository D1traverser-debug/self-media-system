# ADR — Cold-start continuation from short owner phrases

Date: 2026-11-28  
Status: `IMPLEMENTED__REAL_FRESH_CHAT_OUTCOME_OPEN`  
Scope: SMS session entry and continuation recovery. CAOS remains the read-only parent authority.

## Owner operating pattern

The owner often opens a new conversation with a short request such as:
- `继续SMS`
- `继续推特长文1`
- `继续视频制作3`

The intended behavior is not to ask the owner to reconstruct the task. The assistant must recover the target, prior decisions, exact source/artifact state, unresolved work and next action from authorized context. This is a fresh continuation demand, not automatic permission to resurrect an archived workspace, old lease or retired task graph.

## CAOS source and governing requirements

- CAOS parent Skill source read at exact SHA `6a0928b0cc05f9efe3b37aff5fb574db74306cd0`.
- CAOS requires original-source recovery, separate fault obligations, competing causes, falsifiers, exact-head validation, cold-resume adversarial cases and explicit NOT_TESTED/SOURCE_MISSING states.
- SMS requires exact current owner goal, direct-session continuity, narrow dependent-stage decision locks, separate decision/production/verification/business axes, and no automatic resurrection of retired project identities.
- The SMS private method index is a learning locator, not an active task-state ledger.

## Cold-start simulation evidence

### Case A — `继续SMS`

- Resolved target: current SMS architecture construction, not a social-media content deliverable.
- Live PR: #56, open, Draft, unmerged.
- Branch: `refactor/sms-complete-professional-studio-20261126`.
- At simulation time the live head was `b761c85d38e1f04b8564ec133f10585139a946a3`; exact-head PR run `46093986946` passed 618 tests, system audit, topology audit, standalone smoke and historical-program regression smoke.
- The checkpoint was one commit behind the latest live head because its own documentation commit advances the branch; exact live PR/CI readback correctly outranks stale checkpoint fields.
- Open work still includes B01 original requirement source, B02 whole-architecture acceptance, B04/B05 method retrieval and real-task replay, B09 fresh-chat/native-selection and owner-outcome validation, and B10 final reconciliation.
- Correct next behavior: continue the architecture work from the live PR/checkpoint; do not claim the entire SMS product is complete because CI is green.

### Case B — `继续推特长文1`

- The exact literal phrase with suffix `1` was not found in original owner messages available to this retrieval.
- The earlier exact phrase `继续推特长文` is associated in historical conversation retrieval with QUANT X Article **“The Rug Became the Ad”**. The private project index lists it as the first of two separate X Article projects (card 15); the other is Meme X Article **“The Internet Can Copy a Meme. The Market Needs One Ticker”** (card 16).
- Therefore QUANT is the leading provisional interpretation of “longform 1”, not a proven owner-defined alias. The two article projects must never be merged.
- QUANT state recovered: English X Article; the R11 workbench describes it as the final author-review version, unpublished, with internal proofing done and actual X composer/mobile preview and author sign-off still open. The owner explicitly liked the web-preview/workbench form as a reading/copy handoff.
- Important version conflict: the deep-dive and project card bind `QUANT_X_ARTICLE_CINEMA_FINAL.md` to SHA-256 `c4cc97053119bf9cb47dd54ebe7eb85b0c100cb1eaf2906d32e0be679d0f0430`, while the R11 workbench header reports a different article hash beginning `441e7ee5d550` and ending `0c071737f00c`. These may represent distinct revisions; do not edit, publish or declare a single current master until exact bytes and workflow lock are reconciled.
- Correct next behavior: provisionally recover QUANT, read the exact R11 source/master and workflow lock, reconcile article hash and image versions, and only ask a narrow clarification if the suffix `1` materially remains ambiguous before changing content. Do not assume the Meme article is the same task.

### Case C — `继续视频制作3`

- Historical retrieval contains a user-scoped summary associating this short continuation with GTA VI Rain / Motorcycle work, specifically the cover continuation. The private project index also lists `03_GTA6_Rain_Motorcycle.md`. This makes GTA Rain/Motorcycle the strongest candidate, but the exact original definition of suffix `3` was not recovered from a raw transcript.
- The original clip was `this is 10x better than therapy_2026-11-26_100649_kirawontmiss_1048.mp4`, 1280×720, 16:9, approximately 27.062 seconds, ~59.94 FPS, AAC stereo. Audio meaning was not verified in the historical audit.
- The Chinese copy direction was positively accepted. The Chinese cover line `有些游戏，光待着就值了` was selected. English cover direction `NOWHERE TO BE. EVERYWHERE TO GO.` was used in generated candidates, but the complete English title/description/tag package was not finally selected.
- 3:4, 4:3 and 16:9 cover candidates exist. The historical audit says image generation is complete but individual final owner acceptance is not. A later 16:9 brief specifies an independent 1920×1080 composition with copy left, motorcycle central and road/sky right; the output must be checked against this exact brief, not treated as accepted because a 16:9 file exists.
- An earlier assistant summary mapped “video production 3” to Street Fighter 1977. That mapping is unsupported: Street Fighter is project card 09; its internal `C03` means the 16:9 cover-design case, not video project number 3. Do not conflate project ordinal with deliverable sub-stage.
- Correct next behavior: provisionally recover GTA Rain/Motorcycle, verify the exact latest 16:9 file and compare it against the user's 1920×1080 composition contract, then continue only the unresolved production/acceptance step. Do not restart video understanding or copy a line from another video.

## Competing architectural remedies

1. **Rely on the current chat or broad memory alone.** Rejected: a new chat may not contain the prior transcript, and broad summaries can mis-map numbers or stale versions.
2. **Create a new global task database, scheduler or permanent alias registry.** Rejected: SMS already has a project/task ledger for durable work and private Library sources for episodic history; a second control plane would duplicate authority. Do not create a database merely to parse three phrases.
3. **Add a CAOS-governed cold-start retrieval protocol to the existing SMS Skill and entry.** Selected: it uses existing PR/checkpoint state for architecture work and exact private project artifacts/audits for content work, with an explicit ambiguity boundary and no task resurrection.

## Implemented changes

- `skills/social-media-studio/SKILL.md`: added a short-phrase cold-start continuation protocol, Continuation Receipt, source precedence, separate state axes, numeric-suffix ambiguity, retired-workspace boundary, exact-version refresh and concise resume behavior.
- `STUDIO_ENTRY.md`: added the same startup-level requirement.
- `tests/test_learning_source_admission.py`: added regression checks for the three example phrases, Continuation Receipt, numeric-suffix handling, method-card/task identity separation, ambiguity resolution and state-axis separation.
- No CAOS file, original article, video asset, publication artifact or main branch was modified.

## Acceptance boundary

- The three examples have been simulated through available private context, Library files and exact GitHub state.
- `继续SMS` resolves uniquely to the current architecture PR.
- `继续推特长文1` resolves provisionally to QUANT, but suffix `1` is not yet a directly proven owner alias and article hash reconciliation remains open.
- `继续视频制作3` resolves strongly to GTA Rain/Motorcycle, but the exact original suffix definition is not available; the Street Fighter mapping is rejected as an assistant-side conflation.
- Static tests and exact-head CI can prove the recovery contract is present, not that a genuinely fresh ChatGPT client natively selects the Skills or that future creative quality improves. Keep native activation and real fresh-chat outcome `NOT_TESTED` until a first-party trace or actual independent task run is available.
