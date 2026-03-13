from typer.testing import CliRunner

from sustainable_fashion_advisor.cli import app
from sustainable_fashion_advisor.pipeline import analyze_item
from sustainable_fashion_advisor.models import ProductInput


runner = CliRunner()


def test_cli_returns_scorecard():
    result = runner.invoke(
        app,
        ["analyze-item", "--url", "https://demo.shop/patagonia-wool-sweater"],
    )
    assert result.exit_code == 0
    assert "Recommendation:" in result.stdout
    assert "Overall score:" in result.stdout


def test_cli_json_output_contains_decision_trajectory():
    result = runner.invoke(
        app,
        ["analyze-item", "--url", "https://demo.shop/patagonia-wool-sweater", "--json"],
    )
    assert result.exit_code == 0
    assert '"decision_trajectory"' in result.stdout


def test_pipeline_report_contains_assumptions_for_missing_data():
    report = analyze_item(ProductInput(title="Loose Knit", price=50))
    assert report.assumptions
    assert any("brand" in item.lower() for item in report.assumptions)
