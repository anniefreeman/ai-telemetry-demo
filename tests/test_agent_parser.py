from sustainable_fashion_advisor.agent_parser import build_clarification_question, identify_missing_fields
from sustainable_fashion_advisor.models import ProductInput


def test_identify_missing_fields_skips_followup_for_known_fixture_url():
    missing = identify_missing_fields(
        ProductInput(url="https://demo.shop/patagonia-wool-sweater")
    )

    assert missing == []


def test_build_clarification_question_lists_missing_fields():
    question = build_clarification_question(ProductInput(title="Test Sweater"))

    assert question is not None
    assert "brand" in question
    assert "price" in question
    assert "material composition with percentages" in question
