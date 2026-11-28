# Commercial Direction

> **Scope — 2026-11-24 task-neutral architecture:** Reusable commercial design methods. The industries and account positioning below are historical examples, not a standing owner requirement or default business task. Select scope from the current owner demand. Current authority: repository-root `STUDIO_ENTRY.md` and `social_media_studio/data/studio_manifest.json`.

Historical commercial-axis example: AI applications, software/SaaS, 3C electronics, smart hardware and technology-business explanation, with adjacent expansion into appliance/smart-home, automotive technology, cloud/data/internet services when content fit is strong.

Commercial field, content format and production format are separate decisions. Example: field=3C, format=conflict-led explainer, production=AI assets + motion graphics + screen capture.

A sponsor should enter as a functional part of the story, task or mechanism. The desired viewer reaction is not “I failed to notice the ad”; it is “I knew it was an ad, but the piece was still worth watching.”

For every serious topic, identify: likely advertiser pool, natural product insertion point, brand-safety risks, zero-filming feasibility, demonstration method and whether the topic reinforces the account's long-term commercial label.


### Account, content and commercial measurement (non-video capable)

The existing `business_outcome_metrics` adapter supports a separate `SMS_BUSINESS_OBSERVATION_V1` input schema when the requested outcome is an account, individual content item (including article or image), campaign, offer or portfolio observation. Do not invent Episode IDs or published video minutes for these tasks.

Supply the spec as `outcome_receipt_input` and every actual source JSON as a separate declared, immutable artifact input. The spec contains:

- `schema_version`: `SMS_BUSINESS_OBSERVATION_V1`
- `subject`: `kind` (ACCOUNT, CONTENT, CAMPAIGN, OFFER, PORTFOLIO), exact `id`, optional `platform`
- `window`: timezone-aware ISO `start` and `end`
- `metrics`: entries with `id`, `unit`, `semantics`, and either a `source` object (`input` exact imported JSON name, `path` list of JSON keys/indices) or `unavailable_reason`
- optional `ratios`: entries with `id`, `numerator` metric ID, `denominator` metric ID and `semantics`

Example: a metric path `["metrics","impressions"]` reads that actual number from its separately imported source JSON, not a value asserted in the spec. Each extracted number is linked to source artifact ID, version and SHA-256. Missing sources or incompatible paths reject execution; explicitly unavailable metrics and ratios with missing or nonpositive denominator return null, never an invented zero. A ratio is a raw quotient with explicit units, not automatically a percent. Review the provenance, subject/window and metric semantics against the actual platform export, including whether numerator and denominator are comparable. The result proves only extraction and arithmetic on the declared input bytes, not live platform authenticity, causal improvement or owner acceptance. No account update, purchase, upload or publishing effect is performed. The historical Episode outcome path remains available only when video economics are actually relevant.
