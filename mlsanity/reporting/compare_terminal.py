from __future__ import annotations

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from mlsanity.types import CompareReport


def print_compare_report(report: CompareReport, *, console: Console | None = None) -> None:
    con = console or Console()

    summary = Table.grid(padding=(0, 2), expand=True)
    summary.add_column(justify="right", style="dim", no_wrap=True)
    summary.add_column(ratio=1)
    summary.add_row("Type", f"[cyan]{report.dataset_type}[/cyan]")
    summary.add_row("Old path", report.old_path)
    summary.add_row("New path", report.new_path)
    summary.add_row(
        "Samples",
        f"{report.old_total_samples:,} → {report.new_total_samples:,} [dim]({report.total_samples_delta:+,})[/dim]",
    )
    summary.add_row(
        "Health",
        f"{report.old_health_score} → {report.new_health_score} [dim]({report.health_score_delta:+})[/dim]",
    )

    con.print()
    con.print(
        Panel(
            summary,
            title="[bold bright_white on blue] MLSanity Compare [/bold bright_white on blue]",
            border_style="bright_blue",
            box=box.ROUNDED,
            padding=(1, 2),
        )
    )

    checks = Table(box=box.ROUNDED, expand=True)
    checks.add_column("Check", style="cyan", no_wrap=True)
    checks.add_column("Old", justify="center", no_wrap=True)
    checks.add_column("New", justify="center", no_wrap=True)
    checks.add_column("Issues", justify="right", no_wrap=True)

    for d in report.check_deltas:
        checks.add_row(
            d.name,
            d.old_status,
            d.new_status,
            f"{d.old_issue_count} → {d.new_issue_count} ({d.issue_delta:+})",
        )

    con.print()
    con.print(
        Panel(
            checks,
            title="[bold]Check deltas[/bold]",
            border_style="dim",
            box=box.ROUNDED,
            padding=(0, 1),
        )
    )

    notes = Table.grid(padding=(0, 2), expand=True)
    notes.add_column(justify="right", style="dim", no_wrap=True)
    notes.add_column(ratio=1)
    notes.add_row(
        "Introduced",
        ", ".join(report.introduced_regressions) if report.introduced_regressions else "none",
    )
    notes.add_row(
        "Resolved",
        ", ".join(report.resolved_issues) if report.resolved_issues else "none",
    )
    con.print()
    con.print(Panel(notes, title="[bold]Regressions & resolutions[/bold]", border_style="dim", box=box.ROUNDED))
    con.print()
