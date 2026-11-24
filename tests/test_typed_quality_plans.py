import json
from pathlib import Path
from video_studio.domain.assurance import CRITERIA, build_quality_plan

ROOT=Path(__file__).resolve().parents[1]

def test_34_scenarios_have_type_specific_no_pass_plans():
    matrix=json.loads((ROOT/"docs/CONTENT_STUDIO_ARCH_ACCEPTANCE_V2.json").read_text())
    assert len(matrix["scenarios"]) >= 34
    for case in matrix["scenarios"]:
        obj={"id":case["id"],"type":case["deliverable_type"],
             "acceptance":{"target":case["owner_outcome_oracle"]},
             "prohibitions":[case["forbidden_implicit_effect"]]}
        if obj["type"]=="MULTI_ASPECT_IMAGE_SET":
            obj["variants"]=[{"id":"tall","shape":{"width":1080,"height":1440,"orientation":"PORTRAIT"}},
                             {"id":"wide","shape":{"width":1440,"height":1080,"orientation":"LANDSCAPE"}}]
        result=build_quality_plan([obj])
        plan=result["plans"][0]
        assert plan["type"]==obj["type"]
        assert plan["owner_acceptance"]["target"]==case["owner_outcome_oracle"]
        assert plan["criteria"] and plan["quality_verified"] is False
        assert plan["owner_outcome_verified"] is False
        assert result["release_authorized"] is False

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
