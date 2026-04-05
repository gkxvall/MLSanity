import typer
from typing import Optional

from rich import box
from rich.console import Console, Group
from rich.panel import Panel
from rich.text import Text

from mlsanity.engine import run_scan
from mlsanity.reporting.html_report import write_html_report
from mlsanity.reporting.json_report import write_json_report
from mlsanity.reporting.terminal import print_report

_APP_HELP = """\
MLSanity — sanity-check image classification folders or tabular CSV datasets before you train.

[b]Commands[/b]
  [cyan]doctor[/cyan]    Scan a dataset: run checks, print a summary; optional [cyan]--json[/cyan] / [cyan]--html[/cyan].
  [cyan]version[/cyan]   Print the installed MLSanity version.

Use [cyan]mlsanity doctor --help[/cyan] for all scan options.

[b]Examples[/b]
  mlsanity doctor ./dataset --type image
  mlsanity doctor ./data.csv --type tabular --target label
  mlsanity doctor ./data.csv --type tabular --target label --split-column split --json r.json --html r.html
  mlsanity version
"""

app = typer.Typer(
    name="mlsanity",
    help=_APP_HELP.rstrip(),
    rich_markup_mode="rich",
    pretty_exceptions_show_locals=False,
)


@app.command(
    help=(
        "Scan PATH with loaders and checks; print health score and per-check results. "
        "Use --json / --html to write reports."
    ),
)
def doctor(
    path: str = typer.Argument(
        ...,
        help="Dataset root: folder (images) or path to a .csv file (tabular).",
        show_default=False,
    ),
    type: str = typer.Option(
        ...,
        "--type",
        help="Dataset kind: 'image' (class folders) or 'tabular' (CSV).",
        rich_help_panel="Dataset",
    ),
    target: Optional[str] = typer.Option(
        None,
        "--target",
        help="Required for tabular: name of the target / label column in the CSV.",
        rich_help_panel="Tabular",
    ),
    split_column: Optional[str] = typer.Option(
        None,
        "--split-column",
        help="Optional for tabular: column name for train/val/test (enables split leakage checks).",
        rich_help_panel="Tabular",
    ),
    json_out: Optional[str] = typer.Option(
        None,
        "--json",
        metavar="PATH",
        help="Write the full structured report to this JSON file.",
        rich_help_panel="Report output",
    ),
    html_out: Optional[str] = typer.Option(
        None,
        "--html",
        metavar="PATH",
        help="Write an HTML report to this file (Jinja template).",
        rich_help_panel="Report output",
    ),
):
    """
    Run all loaders and checks for the given dataset, then print a terminal summary.

    \b
    Image (folder with train/class/... or class/...):
      mlsanity doctor /path/to/images --type image

    \b
    Tabular (CSV with a target column):
      mlsanity doctor /path/to/data.csv --type tabular --target TARGET_COLUMN

    \b
    Tabular + split column + export:
      mlsanity doctor data.csv --type tabular --target y --split-column split \\
          --json out.json --html out.html
    """
    console = Console()
    report = run_scan(path=path, dataset_type=type, target=target, split_column=split_column)
    print_report(report, console=console)
    if json_out:
        write_json_report(report, json_out)
        console.print(
            f"[bright_green]✓[/bright_green] [bold]JSON[/bold]  [dim]→[/dim] [cyan]{json_out}[/cyan]"
        )
    if html_out:
        write_html_report(report, html_out)
        console.print(
            f"[bright_green]✓[/bright_green] [bold]HTML[/bold]  [dim]→[/dim] [cyan]{html_out}[/cyan]"
        )
    if json_out or html_out:
        console.print()


@app.command(
    help="Print the installed MLSanity version (same as package 0.1.0).",
)
def version() -> None:
    """Show version string for support and bug reports."""
    console = Console()
    console.print()
    console.print(
        Panel.fit(
            Group(
                Text.from_markup("[bold bright_white]MLSanity[/bold bright_white] [dim]v0.1.0[/dim]"),
                Text.from_markup("[dim]Sanity-check your dataset before training.[/dim]"),
            ),
            title="[bright_blue]●[/bright_blue]",
            border_style="bright_blue",
            box=box.ROUNDED,
            padding=(1, 3),
        )
    )
    console.print()


if __name__ == "__main__":
    app()
