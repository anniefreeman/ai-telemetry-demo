import typer

from sustainable_fashion_advisor.agent_parser import (
    AgentParseError,
    build_clarification_question,
    parse_prompt_to_product_input,
)
from sustainable_fashion_advisor.formatting import format_json, format_report
from sustainable_fashion_advisor.pipeline import analyze_item
from sustainable_fashion_advisor.telemetry import configure_telemetry


app = typer.Typer(
    help="Score clothing purchases for sustainability and cost-effectiveness.",
    no_args_is_help=True,
)


@app.callback()
def main_callback() -> None:
    """Sustainable fashion advisor CLI group."""


@app.command("analyze-item")
def analyze_item_command(
    prompt: str = typer.Option(
        ...,
        help="Natural-language purchase prompt, for example 'Should I buy this Patagonia wool sweater for £95?'",
    ),
    as_json: bool = typer.Option(False, "--json", help="Return the full report as JSON."),
) -> None:
    configure_telemetry()
    try:
        input_data = parse_prompt_to_product_input(prompt)
        clarification_question = build_clarification_question(input_data)
        if clarification_question:
            reply = typer.prompt(clarification_question)
            input_data = parse_prompt_to_product_input(prompt, supplemental_details=reply)
    except AgentParseError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)

    report = analyze_item(input_data)
    output = format_json(report) if as_json else format_report(report)
    typer.echo(output)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
