from __future__ import annotations

import asyncio
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from scarti.sources import BankITSource, ISTATSource, get_source, load_catalog

app = typer.Typer(no_args_is_help=True, help="Scarti pipeline CLI")
console = Console()

DEFAULT_CATALOG = Path(__file__).parent / "catalog.yaml"


@app.command()
def discover(
    source: str = typer.Option("istat", "--source", help="istat | bankit"),
    query: str = typer.Option(..., "--query", help="Substring to search in dataflow names"),
    limit: int = typer.Option(30, "--limit"),
) -> None:
    """List dataflows from the source matching the query — helper to fill catalog.yaml."""
    if source not in ("istat", "bankit"):
        raise typer.BadParameter(f"Source '{source}' not supported")

    async def _run() -> None:
        src = ISTATSource() if source == "istat" else BankITSource()
        async with src:
            flows = await src.list_dataflows()

        q = query.lower()
        hits = [f for f in flows if q in (f["name"] or "").lower() or q in (f["id"] or "").lower()]
        hits = hits[:limit]

        table = Table(title=f"ISTAT dataflows matching '{query}' ({len(hits)} shown)")
        table.add_column("id", style="cyan")
        table.add_column("name")
        table.add_column("version", style="dim")
        for f in hits:
            table.add_row(f["id"] or "", f["name"] or "", f["version"] or "")
        console.print(table)

    asyncio.run(_run())


@app.command("verify-catalog")
def verify_catalog(
    catalog: Path = typer.Option(DEFAULT_CATALOG, "--catalog"),
) -> None:
    """Print catalog status: which series are ready vs. still TODO."""
    entries = load_catalog(catalog)

    table = Table(title=f"Catalog — {len(entries)} series")
    table.add_column("id", style="cyan")
    table.add_column("source")
    table.add_column("freq")
    table.add_column("ready")
    for s in entries:
        ready = "[green]yes[/green]" if s.is_ready else "[yellow]TODO[/yellow]"
        table.add_row(s.id, s.source, s.frequency, ready)
    console.print(table)

    todo = [s.id for s in entries if not s.is_ready]
    if todo:
        console.print(
            f"\n[yellow]{len(todo)}/{len(entries)} series need SDMX codes.[/yellow] "
            "Use [bold]scarti discover --source istat --query <term>[/bold] to find them."
        )


@app.command()
def fetch(
    series_id: str = typer.Argument(...),
    catalog: Path = typer.Option(DEFAULT_CATALOG, "--catalog"),
    months: int = typer.Option(120, "--months"),
) -> None:
    """Fetch a single series and print the last observations — smoke test."""
    entries = {s.id: s for s in load_catalog(catalog)}
    if series_id not in entries:
        raise typer.BadParameter(f"Unknown series id: {series_id}")
    series = entries[series_id]

    async def _run() -> None:
        src = get_source(series.source)
        async with src:
            data = await src.fetch(series, months=months)

        console.print(f"[bold]{series.title_it}[/bold] — {len(data.observations)} observations")
        for o in data.observations[-12:]:
            console.print(f"  {o.period}  {o.value}")

    asyncio.run(_run())


@app.command()
def run(
    catalog: Path = typer.Option(DEFAULT_CATALOG, "--catalog"),
    content_dir: Path = typer.Option(None, "--content-dir"),
    data_dir: Path = typer.Option(None, "--data-dir"),
    send_mail: bool = typer.Option(False, "--send-mail", help="Send newsletter after rendering"),
) -> None:
    """Run the full weekly pipeline: fetch → detect → narrate → render [→ mail]."""
    from scarti.pipeline import default_paths, run_weekly

    default_content, default_data = default_paths()
    content_dir = content_dir or default_content
    data_dir = data_dir or default_data

    report = asyncio.run(
        run_weekly(catalog, content_dir=content_dir, data_dir=data_dir)
    )
    if report is None:
        console.print("[yellow]No anomalies this week — no report generated.[/yellow]")
        return

    console.print(
        f"[green]Report generated:[/green] {report.slug} "
        f"— {len(report.anomalies)} anomalies"
    )

    if send_mail:
        from scarti.mailer import send_newsletter

        result = send_newsletter(report)
        console.print(
            f"[green]Newsletter:[/green] sent={result.sent} failed={result.failed}"
        )


if __name__ == "__main__":
    app()
