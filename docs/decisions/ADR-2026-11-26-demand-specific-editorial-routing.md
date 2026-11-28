# ADR-2026-11-26 — Demand-specific editorial routing and audience intent

**Status:** Candidate implementation on the isolated Draft PR #56. Exact-head CI and owner-outcome acceptance remain separate gates.

## Problem

The capability registry listed exact demand names but returned only group-wide knowledge, methods, Skill sections and roles. A short caption could therefore retrieve the same broad references as a long article or news/video editorial method. The current Skill asked the operator to choose applicable resources, but there was no executable demand-level mapping or explicit fallback state.

The deliverable model typed SHORT_COPY, but the editorial inspector handled only platform packages and long articles. Public-facing content also lacked a typed, optional place to record audience value and intended response without presenting them as measured performance.

## Competing explanations

1. Assistant execution lapse only: relevant short-copy guidance existed, but it was not read or applied. This is true for the interrupted session, but does not explain why the registry cannot resolve exact demand resources.
2. Capability-routing defect: supported. capability_lookup accepts only a capability group and returns group-wide resources; it cannot distinguish short copy, long-form editorial, platform title, tags or cover copy.
3. Missing audience contract: supported. the brief can contain audience text and typed clauses, but a deliverable cannot structurally carry an optional, source-bound think/feel/do hypothesis and a reasoned primary action.
4. Missing creative-quality oracle: still open. Structural inspectors cannot establish humor, naturalness, originality, visual craft or observed audience response.

## Alternatives

- Prompt-only correction: rejected as the sole repair. It leaves the same over-broad resolver and no regression oracle.
- A second demand-routing registry: rejected. It duplicates capability ownership and creates another source of truth.
- Demand profiles inside the existing capability registry: selected. Existing groups remain the on-demand index; profiles add scoped references only for exact demands that have been reviewed. Unprofiled demands report GROUP_LEVEL_FALLBACK rather than pretending to have exact routing.
- Mandatory audience-response fields for every task: rejected. Communication intent is optional and limited to public-facing deliverables where audience response materially affects the outcome.

## Decision

1. Keep one modular-monolith control plane, one capability registry, one StudioEngine, one ledger and one scheduler.
2. Add optional demand_profiles inside existing professional_capability_groups; resolve by exact demand ID and expose an explicit group-level fallback when no profile exists.
3. Keep group-level executor routes as candidate metadata. A profile does not prove a local operation or current session provider is available.
4. Narrow editorial_writing and platform_packaging shared references to common material; place short copy, long-form, localization, platform fields and news satire references in their respective demand profiles.
5. Restrict EDITORIAL_PACKAGING to genuine news/current-affairs video satire. It is not a default method for gameplay, pets, fictional entertainment or ordinary creator captions.
6. Narrow benchmark-policy to conditional complex visual/motion production; do not route it as a default writing method.
7. Add an optional CommunicationIntent value to public-facing DeliverableContract types. It separates audience, value promise, think/feel/do hypotheses, one primary action when an action is declared, action rationale, speaker relationship and grounding references.
8. Add a standalone short-copy structural inspector and optional CTA field. Structural PASS never means creative quality, current platform compliance, publication authority or observed engagement.
9. Keep new reference methods in candidate status until distinct-task replay, counterexamples, regression and owner acceptance.

## Research and scope limits

- Jonah Berger, [What Gets Shared, and Why? Interpersonal Communication and Word of Mouth](https://doi.org/10.1146/annurev-psych-013024-031524), Annual Review of Psychology, 76 (2025), 559–581.
- Yingying Cai, Syafila Kamarudin and Saiful Nujaimi, [Willingness to share information on social media: a systematic literature review (2020–2024)](https://doi.org/10.3389/fpsyg.2025.1567506), Frontiers in Psychology (2025).
- [X Help Center: About Articles](https://help.x.com/en/using-x/articles).
- [TikTok for Business Creative Center](https://ads.tiktok.com/business/creativecenter/inspiration/popular/pc/en). Advertising guidance only, not proof of organic ranking behavior.

The literature supports a multi-dimensional, context-dependent model, not a universal viral trigger. Survey-heavy and topic-specific research cannot establish causal effects for every entertainment niche or platform. Platform documentation is a current surface reference, not an algorithm guarantee.

## Falsifier and rollback

The decision is falsified if exact-demand lookup still returns unrelated news/visual methods for ordinary short copy, if fallback is hidden, if optional communication intent forces CTAs or invented audience psychology, or if the new inspector is treated as creative acceptance. Roll back the profile mappings, optional field and inspector as one coherent change; preserve the existing nine-group control plane and historical event/artifact records. No mainline merge, external publication or provider effect is authorized by this ADR.
