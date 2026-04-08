import typer
from pathlib import Path
from typing import Optional

from rich import box
from rich.console import Console, Group
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn, TimeElapsedColumn
from rich.table import Table
from rich.text import Text

from mlsanity.engine import build_compare_report, run_scan
from mlsanity.reporting.quality_gates import evaluate_quality_gates
from mlsanity.reporting.compare_html_report import write_compare_html_report
from mlsanity.reporting.compare_json_report import write_compare_json_report
from mlsanity.reporting.compare_terminal import print_compare_report
from mlsanity.reporting.html_report import write_html_report
from mlsanity.reporting.json_report import write_json_report
from mlsanity.reporting.terminal import print_report

_APP_HELP = """\
MLSanity — sanity-check image classification folders or tabular CSV datasets before you train.

[b]Commands[/b]
  [cyan]doctor[/cyan]    Scan a dataset: run checks, print a summary; optional [cyan]--json[/cyan] / [cyan]--html[/cyan].
  [cyan]compare[/cyan]   Compare two dataset versions (old vs new); optional compare JSON/HTML reports.
  [cyan]version[/cyan]   Print the installed MLSanity version.

Use [cyan]mlsanity doctor --help[/cyan] for all scan options.

[b]Examples[/b]
  mlsanity doctor ./dataset --type image
  mlsanity doctor ./data.csv --type tabular --target label
  mlsanity compare ./old ./new --type image
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


def _run_compare_with_progress(
    console: Console,
    *,
    old_path: str,
    new_path: str,
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
        task_id = progress.add_task("Scanning old dataset", total=3)
        old_report = run_scan(old_path, dataset_type, target=target, split_column=split_column)
        progress.update(task_id, completed=1, description="Scanning new dataset")
        new_report = run_scan(new_path, dataset_type, target=target, split_column=split_column)
        progress.update(task_id, completed=2, description="Building comparison")
        compare_report = build_compare_report(old_report, new_report, dataset_type)
        progress.update(task_id, completed=3, description="Complete")
        return old_report, new_report, compare_report


@app.command(
    help=(
        "Scan PATH with loaders and checks; print health score and per-check results. "
        "Use --json / --html to write reports."
    ),
)
def doctor(
    path: str = typer.Argument(
        ...,
        help="Dataset root: folder (images) or path to a tabular file (.csv/.tsv/.parquet).",
        show_default=False,
    ),
    type: str = typer.Option(
        ...,
        "--type",
        help="Dataset kind: 'image' (class folders) or 'tabular' (CSV/TSV/Parquet).",
        rich_help_panel="Dataset",
    ),
    target: Optional[str] = typer.Option(
        None,
        "--target",
        help="Required for tabular: name of the target / label column in the tabular file.",
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
    min_score: Optional[int] = typer.Option(
        None,
        "--min-score",
        help="CI gate: fail if health score is below this value (0-100).",
        rich_help_panel="Quality gates",
    ),
    fail_on: Optional[str] = typer.Option(
        None,
        "--fail-on",
        help="CI gate: fail if any check is 'warning' (warning+error) or 'error'.",
        rich_help_panel="Quality gates",
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

    quality_gates = evaluate_quality_gates(report, min_score=min_score, fail_on=fail_on)

    saved: list[tuple[str, str]] = []
    if json_out:
        json_path = str(Path(json_out).expanduser().resolve())
        write_json_report(report, json_path, quality_gates=quality_gates)
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

    passed = bool(quality_gates.get("passed"))
    console.print()
    if passed:
        console.print(f"[bold bright_green]Quality gates:[/bold bright_green] PASSED — {quality_gates['exit_reason']}")
    else:
        console.print(f"[bold bright_red]Quality gates:[/bold bright_red] FAILED — {quality_gates['exit_reason']}")
        raise typer.Exit(code=1)

    console.print()


@app.command(
    help=(
        "Compare two dataset versions and show deltas for sample counts, health score, and checks. "
        "Use --json / --html to export compare reports."
    ),
)
def compare(
    old_path: str = typer.Argument(..., help="Path to old dataset version (folder or tabular file)."),
    new_path: str = typer.Argument(..., help="Path to new dataset version (folder or tabular file)."),
    type: str = typer.Option(
        ...,
        "--type",
        help="Dataset type: image or tabular (CSV/TSV/Parquet).",
        rich_help_panel="Dataset",
    ),
    target: Optional[str] = typer.Option(
        None,
        "--target",
        help="Required for tabular datasets: target column name in the tabular file.",
        rich_help_panel="Tabular",
    ),
    split_column: Optional[str] = typer.Option(
        None,
        "--split-column",
        help="Optional split column for tabular datasets.",
        rich_help_panel="Tabular",
    ),
    json_out: Optional[str] = typer.Option(
        None,
        "--json",
        metavar="PATH",
        help="Write compare JSON report to this file.",
        rich_help_panel="Report output",
    ),
    html_out: Optional[str] = typer.Option(
        None,
        "--html",
        metavar="PATH",
        help="Write compare HTML report to this file.",
        rich_help_panel="Report output",
    ),
    min_score: Optional[int] = typer.Option(
        None,
        "--min-score",
        help="CI gate: fail if NEW dataset health score is below this value (0-100).",
        rich_help_panel="Quality gates",
    ),
    fail_on: Optional[str] = typer.Option(
        None,
        "--fail-on",
        help="CI gate: fail if any check is 'warning' (warning+error) or 'error' for NEW dataset.",
        rich_help_panel="Quality gates",
    ),
) -> None:
    console = Console()
    _old, _new, compare_report = _run_compare_with_progress(
        console,
        old_path=old_path,
        new_path=new_path,
        dataset_type=type,
        target=target,
        split_column=split_column,
    )
    print_compare_report(compare_report, console=console)

    quality_gates = evaluate_quality_gates(_new, min_score=min_score, fail_on=fail_on)

    saved: list[tuple[str, str]] = []
    if json_out:
        json_path = str(Path(json_out).expanduser().resolve())
        write_compare_json_report(compare_report, json_path, quality_gates=quality_gates)
        saved.append(("JSON", json_path))
    if html_out:
        html_path = str(Path(html_out).expanduser().resolve())
        write_compare_html_report(compare_report, html_path)
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
                title="[bold green]Compare reports saved[/bold green]",
                border_style="green",
                box=box.ROUNDED,
            )
        )
    else:
        console.print()
        console.print(
            "[dim]No compare report files written. Use [cyan]--json PATH[/cyan] and/or [cyan]--html PATH[/cyan].[/dim]"
        )
    console.print()

    passed = bool(quality_gates.get("passed"))
    if passed:
        console.print(
            f"[bold bright_green]Quality gates:[/bold bright_green] PASSED — {quality_gates['exit_reason']}"
        )
    else:
        console.print(
            f"[bold bright_red]Quality gates:[/bold bright_red] FAILED — {quality_gates['exit_reason']}"
        )
        raise typer.Exit(code=1)


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
                Text.from_markup("[bold bright_white]MLSanity[/bold bright_white] [dim]v0.2.0[/dim]"),
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
