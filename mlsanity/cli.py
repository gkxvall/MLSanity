import typer
from typing import Optional

from mlsanity.engine import run_scan

app = typer.Typer(help="MLSanity - Sanity-check your dataset before training.")


@app.command()
def doctor(
    path: str = typer.Argument(..., help="Path to dataset folder or CSV file."),
    type: str = typer.Option(..., "--type", help="Dataset type: image or tabular."),
    target: Optional[str] = typer.Option(None, "--target", help="Target column for tabular datasets."),
    split_column: Optional[str] = typer.Option(None, "--split-column", help="Split column for tabular datasets."),
):
    """
    Scan a dataset and print a basic health summary.
    """
    report = run_scan(path=path, dataset_type=type, target=target, split_column=split_column)

    typer.echo("\nMLSanity Report")
    typer.echo("----------------")
    typer.echo(f"Dataset type: {report.dataset_type}")
    typer.echo(f"Total samples: {report.total_samples}")
    typer.echo(f"Health score: {report.health_score}/100")
    typer.echo(f"Overall status: {report.overall_status}\n")


@app.command()
def version():
    print("MLSanity v0.1.0")

if __name__ == "__main__":
    app()