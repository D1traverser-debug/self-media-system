from __future__ import annotations

import ast
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import tempfile
import tomllib
from typing import Any

from .engine import StudioEngine
from .review_execution import ReviewExecutionTrustRegistry


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _check(checks: list[dict[str, Any]], check_id: str, passed: bool, detail: Any) -> None:
    checks.append({"id": check_id, "pass": bool(passed), "detail": detail})


def _authority_paths(root: Path, manifest_path: Path, manifest: dict[str, Any]) -> dict[str, str]:
    return {
        str((manifest_path.parent / item["path"]).resolve()): str(item["name"])
        for item in manifest.get("assets", [])
        if isinstance(item, dict) and isinstance(item.get("name"), str) and isinstance(item.get("path"), str)
    }


def _brand_violations(root: Path) -> list[str]:
    """Inspect active product identities; historical medium-specific evidence is not a product alias."""
    paths = [
        root / "pyproject.toml",
        root / "README.md",
        root / "STUDIO_ENTRY.md",
        root / ".github/workflows/ci.yml",
        root / "docs/standalone_social_media_studio.md",
        root / "docs/SOCIAL_MEDIA_STUDIO_ARCHITECTURE_V2.md",
    ]
    for folder in ("social_media_studio", "skills/social-media-studio"):
        directory = root / folder
        if directory.is_dir():
            paths.extend(p for p in directory.rglob("*")
                         if p.is_file() and p.suffix in {".py", ".json", ".md", ".yml", ".toml"})
    retired = (
        "video" + "_studio", "video" + "_growth_agent", "vga" + "-",
        "VGA" + "_", "VIDEO" + "_GROWTH_AGENT", "VIDEO" + "_REPOSITORY",
        "Video" + " Growth Agent", "Universal" + " Content Studio",
    )
    violations = []
    for candidate in paths:
        if not candidate.is_file():
            continue
        body = candidate.read_text(encoding="utf-8")
        for token in retired:
            if token in body:
                violations.append(f"{candidate.relative_to(root)}: retired identifier {token}")
    for old in ("video" + "_studio", "video" + "_growth_agent", "skills/video" + "-growth-agent"):
        if (root / old).exists():
            violations.append(f"retired top-level path remains: {old}")
    return sorted(set(violations))


def run_system_audit(repo_root: str | Path | None = None) -> dict[str, Any]:
    """Audit the standalone Social Media Studio contract without invoking CAOS or paid providers.

    This is a repository-level structural/readiness audit. It exercises the project
    engine in temporary directories and never mutates the repository or user workspace.
    A structural PASS does not mean any deliverable has been generated, reviewed or released.
    """
    root = Path(repo_root).expanduser().resolve() if repo_root else Path(__file__).resolve().parents[1]
    checks: list[dict[str, Any]] = []
    capability_gaps: list[str] = []
    owner_inputs_required: list[str] = []

    required_paths = [
        root / "STUDIO_ENTRY.md",
        root / "pyproject.toml",
        root / "social_media_studio" / "data" / "studio_manifest.json",
        root / "social_media_studio" / "data" / "subsystem_catalog.json",
        root / "social_media_studio" / "data" / "review_executors.json",
        root / "social_media_studio" / "scope.py",
        root / "social_media_studio" / "system_audit.py",
        root / "examples" / "technology-explainer.brief.json",
        root / "examples" / "technology-explainer.tasks.json",
        root / "examples" / "news-fictional-media.brief.json",
        root / "examples" / "news-fictional-media.tasks.json",
        root / "examples" / "ai-self-media-commercialization.brief.json",
        root / "examples" / "ai-self-media-commercialization.tasks.json",
        root / "examples" / "ai-self-media-commercialization.context.json",
        root / "examples" / "program-linked-episode.brief.json",
        root / "examples" / "program-linked-episode.tasks.json",
        root / "projects" / "ai-self-media-commercialization" / "BUSINESS_FLYWHEEL.json",
        root / "examples" / "standalone-domain-adapters.brief.json",
        root / "examples" / "standalone-domain-adapters.tasks.json",
    ]
    missing = [str(path.relative_to(root)) for path in required_paths if not path.is_file()]
    _check(checks, "required_repository_contract_files", not missing, {"missing": missing})
    if missing:
        return {
            "schema_version": "1.0",
            "audited_at": datetime.now(timezone.utc).isoformat(),
            "repository_root": str(root),
            "pass": False,
            "structural_status": "FAIL",
            "production_readiness": "BLOCKED",
            "checks": checks,
            "capability_gaps": [],
            "owner_inputs_required": [],
        }

    try:
        entry = (root / "STUDIO_ENTRY.md").read_text(encoding="utf-8")
        pyproject = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
        studio_manifest = _read_json(root / "social_media_studio" / "data" / "studio_manifest.json")
        review_registry_config = _read_json(root / "social_media_studio" / "data" / "review_executors.json")
        review_registry = ReviewExecutionTrustRegistry(config=review_registry_config)
        review_gate = studio_manifest.get("capabilities", {}).get("release_gates", {}).get("high_assurance_review", {})
        quality_contract = studio_manifest.get("architecture", {}).get("quality_contract", {})
        engine_source = (root / "social_media_studio" / "engine.py").read_text(encoding="utf-8")
        review_markers = (
            "self.review_trust_registry.verify(",
            "review_execution_nonces",
            "REVIEW_PACKET_BOUND",
            "_stage_review_inputs",
            "_verify_review_stage_inputs",
        )
        review_execution_integrated = all(marker in engine_source for marker in review_markers)
        review_contract_detection = StudioEngine._review_contract_requires_execution({
            "reviewer_kind": "HUMAN", "execution_mode": "INDEPENDENT_COLD_READ", "blind_review": True,
        })
        review_fail_closed = (
            not review_registry.config["trusted_executors"]
            and review_gate.get("default_trusted_executor_count") == 0
            and review_gate.get("empty_registry_behavior") == "BLOCK_HIGH_ASSURANCE_RELEASE"
            and review_gate.get("caller_supplied_attestation_is_proof") is False
            and quality_contract.get("high_assurance_review_proven") is False
            and quality_contract.get("production_executor_registered") is False
            and review_execution_integrated and review_contract_detection
        )
        _check(checks, "high_assurance_review_execution_default_fail_closed", review_fail_closed, {
            "trusted_executor_count": len(review_registry.config["trusted_executors"]),
            "empty_registry_behavior": review_gate.get("empty_registry_behavior"),
            "execution_verifier_integrated": review_execution_integrated,
            "high_assurance_contract_detected": review_contract_detection,
            "production_executor_registered": quality_contract.get("production_executor_registered"),
        })
        if not review_registry.config["trusted_executors"]:
            capability_gaps.append(
                "No production high-assurance review executor is registered. Rubrics requiring signed independent execution remain blocked until an executor, identity mapping, signing key and isolation mechanism are independently assessed."
            )
        program_brief = _read_json(root / "examples" / "ai-self-media-commercialization.brief.json")
        program_tasks = _read_json(root / "examples" / "ai-self-media-commercialization.tasks.json")
        episode_tasks = _read_json(root / "examples" / "program-linked-episode.tasks.json")
        context_path = root / "examples" / "ai-self-media-commercialization.context.json"
        context_manifest = _read_json(context_path)
        business_flywheel = _read_json(root / "projects" / "ai-self-media-commercialization" / "BUSINESS_FLYWHEEL.json")
    except (OSError, json.JSONDecodeError, tomllib.TOMLDecodeError, TypeError, KeyError) as exc:
        _check(checks, "repository_contract_parse", False, f"{type(exc).__name__}: {exc}")
        return {
            "schema_version": "1.0",
            "audited_at": datetime.now(timezone.utc).isoformat(),
            "repository_root": str(root),
            "pass": False,
            "structural_status": "FAIL",
            "production_readiness": "BLOCKED",
            "checks": checks,
            "capability_gaps": [],
            "owner_inputs_required": [],
        }

    governance = studio_manifest.get("governance", {})
    entry_ok = (
        "social_media_studio.engine.StudioEngine" in entry
        and "sms-studio" in entry
        and "sms-studio --root WORKSPACE intake REQUEST.json" in entry
        and "import-manifest" in entry
        and "system-audit" in entry
        and studio_manifest.get("system_audit") == "social_media_studio.system_audit.run_system_audit"
        and governance.get("system") == "CAOS"
        and governance.get("mode") == "CHAT_GOVERNED_EXTERNAL"
        and governance.get("session_governance_required") is True
        and governance.get("standalone_mode") == "OFFLINE_MECHANICAL_TESTS_ONLY"
        and governance.get("caos_runtime_dependency") is False
        and governance.get("caos_api_dependency") is False
        and governance.get("caos_skill_dependency") is False
        and governance.get("parent_task_or_lease_dependency") is False
        and governance.get("source_mutation") == "FORBIDDEN"
    )
    _check(checks, "caos_parent_governance_and_runtime_boundary", entry_ok, {
        "entry": "STUDIO_ENTRY.md",
        "runtime": studio_manifest.get("runtime"),
        "governance": governance,
    })

    brand_violations = _brand_violations(root)
    product_identity_ok = (
        studio_manifest.get("product_name") == "Social Media Studio"
        and studio_manifest.get("product_name_zh") == "自媒体系统"
        and studio_manifest.get("owner") == "SOCIAL_MEDIA_STUDIO"
        and studio_manifest.get("repository_slug") == "social-media-studio"
        and pyproject["project"]["name"] == "social-media-studio"
        and pyproject["project"]["scripts"] == {"sms-studio": "social_media_studio.cli:main"}
        and not brand_violations
    )
    _check(checks, "social_media_product_identity_no_active_legacy_aliases",
           product_identity_ok, {"violations": brand_violations})

    from .scope import EPOCH, resolve_intake, validate_workspace_mode
    index = _read_json(root / "projects" / "PROJECT_INDEX.json")
    admission = studio_manifest.get("task_admission", {})
    retired_ids = {item["project_id"] for item in index["projects"]}
    scope_epoch_ok = admission.get("scope_epoch") == EPOCH
    _check(checks, "owner_scope_epoch_matches_runtime", scope_epoch_ok, {
        "manifest_scope_epoch": admission.get("scope_epoch"),
        "runtime_scope_epoch": EPOCH,
    })
    task_neutral = (
        index.get("default_project_id") is None
        and admission.get("default_project_id") is None
        and admission.get("default_task_graph") is None
        and admission.get("automatic_resume") is False
        and set(admission.get("retired_project_ids", [])) == retired_ids
        and all(item["status"] == "RETIRED_EVIDENCE_ONLY" and not item["default_for_generic_domain_intent"] for item in index["projects"])
    )
    intake_failure = None
    with tempfile.TemporaryDirectory(prefix="sms-intake-") as scope_root:
        try:
            route = resolve_intake(scope_root, {"mode": "NEW", "goal": "Create a short original caption"})
            task_neutral = task_neutral and route["project_id"] is None and route["selected_task_graph"] is None
        except ValueError as exc:
            task_neutral = False
            intake_failure = f"{type(exc).__name__}: {exc}"
        if intake_failure is None:
            for retired_id in retired_ids:
                try:
                    resolve_intake(scope_root, {"mode": "RESUME", "project_id": retired_id})
                except ValueError:
                    continue
                task_neutral = False
    _check(checks, "task_neutral_intake_and_retirement", task_neutral, {
        "retired_project_ids": sorted(retired_ids),
        "intake_failure": intake_failure,
    })

    workspace_mode_failures: list[str] = []
    try:
        import shutil
        with tempfile.TemporaryDirectory(prefix="sms-workspace-mode-") as mode_root:
            base = Path(mode_root)
            owner_root = base / "owner"
            owner_root.mkdir()
            fixture_root = base / "fixture"
            validate_workspace_mode(
                fixture_root, offline_fixture=True, initialize=True, owner_root=owner_root,
            )
            try:
                validate_workspace_mode(fixture_root, offline_fixture=False, owner_root=owner_root)
            except ValueError:
                pass
            else:
                workspace_mode_failures.append("owner mode accepted a fixture-marked root")
            try:
                validate_workspace_mode(
                    owner_root, offline_fixture=True, initialize=True, owner_root=owner_root,
                )
            except ValueError:
                pass
            else:
                workspace_mode_failures.append("fixture mode accepted the default owner root")
            occupied_root = base / "occupied"
            occupied_root.mkdir()
            (occupied_root / "projects").mkdir()
            try:
                validate_workspace_mode(
                    occupied_root, offline_fixture=True, initialize=True, owner_root=owner_root,
                )
            except ValueError:
                pass
            else:
                workspace_mode_failures.append("fixture mode adopted a pre-existing unmarked workspace")
            copied_root = base / "copied"
            copied_root.mkdir()
            shutil.copy2(
                fixture_root / ".sms-offline-fixture.json",
                copied_root / ".sms-offline-fixture.json",
            )
            try:
                validate_workspace_mode(copied_root, offline_fixture=True, owner_root=owner_root)
            except ValueError:
                pass
            else:
                workspace_mode_failures.append("fixture marker was accepted at a different root")
    except (OSError, ValueError, TypeError) as exc:
        workspace_mode_failures.append(f"{type(exc).__name__}: {exc}")
    _check(checks, "owner_and_fixture_workspace_modes_are_isolated",
           not workspace_mode_failures, workspace_mode_failures)
    from .scope import knowledge_lookup
    try:
        methods = knowledge_lookup(include_nonactive=True, repo_root=root)
        _check(checks, "knowledge_locator_integrity", True, {"source_count": len(methods["entries"])})
    except (ValueError, OSError, KeyError, TypeError) as exc:
        _check(checks, "knowledge_locator_integrity", False, str(exc))
    learning_policy = studio_manifest.get("learning_policy", {})
    knowledge_lifecycle = studio_manifest.get("knowledge_lifecycle", {})
    adapter_execution = studio_manifest.get("capabilities", {}).get("domain_adapter_execution", {})
    minimum_counterexamples = learning_policy.get("minimum_counterexample_trials")
    promotion_contract_ok = (
        learning_policy.get("default_status") == "CANDIDATE"
        and learning_policy.get("requires_evidence") is True
        and learning_policy.get("requires_counterexamples") is True
        and learning_policy.get("requires_failure_conditions") is True
        and learning_policy.get("requires_independent_replay_for_validation") is True
        and learning_policy.get("minimum_independent_replays") == 2
        and isinstance(minimum_counterexamples, int)
        and not isinstance(minimum_counterexamples, bool)
        and minimum_counterexamples >= 1
        and learning_policy.get("requires_real_case") is True
        and learning_policy.get("requires_cross_task_transfer") is True
        and learning_policy.get("requires_regression_test") is True
        and learning_policy.get("requires_rollback") is True
        and learning_policy.get("requires_owner_burden_cost_or_na") is True
        and learning_policy.get("requires_independent_readback") is True
        and learning_policy.get("requires_caos_owner_acceptance") is True
        and learning_policy.get("project_candidate_promotion_authorized") is False
        and adapter_execution.get("candidate_promotion_authorized") is False
        and knowledge_lifecycle.get("active_statuses") == ["ACTIVE_REFERENCE", "VERIFIED_OPERATION"]
        and knowledge_lifecycle.get("candidate_status") == "CANDIDATE_REQUIRES_REVALIDATION"
        and knowledge_lifecycle.get("retired_status") == "RETIRED_EVIDENCE_ONLY"
        and learning_policy.get("global_knowledge_promotion")
        == "VERSIONED_REPOSITORY_CHANGE_AFTER_EVIDENCE_INDEPENDENT_REPLAY_AND_CAOS_ACCEPTANCE"
        and knowledge_lifecycle.get("mutation_authority")
        == "SOCIAL_MEDIA_STUDIO_REPOSITORY_VERSIONED_CHANGE_WITH_EVIDENCE_AND_INDEPENDENT_REPLAY"
    )
    _check(checks, "knowledge_promotion_is_scoped_and_fail_closed", promotion_contract_ok, {
        "default_project_status": learning_policy.get("default_status"),
        "minimum_independent_replays": learning_policy.get("minimum_independent_replays"),
        "minimum_counterexample_trials": learning_policy.get("minimum_counterexample_trials"),
        "cross_task_transfer_required": learning_policy.get("requires_cross_task_transfer"),
        "automatic_project_promotion": learning_policy.get("project_candidate_promotion_authorized"),
        "mutation_authority": knowledge_lifecycle.get("mutation_authority"),
    })
    from .scope import capability_lookup
    try:
        coverage = capability_lookup(profile=_read_json(root / "social_media_studio" / "legacy" / "data" / "capabilities.json"))
        _check(checks, "professional_capability_route_integrity", True, {
            "groups": len(coverage["groups"]),
            "registry_alignment": coverage["registry_alignment"],
            "business_outcome_verified": False,
        })
        capability_gaps.extend(f"{group['id']}: {gap}" for group in coverage["groups"] for gap in group["gaps"])
    except (ValueError, KeyError, TypeError, OSError) as exc:
        _check(checks, "professional_capability_route_integrity", False, str(exc))
    # Design coverage cannot certify actual craft or native CAOS, but missing
    # positive/negative oracles must fail before a contract is promoted.
    from .domain.contracts import DELIVERABLE_TYPES, inspect_declared_deliverables
    matrix_failures = []
    try:
        matrix = _read_json(root / "docs" / "SOCIAL_MEDIA_STUDIO_ARCH_ACCEPTANCE_V2.json")
        groups = {x["id"] for x in _read_json(
            root / "social_media_studio" / "legacy" / "data" / "capabilities.json"
        )["professional_capability_groups"]}
        seen = set()
        for case in matrix.get("scenarios", []):
            case_id = case.get("id")
            kind = case.get("deliverable_type")
            if case_id in seen or not isinstance(case_id, str) or not case_id:
                matrix_failures.append(f"{case_id}:duplicate_or_missing_identity")
            seen.add(case_id)
            if kind not in DELIVERABLE_TYPES:
                matrix_failures.append(f"{case_id}:unknown_deliverable")
                continue
            if not isinstance(case.get("owner_outcome_oracle"), str) or not case["owner_outcome_oracle"].strip():
                matrix_failures.append(f"{case_id}:missing_positive_oracle")
            if not isinstance(case.get("forbidden_implicit_effect"), str) or not case["forbidden_implicit_effect"].strip():
                matrix_failures.append(f"{case_id}:missing_negative_oracle")
            if any(item not in groups for item in case.get("required_contexts", [])):
                matrix_failures.append(f"{case_id}:unregistered_context")
            item = {"id": "candidate", "type": kind}
            if kind == "MULTI_ASPECT_IMAGE_SET":
                item["variants"] = [
                    {"id": "portrait", "shape": {"width": 1080, "height": 1440, "orientation": "PORTRAIT"}},
                    {"id": "landscape", "shape": {"width": 1440, "height": 1080, "orientation": "LANDSCAPE"}},
                ]
            preview = inspect_declared_deliverables([item])
            if preview["effect_authorized"] or preview["quality_verified"] or preview["selected_task_graph"] is not None:
                matrix_failures.append(f"{case_id}:false_effect_or_quality_assurance")
        if len(seen) < 28:
            matrix_failures.append("scenario_coverage_regressed")
    except (ValueError, TypeError, KeyError, OSError) as exc:
        matrix_failures.append(f"source_or_contract_error:{exc}")
    _check(checks, "typed_deliverables_and_architecture_negative_oracles", not matrix_failures,
           {"scenario_count": len(seen) if "seen" in locals() else 0,
            "failure_refs": matrix_failures, "verification": "STRUCTURE_ONLY_NOT_BUSINESS_OUTCOME"})
    from .subsystems import audit_subsystems
    try:
        topology = audit_subsystems(root)
        _check(checks, "all_internal_subsystems_owned_and_no_legacy_control_reentry",
               topology["pass"],
               {key: topology[key] for key in ("tracked_files","code_modules","owned_modules",
                  "subsystems","domain_adapters","production_operations","topology_contract",
                  "unclassified_paths","violations","assurance")})
    except (ValueError, OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        _check(checks, "all_internal_subsystems_owned_and_no_legacy_control_reentry", False,
               f"{type(exc).__name__}: {exc}")
    scripts = pyproject.get("project", {}).get("scripts", {})
    cli_source = (root / "social_media_studio" / "cli.py").read_text(encoding="utf-8")
    cli_registered = (
        scripts.get("sms-studio") == "social_media_studio.cli:main"
        and "system-audit" in cli_source and "import-manifest" in cli_source
        and "transfer-asset" in cli_source and hasattr(StudioEngine, "transfer_artifact")
    )
    _check(checks, "standalone_cli_registration", cli_registered, scripts)

    import_failures: list[str] = []
    scanned_files = sorted((root / "social_media_studio").rglob("*.py"))
    for path in scanned_files:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, SyntaxError) as exc:
            import_failures.append(f"{path.relative_to(root)}: {type(exc).__name__}: {exc}")
            continue
        for node in ast.walk(tree):
            modules: list[str] = []
            if isinstance(node, ast.Import):
                modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules.append(node.module)
            for module in modules:
                if module == "caos" or module.startswith("caos.") or module.startswith("cognition_agent_os"):
                    import_failures.append(f"{path.relative_to(root)} imports {module}")
                if module == "social_media_studio.legacy" or module.startswith("social_media_studio.legacy."):
                    if path.name != "adapters.py":
                        import_failures.append(f"{path.relative_to(root)} imports legacy domain code outside the explicit adapter bridge: {module}")
    _check(checks, "runtime_dependency_boundary", not import_failures, import_failures)

    adapter_source = (root / "social_media_studio" / "adapters.py").read_text(encoding="utf-8")
    implemented_adapters = set(re.findall(r"""(?:if|elif) name == ["']([^"']+)["']""", adapter_source))
    declared_adapters = set(studio_manifest.get("capabilities", {}).get("domain_adapters", {}))
    from .adapters import SUPPORTED_DOMAIN_ADAPTERS, supports_domain_adapter
    supported_adapters = set(SUPPORTED_DOMAIN_ADAPTERS)
    adapter_registry_ok = declared_adapters == implemented_adapters == supported_adapters
    _check(checks, "domain_adapter_registry_matches_manifest", adapter_registry_ok, {
        "declared_count": len(declared_adapters),
        "implemented_count": len(implemented_adapters),
        "supported_count": len(supported_adapters),
        "undeclared_supported": sorted(supported_adapters - declared_adapters),
        "declared_without_implementation": sorted(declared_adapters - implemented_adapters),
        "implemented_without_support_registration": sorted(implemented_adapters - supported_adapters),
    })

    from .production.executors import tool_executor_for_task

    tool_binding_failures = []
    for task in program_tasks:
        if task.get("executor") != "tool":
            continue
        requirements = task.get("requirements", {})
        adapter = requirements.get("domain_adapter") if isinstance(requirements, dict) else None
        if isinstance(adapter, dict):
            name = str(adapter.get("name") or "").strip()
            if not name or name not in declared_adapters or not supports_domain_adapter(name):
                tool_binding_failures.append(f"{task.get('task_id')}: domain adapter is not declared and executable: {name!r}")
        elif not tool_executor_for_task(task):
            tool_binding_failures.append(f"{task.get('task_id')}: no registered production/domain executor")
    _check(checks, "program_tool_tasks_have_registered_executors", not tool_binding_failures, tool_binding_failures)

    all_example_tool_failures = []
    all_example_tool_count = 0
    for task_path in sorted((root / "examples").glob("*.tasks.json")):
        for task in _read_json(task_path):
            if task.get("executor") != "tool":
                continue
            all_example_tool_count += 1
            executor_ref = tool_executor_for_task(task)
            if not executor_ref:
                all_example_tool_failures.append(
                    f"{task_path.name}:{task.get('task_id')}: no registered executor"
                )
                continue
            requirements = task.get("requirements", {})
            adapter = requirements.get("domain_adapter") if isinstance(requirements, dict) else None
            if isinstance(adapter, dict):
                name = str(adapter.get("name") or "").strip()
                if name not in declared_adapters or not supports_domain_adapter(name):
                    all_example_tool_failures.append(
                        f"{task_path.name}:{task.get('task_id')}: undeclared domain adapter {name!r}"
                    )
    _check(checks, "all_example_tool_tasks_have_registered_executors", not all_example_tool_failures, {
        "example_task_graph_count": len(list((root / "examples").glob("*.tasks.json"))),
        "tool_task_count": all_example_tool_count,
        "failures": all_example_tool_failures,
    })

    task_ids = {str(task.get("task_id")) for task in program_tasks}
    output_producers = {
        output: str(task.get("task_id"))
        for task in program_tasks
        for output in task.get("outputs", [])
    }
    flywheel_failures = []
    for loop_name, loop in business_flywheel.get("execution_bindings", {}).items():
        loop_task_ids = set(loop.get("task_ids", []))
        for task_id in sorted(loop_task_ids - task_ids):
            flywheel_failures.append(f"{loop_name}: unknown task {task_id}")
        for artifact_name in loop.get("handoff_artifacts", []):
            producer = output_producers.get(artifact_name)
            if producer is None:
                flywheel_failures.append(f"{loop_name}: handoff artifact has no producer: {artifact_name}")
            elif producer not in loop_task_ids:
                flywheel_failures.append(f"{loop_name}: producer {producer} for {artifact_name} is not in the loop task set")
    _check(checks, "cross_workstream_flywheel_handoffs_resolve", not flywheel_failures, flywheel_failures)

    program_handoff_validator = next(
        (task for task in program_tasks if task.get("task_id") == "validate-episode-production-handoff"), {}
    )
    episode_handoff_validator = next(
        (task for task in episode_tasks if task.get("task_id") == "validate-program-handoff"), {}
    )
    program_handoff_outputs = set(program_handoff_validator.get("outputs", []))
    episode_handoff_inputs = set(episode_handoff_validator.get("inputs", []))
    source_artifact_inputs = set(
        program_handoff_validator.get("requirements", {}).get("domain_adapter", {}).get("source_artifact_inputs", [])
    )
    expected_source_artifact_inputs = {
        "portfolio-allocation-decision", "pilot-topic-slate-decision",
        "production-strategy", "commercial-production-constraints", "growth-baseline",
    }
    cross_project_handoff_failures = []
    if program_handoff_outputs != {"validated-episode-intent"}:
        cross_project_handoff_failures.append(f"Program validator must emit validated-episode-intent: {sorted(program_handoff_outputs)}")
    if episode_handoff_inputs != program_handoff_outputs:
        cross_project_handoff_failures.append(
            f"Episode input names must exactly match Program output names: {sorted(episode_handoff_inputs)} != {sorted(program_handoff_outputs)}"
        )
    if source_artifact_inputs != expected_source_artifact_inputs:
        cross_project_handoff_failures.append(f"Program source artifact binding set is incomplete: {sorted(source_artifact_inputs)}")
    episode_adapter = episode_handoff_validator.get("requirements", {}).get("domain_adapter", {})
    if episode_adapter.get("require_validated_transfer") is not True:
        cross_project_handoff_failures.append("Episode validator must require immutable validated cross-project transfer metadata")
    if episode_adapter.get("handoff_input") != "validated-episode-intent":
        cross_project_handoff_failures.append("Episode validator input binding does not match the canonical Program handoff")
    _check(checks, "cross_project_program_episode_handoff_contract", not cross_project_handoff_failures, {
        "program_outputs": sorted(program_handoff_outputs),
        "episode_inputs": sorted(episode_handoff_inputs),
        "source_artifact_inputs": sorted(source_artifact_inputs),
        "failures": cross_project_handoff_failures,
    })

    from .production.registry import PRODUCTION_EXECUTORS

    local_operations = set(PRODUCTION_EXECUTORS.operations())
    # The registered subsystem topology is the single declared operation authority.
    # Do not maintain a second stale hand-written executor allowlist here.
    topology_catalog = _read_json(root / "social_media_studio" / "data" / "subsystem_catalog.json")
    expected_operations = {
        operation for subsystem in topology_catalog["subsystems"]
        for operation in subsystem.get("production_operations", [])
    }
    _check(checks, "local_production_executor_registry", local_operations == expected_operations, {
        "registered": sorted(local_operations),
        "expected": sorted(expected_operations),
    })

    names_by_path = _authority_paths(root, context_path, context_manifest)
    authority_failures: list[str] = []
    for key, reference in program_brief.get("program_context", {}).items():
        if key.endswith("_ref") and isinstance(reference, str) and reference.startswith(("projects/", "docs/")):
            if str((root / reference).resolve()) not in names_by_path:
                authority_failures.append(f"brief.program_context.{key} is not imported: {reference}")
    for task in program_tasks:
        requirements = task.get("requirements", {})
        refs = list(requirements.get("authority_refs", []))
        if requirements.get("authority_ref"):
            refs.append(requirements["authority_ref"])
        for reference in refs:
            resolved = str((root / reference).resolve())
            asset_name = names_by_path.get(resolved)
            if asset_name is None:
                authority_failures.append(f"{task.get('task_id')} authority ref is absent from context manifest: {reference}")
            elif asset_name not in task.get("inputs", []):
                authority_failures.append(f"{task.get('task_id')} does not bind {reference} as input {asset_name}")
    _check(checks, "program_authority_refs_are_digest_bound_inputs", not authority_failures, authority_failures)

    graph_failures: list[str] = []
    with tempfile.TemporaryDirectory(prefix="sms-standalone-audit-") as temp_root:
        for project_id, brief_name, tasks_name in (
            ("explainer", "technology-explainer.brief.json", "technology-explainer.tasks.json"),
            ("satire", "news-fictional-media.brief.json", "news-fictional-media.tasks.json"),
            ("adapter-demo", "standalone-domain-adapters.brief.json", "standalone-domain-adapters.tasks.json"),
            ("program-linked-episode", "program-linked-episode.brief.json", "program-linked-episode.tasks.json"),
        ):
            try:
                engine = StudioEngine(Path(temp_root) / project_id)
                brief = _read_json(root / "examples" / brief_name)
                tasks = _read_json(root / "examples" / tasks_name)
                engine.create_project(project_id, project_id, brief)
                engine.add_tasks(project_id, tasks)
                audit = engine.audit(project_id)
                if audit.get("pass") is not True:
                    graph_failures.append(f"{project_id}: {audit}")
                if project_id == "program-linked-episode":
                    task_map = {item["task_id"]: item for item in engine.list_tasks(project_id)}
                    if task_map.get("validate-program-handoff", {}).get("status") != "WAITING_INPUT":
                        graph_failures.append("program-linked-episode must fail closed until the validated Program handoff artifact is imported")
            except Exception as exc:
                graph_failures.append(f"{project_id}: {type(exc).__name__}: {exc}")
        try:
            engine = StudioEngine(Path(temp_root) / "program")
            engine.create_project("program", "Integrated media program", program_brief)
            for asset in context_manifest.get("assets", []):
                source = (context_path.parent / asset["path"]).resolve(strict=True)
                engine.import_asset(
                    "program", asset["name"], source,
                    kind=asset["kind"], media_type=asset["media_type"],
                    rights_status=asset["rights_status"], metadata=asset.get("metadata", {}),
                )
            engine.add_tasks("program", program_tasks)
            program_audit = engine.audit("program")
            task_map = {item["task_id"]: item for item in engine.list_tasks("program")}
            expected_ready = {
                "growth-baseline-and-topic-hypotheses",
                "commercial-advertiser-map",
                "production-economics-baseline",
                "provider-capability-benchmark",
                "media-graph-bootstrap",
                "jensen-case-fact-audit",
            }
            for task_id in sorted(expected_ready):
                if task_map.get(task_id, {}).get("status") != "READY":
                    graph_failures.append(f"program task should be READY: {task_id} -> {task_map.get(task_id, {}).get('status')}")
            for task_id in ("jensen-source-media-inspection", "jensen-rights-identity-audit"):
                if task_map.get(task_id, {}).get("status") != "WAITING_INPUT":
                    graph_failures.append(f"owner-media task should WAIT_INPUT: {task_id} -> {task_map.get(task_id, {}).get('status')}")
            if task_map.get("ipos-video-identity-bundle-import", {}).get("status") != "PENDING":
                graph_failures.append("IPOS import must remain dependency-pending until MediaGraph bootstrap is completed")
            if program_audit.get("pass") is not True:
                graph_failures.append(f"program graph audit failed: {program_audit}")
            from .production.worker_pool import run_ready_tool_tasks
            tool_smoke = run_ready_tool_tasks(engine, "program", worker_prefix="system-audit", max_workers=2, max_rounds=10)
            completed_tool_ids = {item["task_id"] for item in tool_smoke.get("completed", [])}
            if "media-graph-bootstrap" not in completed_tool_ids:
                graph_failures.append(f"Program local tool smoke did not execute media-graph-bootstrap: {tool_smoke}")
            if tool_smoke.get("failed") or tool_smoke.get("ready_tool_tasks_without_registered_executor"):
                graph_failures.append(f"Program local tool smoke found execution failures or unregistered tools: {tool_smoke}")
            post_smoke_tasks = {item["task_id"]: item for item in engine.list_tasks("program")}
            if post_smoke_tasks.get("media-graph-bootstrap", {}).get("status") != "COMPLETED":
                graph_failures.append("media-graph-bootstrap must complete through the registered local tool executor")
            if post_smoke_tasks.get("ipos-video-identity-bundle-import", {}).get("status") != "WAITING_INPUT":
                graph_failures.append("IPOS import must wait for the missing owner-approved bundle after MediaGraph bootstrap")
            if engine.audit("program").get("pass") is not True:
                graph_failures.append("Program graph audit failed after the real local tool execution smoke")
        except Exception as exc:
            graph_failures.append(f"program: {type(exc).__name__}: {exc}")
    _check(checks, "isolated_regression_graphs_and_local_execution", not graph_failures, graph_failures)

    explainer_brief = _read_json(root / "examples" / "technology-explainer.brief.json")
    satire_brief = _read_json(root / "examples" / "news-fictional-media.brief.json")
    hard_gate_failures = []
    for name, brief in (("technology-explainer", explainer_brief), ("news-fictional-media", satire_brief)):
        policy = brief.get("release_policy", {})
        if policy.get("require_rights") is not True or policy.get("require_rights_evidence") is not True:
            hard_gate_failures.append(f"{name}: rights and evidence must be required")
        if policy.get("no_auto_publish") is not True:
            hard_gate_failures.append(f"{name}: no_auto_publish must be true")
    red_team = explainer_brief.get("release_policy", {}).get("review_contracts", {}).get("red-team", {})
    if int(red_team.get("min_findings", 0)) < 3:
        hard_gate_failures.append("technology-explainer: Red Team must require at least three findings")
    # These are the *historical explainer/satire* video fixture policies,
    # not compulsory release gates for an X article, caption or static image.
    _check(checks, "isolated_historical_video_fixture_release_policy", not hard_gate_failures, {
        "scope": "HISTORICAL_VIDEO_FIXTURES_ONLY",
        "source_examples": ["technology-explainer", "news-fictional-media"],
        "failures": hard_gate_failures,
        "universal_content_gate": False,
    })

    provider_state = (
        studio_manifest.get("capabilities", {})
        .get("domain_adapter_execution", {})
        .get("external_provider_generation", "UNSPECIFIED")
    )
    if str(provider_state).startswith("NOT_CONNECTED"):
        capability_gaps.append(
            "No repository-registered generative-video executor. Agent tasks may use a currently available session tool only after operation, availability, rights and cost checks; paid generation requires explicit owner approval."
        )
    # Missing inputs are demand-specific; isolated fixtures cannot create owner obligations.
    owner_inputs_required = sorted(set(owner_inputs_required))

    failed_checks = [item for item in checks if not item["pass"]]
    return {
        "schema_version": "1.0",
        "audited_at": datetime.now(timezone.utc).isoformat(),
        "repository_root": str(root),
        "pass": not failed_checks,
        "structural_status": "PASS" if not failed_checks else "FAIL",
        "production_readiness": "PARTIAL" if capability_gaps or owner_inputs_required else "READY",
        "checks": checks,
        "capability_gaps": capability_gaps,
        "owner_inputs_required": owner_inputs_required,
        "boundary": {
            "caos_session_governance_required": True,
            "caos_runtime_dependency": False,
            "caos_source_mutation_allowed": False,
            "paid_provider_calls_made": False,
            "automatic_publication": False,
            "temporary_workspace_only": True,
        },
    }
