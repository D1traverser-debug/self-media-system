# ADR — Do not confuse any valid draft with final selected deliverable

Date: 2026-11-27. Status: CANDIDATE, SMS Draft PR #56.

## CAOS root cause, alternatives, falsifiers
Actual user requirement: an intended final deliverable (one title, one chosen design per ratio, or one transform preserving its source audio), not "some candidate has good metadata". Inspection currently used `any(candidate.conformance == MATCH)`; multiple current alternatives could hide a newer invalid or unselected output. Project release coverage used `any(ACCEPTED)` and did not reject two accepted artifacts of one variant. `MEDIA_TRANSFORM` source audio promise was not consulted by the actual-byte inspector. Alternative "choose newest timestamp" rejected: newest draft is not owner choice and timestamps are not authorization. Alternative "aesthetic grade via MIME/width" rejected: a metadata probe is not source-bound QA or creative critique.

## Decision and acceptance boundaries
- Pure `select_variant_candidate`: only one current candidate can be inspected as a sole proposal, or a single `ACCEPTED` artifact can be inspected as the individual artifact-level release selection. Multiple current unselected candidates and multiple accepted artifacts are AMBIGUOUS, never silently MATCH. Candidate identity and all findings remain visible. This does **not** infer owner endorsement.
- Project-level release projection requires exactly one accepted artifact per declared variant; duplicate accepted variants are surfaced separately and cannot create a complete release.
- `MEDIA_TRANSFORM` with a declared original audio promise checks absence of an audio stream as a hard mismatch. Even where audio streams exist, metadata cannot establish bitstream, PCM or perceptual identity; status remains UNVERIFIED pending independent source+output bound proof. A true visual pixel match is not sound identity.
- Blank UTF-8 short-copy output is a measured content minimum failure, not proof of natural language or audience value.
- Existing single SQLite ledger, current scope/decision and technical video release gates remain authoritative; no new scheduler, source of release truth, or provider. `inspect-outcome` remains opt-in, read-only and never publishes.

## Regression and challenge
Tests cover two candidate images (one correct 3:4, one incorrect 16:9), selection ambiguity, two individually accepted alternatives, blank caption, no-sound video, video with sound but unverified source identity, single artifact control cases and historical scope isolation. Falsifier: user can prove final selected valid bytes get hidden or earlier wrong choices auto-promote to full owner acceptance. All new behavior must pass exact-head CI before production claims.

## Existing source-bound runtime evidence, not generated receipts
The current `artifact_inputs` SQLite ledger already records immutable, digest-bound derivation edges. The on-demand inspector now uses those edges to locate **one** current exact source video, confirms its file digest, and independently reruns the existing `verify_audio_packet_identity` function over actual source/output packet hashes, checking both file hashes again after the probe. This positive proof is limited to `BITSTREAM_IDENTITY`. No input, multiple candidate source videos, missing source bytes or unavailable FFprobe remain UNVERIFIED; changed source / genuinely different encoded audio is MISMATCH. A legitimate shortened output that matches only a source audio *prefix* remains UNVERIFIED for full-source preservation, with the narrower prefix evidence exposed. The tool's self-generated receipt is not the deciding proof. PCM/perceptual identity and listening quality require their own review. This adds no new ledger or write operation.
