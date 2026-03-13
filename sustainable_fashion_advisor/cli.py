from typing import Optional

import typer

from sustainable_fashion_advisor.formatting import format_json, format_report
from sustainable_fashion_advisor.models import ProductInput
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
    url: Optional[str] = typer.Option(None, help="Product URL mapped to a local demo fixture."),
    title: Optional[str] = typer.Option(None, help="Manual product title."),
    brand: Optional[str] = typer.Option(None, help="Manual brand name."),
    price: Optional[float] = typer.Option(None, help="Manual product price."),
    currency: str = typer.Option("GBP", help="Currency code for the provided price."),
    materials: Optional[str] = typer.Option(
        None, help='Material composition like "80% wool, 20% nylon".'
    ),
    category: Optional[str] = typer.Option(None, help="Garment category like sweater or coat."),
    as_json: bool = typer.Option(False, "--json", help="Return the full report as JSON."),
) -> None:
    configure_telemetry()
    input_data = ProductInput(
        url=url,
        title=title,
        brand=brand,
        price=price,
        currency=currency,
        materials=materials,
        category=category,
    )
    report = analyze_item(input_data)
    output = format_json(report) if as_json else format_report(report)
    typer.echo(output)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
