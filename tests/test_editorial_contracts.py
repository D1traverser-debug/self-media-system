import json
import pytest

from social_media_studio.domain.editorial import (
    EditorialContractError, inspect_long_article, inspect_platform_package,
)


def test_six_platforms_plus_toutiao_bilingual_packaging_has_distinct_roles():
    kinds=["X","TIKTOK","YOUTUBE","DOUYIN","WECHAT_CHANNELS","TOUTIAO","XIAOHONGSHU","BILIBILI"]
    variants=[]
    for index,platform in enumerate(kinds):
        variants.append({
            "variant_id":f"v-{index}", "platform":platform,
            "locale":"en-US" if index<3 else "zh-CN",
            "title":f"An intriguing hook {index}",
            "description":f"A different contextual statement {index}",
            "cover_copy":f"Visual question {index}?",
            "hashtags":["#Gaming","#Media"] if index<3 else ["#游戏","#趣闻"],
            "source_refs":["owner-media-source"],
        })
    report=inspect_platform_package({"schema_version":"1.0",
        "content_intent":"The player unexpectedly dances with two apples", "variants":variants})
    assert len(report["variants"])==8
    assert "TOUTIAO" in {x["platform"] for x in report["variants"]}
    assert report["structural_status"]=="PASS"
    assert report["creative_quality_verified"] is False
    assert report["publication_authorized"] is False
    assert all(x["semantic_distinctness_verified"] is False for x in report["variants"])
    assert all(x["platform_spec_current_verified"] is False for x in report["variants"])


def test_title_description_cover_exact_duplicates_are_rejected_not_mistaken_for_quality():
    with pytest.raises(EditorialContractError,match="repeat"):
        inspect_platform_package({"schema_version":"1.0","content_intent":"A useful story",
            "variants":[{"variant_id":"a","platform":"X","locale":"en-US",
                         "title":"WHO SAID I'M DONE?","cover_copy":"Who said Im done","description":"A new outcome"}]})
    with pytest.raises(EditorialContractError,match="duplicate hashtags"):
        inspect_platform_package({"schema_version":"1.0","content_intent":"A useful story",
            "variants":[{"variant_id":"a","platform":"X","locale":"en-US",
                         "description":"Something interesting","hashtags":["#News","#news"]}]})


def test_article_structure_allows_variable_length_and_visual_slots_without_hardcoding_pages():
    report=inspect_long_article({"schema_version":"1.0","title":"When a Meme Walks Alone",
        "locale":"en-US","intent_kind":"ARGUMENT",
        "sections":[
            {"section_id":"setup","body":"A real argument starts here."},
            {"section_id":"change","body":"A new observation makes the thesis matter."},
        ],
        "factual_claims":[{"claim_id":"c1","statement":"A publicly observable event","source_refs":["source-1"]}],
        "visual_slots":[{"section_id":"change","purpose":"Explain the central shift visually"}]})
    assert report["section_count"]==2
    assert report["visual_slot_count"]==1
    assert report["fact_check_verified"] is False
    assert report["argument_quality_verified"] is False
    assert report["owner_outcome_verified"] is False


def test_article_and_package_do_not_require_a_video_project_or_fixed_article_length():
    short=inspect_long_article({"schema_version":"1.0","title":"One thought",
        "locale":"zh-CN","intent_kind":"PERSONAL_ESSAY","body":"不同话题也可以独立表达。"})
    assert short["section_count"]==0
    assert short["originality_verified"] is False
    single=inspect_platform_package({"schema_version":"1.0","content_intent":"One line only",
        "variants":[{"variant_id":"just-caption","platform":"TIKTOK","locale":"en-US",
                     "description":"A single line is all this user asked for."}]})
    assert single["variants"][0]["title"] is None
    assert single["variants"][0]["cover_copy"] is None


def test_malformed_proposals_and_false_sources_are_not_silently_passed():
    with pytest.raises(EditorialContractError):
        inspect_platform_package({"schema_version":"1.0","content_intent":"test",
                                  "variants":[{"variant_id":"bad","platform":"UNKNOWN","locale":"en-US",
                                               "description":"fake"}]})
    with pytest.raises(EditorialContractError):
        inspect_long_article({"schema_version":"1.0","title":"Topic","locale":"en-US",
                              "intent_kind":"ARGUMENT","sections":[{"section_id":"a","body":"first"},
                                                                    {"section_id":"a","body":"dup"}]})
