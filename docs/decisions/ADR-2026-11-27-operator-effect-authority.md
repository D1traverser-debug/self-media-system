# ADR — Operator effect authority separate from user task data (2026-11-27)

Status: candidate on Draft SMS PR #56.

## CAOS root-cause replay
Audit F08: a project-registered Python source can execute through `frame_worker.exec_module`. Prior `trusted_code_execution:true` was entirely inside mutable task/spec JSON; rights clearance attests usage rights, not safety of the executable code. `python -I` and filtered environment **are not a sandbox**. No task, assistant, prompt, rights file or tool adapter may promote its own trust to a host process permission.

Alternatives: unconditional execution rejected; a separate scheduling agent / controller rejected; blanket disable of all local production rejected because deterministic tools still fulfill valid owner requests; sandbox claims rejected without tested OS/network isolation. Chosen upper boundary: known risk classification on the *existing production registry* and a fail-closed independent operator process allowlist for unsandboxed source.

## Mechanism and effect limitations
Every registered local operation declares a validated risk class. Unknown risks and implicit registration fail closed. The Python frame operation is `TRUSTED_CODE_UNSANDBOXED` and is checked before dispatch; direct renderer calls repeat the check immediately before any Python process is launched. The process operator must set `SMS_TRUSTED_PYTHON_RENDERER_SHA256` to the exact 64-character lowercase source SHA256 **outside all project/task JSON**. The program rehashes the current file and compares in constant time; changed source or missing/malformed grant is denied. A preexisting independent human rights-clearance review remains required by the original rights path.

This grant is intentionally limited: it is **neither** an OS sandbox, **nor** content safety certification, a signature, model authorization, owner creative acceptance or platform publishing permission. The operator assumes execution risk for that exact file; do not run untrusted source in a shared privileged environment. Future external providers require additional effect types and a real provider-specific approval/effect policy, not a generic arbitrary script loader.

The `ProductionExecutorRegistry` remains the only local effect operation registry; no new runtime controller, account adapter, task ledger or shadow scheduler. All deterministic operations are unchanged. Fixture positive execution explicitly supplies operator grant; negative cases test missing/wrong/digest-replaced grants and registry misclassification.

Referenced security guidance:
- OWASP AI Agent Security Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html
- OpenFeature Provider specification (interfaces vs provider implementation): https://openfeature.dev/specification/sections/providers/

## Exact execution bytes and TOCTOU protection
The execution worker now receives a per-attempt private snapshot of the exact granted Python source. The source is checked before copy and the snapshot rehashed against both the operator grant and immutable registered input digest before the worker is started. If the original source path changes after copying, the worker still sees the approved snapshot. This protects the authorized file identity against simple time-of-check/time-of-use replacement; it does **not** sandbox imports, file or network effects by authorized Python code. Self-contained renderer source is preferred; companion Python modules are not implicitly trusted source bytes.
