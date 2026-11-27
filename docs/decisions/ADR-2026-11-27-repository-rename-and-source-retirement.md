# ADR — Repository rename alignment and source lifecycle/retirement authority

Date: 2026-11-27. Status: CANDIDATE on SMS Draft PR #56.

## Problem, proof and counteroptions
The owner renamed the GitHub repository to `D1traverser-debug/self-media-system` without changing GitHub repository ID 1411170938, active integration branch, PR #56 or the Python distribution. Previously `studio_manifest.repository_slug` still said `social-media-studio`, making package name falsely stand for repository identity. The main README also incorrectly claimed an administrative repository rename was still pending. These are **current contradictions**, not historical naming preferences.

Legacy source has three different lifecycle meanings: (1) domain specialist implementation still imported by current adapters; (2) historical control fixtures still referenced by old regression tests but banned from the active runtime; (3) unused obsolete code with no current execution consumers. Deleting everything under `legacy/` would destroy functioning IPOS, editorial, model-routing and media algorithms. Keeping every old file indefinitely would preserve unnecessary duplicated status authority. Chosen: distinguish by real Python import edges and exact current owner, then remove a demonstrably unused obsolete implementation.

## Changes and limits
- GitHub canonical identity is stored in the current studio manifest, README, entry and Skill, with product/PyPI name explicitly separate. The renamed repository URL is a new source of authority; old project aliases remain historical evidence only.
- Removed `social_media_studio/legacy/operator_view.py` and its sole dedicated retired test. Current current-session status/resume are provided by the one `StudioEngine` ledger; no active import from existing production/adapters used the obsolete operator snapshot. The old source/test remains recoverable from the exact parent Git commit.
- `data/subsystem_catalog.json.source_retirements` records the deletion, reason, successor and baseline; the structural audit rejects a reintroduced deleted file, reintroduced dedicated test or import to a permanently retired module.
- `sms-studio subsystems` now reports `legacy_module_lifecycle` classified by **static import graph only** into `ACTIVE_SPECIALIST_IMPORT_DEPENDENCY_NOT_NEW_CONTROLLER`, `RETIRED_FIXTURE_COMPATIBILITY_NOT_CURRENT_RUNTIME`, or `DORMANT_LEGACY_SOURCE_REQUIRES_CONSUMER_REVIEW`. This does not imply dynamic imports, creative output verification or permissions.
- Legacy standalone CLI/runtime/studio_agents/orchestrator/storage remain fixture-fenced: they still have real test consumers. Removing them requires migrating those fixtures and proving that current state/recovery/rights/quality invariants remain covered. Old data and user projects are not deleted.

## Falsifiers
New canonical manifest fails audit; missing retired code is imported by a current adapter; stale operator view unexpectedly drives user actions; removal breaks current job/legacy regression, smoke, or independent installer. Any such event reopens the earliest mistaken dependency classification rather than relaxing runtime permission gates.

## Second reviewed retirement: obsolete ProgramOrchestrator
`legacy/program_orchestration.py` maintained a second file-backed mutable ProgramRunState and coordination graph. Real current `ProjectTaskService._validate_graph` and `StudioEngine` already own dynamic task dependencies, independent branches, candidate/owner adjudication and failure recovery through one ledger; old ProgramOrchestrator is not imported by that runtime or an active domain adapter. Its sole original direct test consumer was `tests/test_program_orchestration.py`, which exercised a retired example Program graph. Both source and obsolete test are now deleted, with a tombstone rejecting accidental return; current engine coordination regression tests remain. Historical project JSON examples are not removed and no owner workspace or artifact is changed.

The historical singleton runtime, old fixture CLI and old standalone orchestration in `legacy/runtime.py`, `orchestrator.py` and `studio_agents.py` still retain multiple isolated test consumers and are **not** yet eligible for deletion under the present proof threshold.
