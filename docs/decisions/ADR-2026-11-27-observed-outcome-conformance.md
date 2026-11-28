# ADR — On-demand observed deliverable conformance (2026-11-27)

Status: CANDIDATE, Draft SMS integration PR #56.

## CAOS root-cause and alternatives
F03/F12: a typed task candidate stores a declared MIME, digest, producer and variant, but neither MIME truth nor claimed shape is verified from bytes. A static image represented as `.png` or advertised as 3:4 can actually be a JPEG, unreadable bytes or 16:9. A model's high-level claim, file extension, successful task state or technical release PASS must not silently serve as the owner outcome oracle.

Alternative review: a per-video custom QA patch would fail cross-domain reuse; a second job graph/acceptance database would duplicate authority; doing FFprobe and image decoding on *every* `status` call would add unbounded latency to worker scheduling; treating visual dimensions as aesthetic PASS would mislead. Selected: independent **explicit on-demand, read-only, type-sensitive observation port** that reads the *existing* exact artifact records and the owner typed deliverable variants. No new scheduler, approval or result status writes.

## Implementation boundaries
- `domain.conformance.assess_observation` is pure and interprets observed media/text evidence; mismatched shape/MIME/bytes cause MISMATCH; unavailable probes are UNVERIFIED rather than PASS.
- `application.outcome_inspection` owns temporary read-only file probes. Pillow detects actual image bytes; FFprobe probes local media streams; text/json are decoded rather than trusting filename.
- `StudioEngine.inspect_outcome` and `sms-studio inspect-outcome PROJECT` are read-only facades. `status`, `resume`, leases, existing release events and the current immutable artifact ledger are unchanged.
- Each current typed variant carries its expected pixel shape into the existing candidate projection. Variant-specific evidence can now show 3:4 MATCH and 16:9 MISMATCH rather than 2/2 blindly ready.
- Technical conformance does **not** prove sound preservation, visual attractiveness, semantic claims, writing craft, actual source interpretation, review independence, user acceptance or external publication rights; all remain explicitly false/unverified.

## Safety, cost and falsifiers
Actual media probes are opt-in to avoid silently running FFprobe on every status call. FFprobe uses explicit local process invocation with restricted input protocols and timeout. No network fetch or external provider, paid tool or account action is allowed. A mislabeled PNG, wrong dimensions, wrong text encoding, replaced bytes, unavailable FFprobe or missing variants cannot pass the observed conformance gate. Full same-head CI/system topology/durable project tests are required; rollback this isolated slice if it breaks existing content-type independence. The media dimension check is not a replacement for the established canonical video QA report.
