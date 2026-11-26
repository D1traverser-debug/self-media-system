# SMS demand boundary v1 — implementation candidate

Baseline: 7cd1cff75fdb807cab8a23c8991dab793573c051. This change implements a shared declaration validator, not a second owner authority or a new runtime controller. The existing brief and its event history are the sole durable demand state. The original user messages and ordered corrections remain the goal authority outside the runtime.

## Diagnosed failure
The old intake and owner creation validated optional deliverable specs; direct StudioEngine.revise_brief validated the generic brief and scope epoch but did not revalidate typed deliverables. A malformed revision could be stored, only to fail later during resume. Whole-brief invalidation is conservative and remains necessary until task-level semantic dependencies are independently established. No evidence proves that this structural defect alone causes poor editorial work.

## Contract and decisions
Reuse the existing brief, typed deliverables, event identity and decision hash. Do not invent a duplicate demand database, enforce fixed stages, or translate free text into claimed owner requirements automatically. Optional demand_contract v1 is a declaration within the existing brief:
```json
{
  "schema_version": 1,
  "owner_source_refs": ["current-owner-message"],
  "clauses": [
    {"id": "preserve-audio", "kind": "HARD_CONSTRAINT",
     "text": "Keep original audio unchanged",
     "source_ref": "current-owner-message", "deliverable_refs": ["edit"]}
  ]
}
```
Empty deliverable_refs denotes demand-wide application. Clause categories separate outcomes, hard constraints, preferences, prohibitions, acceptance, authorization limits and unresolved questions. A reference is not proof of authentic owner consent. Actual semantic interpretation, conflicts, authorizations and independent acceptance remain separate. Direct requests without typed declarations stay valid and read-only. Existing unstructured briefs remain readable; newly added typed sections cannot silently disappear during revision. Old declaration history is not erased.

Alternative rejected: force all direct requests into a durable typed project, or infer meaning/permissions from natural language using a deterministic parser. Alternative deferred: selective invalidation by clause IDs alone, which is unsound for global or implicit dependencies. No native CAOS activation or real creative outcome is claimed.

## Verification and rollback
Tests cover shared validation, no workspace mutation on intake, invalid typed revision rollback, source and deliverable references, explicit no-effect flags and no silent schema downgrade. Existing scope epoch, task decisions, event identity, release gates, scheduler and provider paths remain unchanged. Revert the candidate commit before promotion if compatibility or topology fails. No migration of existing data is required. Actual owner-source authenticity, correction completeness, semantic contradiction handling, selective invalidation and direct-session adoption remain OPEN. This slice does not promote Architecture V2 or supersede the frozen acceptance matrix.

## Adversarial governance re-entry — 2026-11-26

**Reopened assumption:** A shared structural validator does not prevent silent intent loss.
The initial implementation permitted removing any existing prohibition or rewriting a
structured clause without an acknowledged correction, and RESUME silently discarded
extra user instructions. Both contradict the owner requirement to retain corrections.

**Rival explanations:** (1) model execution drift alone (insufficient; bypass reproducible
from API semantics), (2) missing orchestration framework (not evidenced), (3) incomplete
shared demand evolution boundary (supported by code and targeted regressions).
Read the real scope/intake, engine.revise_brief, existing event history and tests before
choosing the fix. An untrusted owner_source_ref remains an assertion, not approval proof.

**Selected correction:** Keep the single existing brief and event ledger. Structured
contract revisions now require append-only owner source references and explicit
amendments for each changed clause, plus one `@brief` amendment if the enclosing brief
changes. Every new amendment must cite a newly declared correction source. Retiring
a prohibition requires an explicit RETIRE amendment; RESUME with any new fields
fails visibly and instructs the caller to revise the stored brief. This is fail-closed,
not autonomous interpretation, nor unverified permission for public posting.

**Strong counterexamples still OPEN:** A model could invent a source ref; an actual user
may correct two global constraints but the single `@brief` record is not field-level
dependency proof; direct-session messages have no native hook; accepted creative
output and true provider effects are not established. Separate, independent review,
actual user-supplied source binding, and real-result trials remain required.
Rollback: revert candidate branch; no data migration, no mainline mutation.
