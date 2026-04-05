from __future__ import annotations

from rich import box
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from mlsanity.types import Report


def _overall_style(overall: str) -> str:
    return {
        "healthy": "bold bright_green",
        "acceptable": "bold bright_cyan",
        "needs_attention": "bold bright_yellow",
        "critical": "bold bright_red",
    }.get(overall, "bold white")


def _check_status_style(status: str) -> str:
    return {
        "ok": "bright_green",
        "warning": "bright_yellow",
        "error": "bright_red",
    }.get(status, "white")


def _check_status_label(status: str) -> str:
    labels = {"ok": "OK", "warning": "WARN", "error": "FAIL"}
    return labels.get(status, status.upper())


def _score_meter(score: int, width: int = 20) -> Text:
    filled = int(round((score / 100.0) * width))
    filled = max(0, min(width, filled))
    bar = "█" * filled + "░" * (width - filled)
    t = Text()
    t.append(bar, style="bright_blue")
    t.append(f"  {score}/100", style="bold")
    return t


def print_report(report: Report, *, console: Console | None = None) -> None:
    con = console or Console()

    path_display = report.dataset_path or "—"
    if len(path_display) > 72:
        path_display = "…" + path_display[-69:]

    meta = Table.grid(padding=(0, 2), expand=True)
    meta.add_column(justify="right", style="dim", no_wrap=True)
    meta.add_column(ratio=1)
    meta.add_row("Path", path_display)
    meta.add_row("Type", f"[cyan]{report.dataset_type}[/cyan]")
    meta.add_row("Samples", f"[bold white]{report.total_samples:,}[/bold white]")

    score_row = Table.grid(padding=(0, 2), expand=True)
    score_row.add_column(justify="right", style="dim", no_wrap=True)
    score_row.add_column(ratio=1)
    score_row.add_row("Health", _score_meter(report.health_score))
    score_row.add_row(
        "Status",
        Text.assemble(
            ("● ", _overall_style(report.overall_status)),
            (report.overall_status.replace("_", " "), _overall_style(report.overall_status)),
        ),
    )

    header_inner = Group(meta, Text(""), score_row)
    con.print()
    con.print(
        Panel(
            header_inner,
            title="[bold bright_white on blue] MLSanity [/bold bright_white on blue]",
            subtitle="[dim]dataset sanity report[/dim]",
            subtitle_align="left",
            border_style="bright_blue",
            box=box.ROUNDED,
            padding=(1, 2),
        )
    )

    checks_table = Table(
        box=box.ROUNDED,
        show_header=True,
        header_style="bold bright_white",
        border_style="dim",
        pad_edge=False,
        expand=True,
    )
    checks_table.add_column("Status", justify="center", width=6, no_wrap=True)
    checks_table.add_column("Check", style="cyan", no_wrap=True, max_width=18)
    checks_table.add_column("Summary", ratio=1)

    for c in report.checks:
        st_style = _check_status_style(c.status)
        st_label = _check_status_label(c.status)
        checks_table.add_row(
            f"[{st_style}]{st_label}[/]",
            c.name,
            c.summary,
        )
        for s in c.suggestions[:4]:
            checks_table.add_row("", "", f"[dim]↳[/dim] [dim]{s}[/dim]")

    con.print()
    con.print(
        Panel(
            checks_table,
            title="[bold]Checks[/bold]",
            border_style="dim",
            box=box.ROUNDED,
            padding=(0, 1),
        )
    )
    con.print()
