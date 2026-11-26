from __future__ import annotations

import json
from pathlib import Path

from social_media_studio.adapters import (
    DomainAdapterError,
    SUPPORTED_DOMAIN_ADAPTERS,
    run_claimed_domain_adapter,
    supports_domain_adapter,
)
from social_media_studio.domain_adapters.registry import (
    DOMAIN_ADAPTERS,
    public_domain_adapter_registry,
)
from social_media_studio.scope import capability_lookup


ROOT = Path(__file__).resolve().parents[1]


def test_one_typed_registry_binds_all_17_domain_adapter_handlers_and_manifest_refs():
    manifest = json.loads((ROOT / "social_media_studio/data/studio_manifest.json").read_text(encoding="utf-8"))
    declared = manifest["capabilities"]["domain_adapters"]
    assert set(DOMAIN_ADAPTERS) == set(SUPPORTED_DOMAIN_ADAPTERS) == set(declared)
    for name, spec in DOMAIN_ADAPTERS.items():
        assert spec.name == name
        assert callable(spec.handler)
        assert declared[name] == spec.handler_ref
        assert spec.handler_ref == f"{spec.handler.__module__}.{spec.handler.__name__}"
        assert spec.external_effects is False
        assert spec.promotes_candidate is False
        assert spec.publishes is False
        assert spec.effect_scope.startswith("PROJECT_LOCAL")
        assert spec.capability_group
        assert spec.output_contract
        assert spec.assurance_ceiling
        assert spec.known_gap
        assert supports_domain_adapter(name)
    assert not supports_domain_adapter("unregistered_external_video_generator")
    assert len(DOMAIN_ADAPTERS) == 17


def test_capability_lookup_exposes_operation_limits_without_claiming_provider_access():
    profile = capability_lookup()
    operations = profile["domain_operations"]
    assert len(operations) == 17
    assert {item["name"] for item in operations} == set(DOMAIN_ADAPTERS)
    assert all(item["handler_registered"] is True for item in operations)
    assert all(item["external_effects"] is False for item in operations)
    assert all(item["promotes_candidate"] is False for item in operations)
    assert all(item["publishes"] is False for item in operations)
    assert profile["effect_authorized"] is False
    assert profile["business_outcome_verified"] is False
    assert profile["native_activation"] == "NOT_VERIFIED_BY_RUNTIME"


def test_group_filtered_capability_lookup_returns_only_the_selected_group_operations():
    all_profile = capability_lookup()
    group = all_profile["groups"][0]
    filtered = capability_lookup(group["id"])
    assert [item["id"] for item in filtered["groups"]] == [group["id"]]
    assert {item["name"] for item in filtered["domain_operations"]} == set(group["adapters"])


def test_adapters_module_is_a_compatibility_facade_not_a_second_dispatcher():
    source = (ROOT / "social_media_studio/adapters.py").read_text(encoding="utf-8")
    assert "if name ==" not in source
    assert "from .domain_adapters.dispatch import run_claimed_domain_adapter" in source
    assert run_claimed_domain_adapter.__module__ == "social_media_studio.domain_adapters.dispatch"
    assert DomainAdapterError.__module__ == "social_media_studio.domain_adapters.common"


def test_registry_metadata_does_not_upgrade_structural_tools_into_quality_or_release_oracles():
    registry = {item["name"]: item for item in public_domain_adapter_registry()}
    assert registry["extended_media_qa"]["assurance_ceiling"] == "TECHNICAL_MEASUREMENT_NOT_AESTHETIC"
    assert registry["shot_route"]["assurance_ceiling"] == "DECISION_SUPPORT_NOT_PROVIDER_EXECUTION"
    assert registry["business_outcome_metrics"]["assurance_ceiling"] == "DERIVED_METRICS_NOT_CAUSAL_GROWTH"
    assert registry["programmatic_graphic_render"]["assurance_ceiling"] == "CANDIDATE_RENDER_NOT_PROMOTION_OR_RELEASE"
