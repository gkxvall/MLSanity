import typer
from pathlib import Path
from typing import Optional

from rich import box
from rich.console import Console, Group
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn, TimeElapsedColumn
from rich.table import Table
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


def _run_scan_with_progress(
    console: Console,
    *,
    path: str,
    dataset_type: str,
    target: Optional[str],
    split_column: Optional[str],
):
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(bar_width=None),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
        transient=True,
    ) as progress:
        task_id: int | None = None

        def on_progress(completed: int, total: int, label: str) -> None:
            nonlocal task_id
            if task_id is None:
                task_id = progress.add_task(label, total=total)
            progress.update(task_id, completed=completed, total=total, description=label)

        return run_scan(
            path=path,
            dataset_type=dataset_type,
            target=target,
            split_column=split_column,
            progress=on_progress,
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
    report = _run_scan_with_progress(
        console,
        path=path,
        dataset_type=type,
        target=target,
        split_column=split_column,
    )

    print_report(report, console=console)

    saved: list[tuple[str, str]] = []
    if json_out:
        json_path = str(Path(json_out).expanduser().resolve())
        write_json_report(report, json_path)
        saved.append(("JSON", json_path))
    if html_out:
        html_path = str(Path(html_out).expanduser().resolve())
        write_html_report(report, html_path)
        saved.append(("HTML", html_path))

    if saved:
        table = Table(show_header=True, header_style="bold", box=box.SIMPLE, padding=(0, 1))
        table.add_column("Format", style="cyan", no_wrap=True)
        table.add_column("Saved to (absolute path)", overflow="fold")

        for fmt, abs_path in saved:
            table.add_row(fmt, abs_path)

        console.print()
        console.print(
            Panel(
                table,
                title="[bold green]Reports saved[/bold green]",
                border_style="green",
                box=box.ROUNDED,
            )
        )
    else:
        console.print()
        console.print(
            "[dim]No report files written. Use [cyan]--json PATH[/cyan] and/or [cyan]--html PATH[/cyan] to save.[/dim]"
        )

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
