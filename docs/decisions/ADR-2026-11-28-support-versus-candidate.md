# ADR: Local support is not candidate production

Status: PR candidate; exact-head CI and independent acceptance required.

Baseline: 87004009bd7cef751947f06280b4832c3daba9bc, exact-head CI 46107027243, 628 tests.

Evidence: scope.validate_task_binding checks demand applicability, actual local dispatch membership and variant identity but did not check whether that local operation can produce the requested artifact. For example shot_route supports video_generation but returns a JSON decision, not a generated video. An explicit output binding could incorrectly count it toward candidate coverage. The same issue applies to editorial-plan validation, source evidence audits, business-object validation and delivery archives.

Decision: retain existing route catalog, registries, task ledger and effect gates. Record candidate deliverable type ceilings beside actual registered implementations; discovery intersects them with the exact demand. Typed local admission rejects a candidate binding outside this intersection while still permitting support tasks with intermediate outputs. Bounded technical/metrics reports are valid candidates when explicitly requested; no semantic or provider claim follows. Unstructured work is unchanged. Prior typed decisions with changed route snapshots require existing re-admission rather than silent migration.

Alternatives: adding 54 separate workflows duplicates governance; merely improving descriptions leaves the binding bypass; banning validators entirely destroys useful evidence and legitimate report outputs. The chosen shared check addresses scope, not authoring quality.

Falsifiers: routing receipt as video, source audit as short copy, business-object validation as strategy, archive as platform copy, technical QA as video. Positive cases: scoped technical report, numeric observation report, motion render and bounded media transformation. Exact multi-output roles and bytes, provider availability, independent review and owner outcomes still require separate evidence; type ceilings alone are not full artifact conformance.

Rollback: revert atomic PR commit, no main/CAOS/IPOS mutation or workspace migration.
