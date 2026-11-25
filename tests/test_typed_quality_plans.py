import json
from pathlib import Path
from social_media_studio.domain.assurance import CRITERIA, build_quality_plan
from social_media_studio.domain.contracts import MediaShape

ROOT=Path(__file__).resolve().parents[1]

def test_34_scenarios_have_type_specific_no_pass_plans():
    matrix=json.loads((ROOT/"docs/SOCIAL_MEDIA_STUDIO_ARCH_ACCEPTANCE_V2.json").read_text())
    assert len(matrix["scenarios"]) >= 34
    for case in matrix["scenarios"]:
        obj={"id":case["id"],"type":case["deliverable_type"],
             "acceptance":{"target":case["owner_outcome_oracle"]},
             "prohibitions":[case["forbidden_implicit_effect"]]}
        if obj["type"]=="MULTI_ASPECT_IMAGE_SET":
            shapes=case.get("requested_shapes") or [
                {"width":1080,"height":1440,"orientation":"PORTRAIT"},
                {"width":1440,"height":1080,"orientation":"LANDSCAPE"}]
            obj["variants"]=[{"id":f"variant-{i}","shape":shape} for i,shape in enumerate(shapes)]
        elif case.get("requested_ratio"):
            obj["shape"]=MediaShape.from_ratio(
                case["requested_ratio"],ratio_order=case["ratio_convention"],
                long_edge_pixels=case["long_edge_pixels"]).as_dict()
        elif case.get("canonical_shape"):
            obj["shape"]=case["canonical_shape"]
        result=build_quality_plan([obj])
        plan=result["plans"][0]
        assert plan["type"]==obj["type"]
        assert plan["owner_acceptance"]["target"]==case["owner_outcome_oracle"]
        assert plan["criteria"] and plan["quality_verified"] is False
        assert plan["owner_outcome_verified"] is False
        assert result["release_authorized"] is False
        if case.get("canonical_shape"):
            assert plan["shape"]["width"] == case["canonical_shape"]["width"]
            assert plan["shape"]["height"] == case["canonical_shape"]["height"]
            assert plan["shape"]["orientation"] == case["canonical_shape"]["orientation"]
        if case.get("requested_shapes"):
            assert [v["shape"]["orientation"] for v in plan["per_variant_review"]] == [
                shape["orientation"] for shape in case["requested_shapes"]
            ]
            assert all(v["shape"]["ratio_order"] == "WIDTH:HEIGHT" for v in plan["per_variant_review"])

def test_caption_and_article_have_no_fixed_video_stage():
    for kind in ["SHORT_COPY","LONG_ARTICLE","PROMPT_SPEC"]:
        p=build_quality_plan([{"id":"one","type":kind}])["plans"][0]
        assert "full_playback" not in p["criteria"]
        assert "lookdev" not in p["criteria"]
    assert "natural_language" in CRITERIA["SHORT_COPY"]

def test_multi_aspect_reviews_each_ratio_and_ipos_requires_actual_approval():
    covers=build_quality_plan([{"id":"two","type":"MULTI_ASPECT_IMAGE_SET",
        "variants":[{"id":"vertical","shape":{"width":1080,"height":1440,"orientation":"PORTRAIT"}},
                    {"id":"horizontal","shape":{"width":1440,"height":1080,"orientation":"LANDSCAPE"}}]}])["plans"][0]
    assert [x["id"] for x in covers["per_variant_review"]]==["vertical","horizontal"]
    assert all(x["pixels_reviewed"] is False for x in covers["per_variant_review"])
    identity=build_quality_plan([{"id":"avatar","type":"IDENTITY_ASSET",
          "constraints":{"identity_mode":"PERSISTENT_IDENTITY_DESIGN"}}])["plans"][0]
    assert identity["owner_approved_ipos_canon_verified"] is False
    transform=build_quality_plan([{"id":"clip","type":"MEDIA_TRANSFORM",
          "constraints":{"original_audio_promise":"BITSTREAM_IDENTITY"}}])["plans"][0]
    assert transform["audio_promise"]=="BITSTREAM_IDENTITY"
    assert transform["audio_identity_verified"] is False


def test_quality_plan_preserves_user_facing_shape_platform_locale_sources_and_prohibitions():
    plan=build_quality_plan([{
        "id":"portrait-cover","type":"STATIC_IMAGE","locale":"zh-CN","platform":"TIKTOK",
        "shape":{"width":1080,"height":1440,"orientation":"PORTRAIT"},
        "source_refs":["source-cover"],"prohibitions":["no collage","no title panel"],
        "acceptance":{"target":"one portrait cover, readable on mobile"},
    }])["plans"][0]
    assert plan["shape"]["width"]==1080 and plan["shape"]["height"]==1440
    assert plan["shape"]["orientation"]=="PORTRAIT"
    assert plan["shape"]["ratio_order"]=="WIDTH:HEIGHT"
    assert plan["locale"]=="zh-CN" and plan["platform"]=="TIKTOK"
    assert plan["source_refs"]==["source-cover"]
    assert plan["prohibitions"]==["no collage","no title panel"]
    assert plan["owner_acceptance_status"]=="DECLARED"
    assert plan["blocking_gaps"]==[]


def test_missing_owner_acceptance_is_explicitly_blocking_not_silently_complete():
    plan=build_quality_plan([{"id":"caption","type":"SHORT_COPY"}])["plans"][0]
    assert plan["owner_acceptance_status"]=="MISSING"
    assert "OWNER_ACCEPTANCE_NOT_DECLARED" in plan["blocking_gaps"]
    assert plan["quality_verified"] is False


def test_static_image_quality_does_not_inherit_motion_or_video_requirements():
    criteria=set(CRITERIA["STATIC_IMAGE"])
    assert "full_playback" not in criteria
    assert "motion_craft" not in criteria
    assert "audio_promise" not in criteria
    assert "mobile_thumbnail" in criteria


def test_active_quality_references_are_conditional_not_universal():
    root=Path(__file__).resolve().parents[1]
    knowledge=json.loads((root/"social_media_studio/data/knowledge_catalog.json").read_text())
    scopes={item["id"]:item["scope"] for item in knowledge["entries"]}
    assert "never apply by default" in scopes["quality-gates"]
    assert "never a default gate" in scopes["quality-rubric"]
    rubric=json.loads((root/"social_media_studio/legacy/data/quality-rubric.json").read_text())
    assert "MOTION_PRODUCTION_ONLY" in rubric["scope"]
    assert all(stage["applies_to"]==["ORIGINAL_VIDEO"] for stage in rubric["stages"].values())
    gates=(root/"skills/social-media-studio/references/quality-gates.md").read_text()
    assert "Static images do not require camera motion" in gates
    assert "Do **not** impose three hero frames" in gates


def test_multi_aspect_quality_plan_preserves_each_variant_platform_and_locale():
    plan=build_quality_plan([{
        "id":"platform-covers","type":"MULTI_ASPECT_IMAGE_SET",
        "variants":[
            {"id":"tiktok-portrait","locale":"zh-CN","platform":"TIKTOK",
             "shape":{"width":1080,"height":1440,"orientation":"PORTRAIT"}},
            {"id":"x-landscape","locale":"en-US","platform":"X",
             "shape":{"width":1440,"height":1080,"orientation":"LANDSCAPE"}},
        ],
        "acceptance":{"target":"same concept, platform-specific composition"},
    }])["plans"][0]
    assert [(v["id"],v["locale"],v["platform"]) for v in plan["per_variant_review"]]==[
        ("tiktok-portrait","zh-CN","TIKTOK"),
        ("x-landscape","en-US","X"),
    ]
    assert [(v["shape"]["width"],v["shape"]["height"]) for v in plan["per_variant_review"]]==[
        (1080,1440),(1440,1080)
    ]


def test_social_media_skill_requires_user_outcome_fidelity_before_effect_and_delivery():
    root=Path(__file__).resolve().parents[1]
    skill=(root/"skills/social-media-studio/SKILL.md").read_text()
    assert "Outcome-fidelity gate" in skill
    assert "Preserve every user correction as a current constraint" in skill
    assert "Do not substitute a nearby capability" in skill
    assert "inspect the actual result" in skill
    assert "never silently downgrade the requirement" in skill
