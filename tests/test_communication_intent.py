import pytest

from social_media_studio.domain.communication import CommunicationIntent, CommunicationIntentError
from social_media_studio.domain.editorial import EditorialContractError, inspect_long_article, inspect_platform_package, inspect_short_copy


def base_intent():
    return {
        "schema_version": "1.0",
        "audience": "People who enjoy source-grounded entertainment",
        "value_promise": "A quick, specific moment of recognition",
        "think": "That moment is unexpectedly relatable",
        "feel": "Amused",
        "do": ["SHARE", "COMMENT"],
        "primary_action": "SHARE",
        "mechanism": "Recognition and humor",
        "action_rationale": "It is easy to send to a friend who would recognize the situation.",
        "speaker_relation": "Conversational peer without presuming a shared personal history",
        "grounding_refs": ["source-1"],
        "assumptions": [],
    }


def test_communication_intent_separates_value_response_and_action():
    intent = CommunicationIntent.from_mapping(base_intent())
    assert intent.value_promise == "A quick, specific moment of recognition"
    assert intent.actions == ("SHARE", "COMMENT")
    assert intent.primary_action == "SHARE"
    assert intent.status == "HYPOTHESIS_UNMEASURED"
    assert CommunicationIntent.from_mapping(intent.as_dict()) == intent


def test_mechanism_is_open_text_not_a_closed_engagement_taxonomy():
    data = base_intent()
    data["mechanism"] = "A niche in-joke combined with affectionate absurdity"
    assert CommunicationIntent.from_mapping(data).mechanism == data["mechanism"]


def test_no_forced_action_is_valid_when_think_or_feel_is_the_goal():
    data = {
        "schema_version": "1.0",
        "audience": "People who enjoy quiet game-world moments",
        "value_promise": "A moment of calm immersion",
        "feel": "Relaxed",
        "do": [],
    }
    intent = CommunicationIntent.from_mapping(data)
    assert intent.actions == ()
    assert intent.primary_action is None
    assert intent.status == "HYPOTHESIS_UNMEASURED"


def test_declared_actions_need_one_primary_action_and_a_reason():
    data = base_intent()
    data["primary_action"] = "FOLLOW"
    with pytest.raises(CommunicationIntentError, match="one of the declared"):
        CommunicationIntent.from_mapping(data)
    data = base_intent()
    data["action_rationale"] = ""
    with pytest.raises(CommunicationIntentError, match="action_rationale"):
        CommunicationIntent.from_mapping(data)


def test_unknown_actions_empty_responses_and_unknown_fields_fail_closed():
    data = base_intent()
    data["do"] = ["GO_VIRAL"]
    data["primary_action"] = "GO_VIRAL"
    with pytest.raises(CommunicationIntentError, match="unsupported"):
        CommunicationIntent.from_mapping(data)
    with pytest.raises(CommunicationIntentError, match="at least one"):
        CommunicationIntent.from_mapping({
            "schema_version": "1.0", "audience": "Viewers",
            "value_promise": "A useful moment", "do": [],
        })
    data = base_intent()
    data["ctr_prediction"] = 0.42
    with pytest.raises(CommunicationIntentError, match="unknown"):
        CommunicationIntent.from_mapping(data)


def test_short_copy_and_platform_package_keep_intent_unmeasured_and_source_bound():
    intent = base_intent()
    short = inspect_short_copy({
        "schema_version": "1.0", "text": "One concise line.",
        "platform": "X", "locale": "en-US", "content_intent": "Entertainment",
        "source_refs": ["source-1"], "communication_intent": intent,
    })
    assert short["communication_intent"]["status"] == "HYPOTHESIS_UNMEASURED"
    package = inspect_platform_package({
        "schema_version": "1.0", "content_intent": "Entertainment",
        "communication_intent": intent,
        "variants": [{
            "variant_id": "x-en", "platform": "X", "locale": "en-US",
            "title": "A truthful hook", "description": "A different context line",
            "source_refs": ["source-1"],
        }],
    })
    assert package["communication_intent"]["primary_action"] == "SHARE"
    with pytest.raises(EditorialContractError, match="grounding_refs"):
        inspect_short_copy({
            "schema_version": "1.0", "text": "One line", "platform": "X",
            "locale": "en-US", "content_intent": "Entertainment",
            "source_refs": [], "communication_intent": intent,
        })


def test_long_article_can_declare_reader_response_without_claiming_quality():
    intent = base_intent()
    report = inspect_long_article({
        "schema_version": "1.0", "title": "A useful argument",
        "locale": "en-US", "intent_kind": "ARGUMENT",
        "body": "A complete short article.",
        "factual_claims": [{
            "claim_id": "claim-1", "statement": "A sourced statement",
            "source_refs": ["source-1"],
        }],
        "communication_intent": intent,
    })
    assert report["communication_intent"]["status"] == "HYPOTHESIS_UNMEASURED"
    assert report["publication_authorized"] is False
