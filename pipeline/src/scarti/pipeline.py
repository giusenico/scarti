"""End-to-end pipeline: fetch → detect → narrate → render.

Stateless: no disk writes until the final render step. All intermediate state
lives in memory. Call `run_weekly()` once per week (Monday morning).
"""
from __future__ import annotations

import asyncio
import os
from datetime import date, timedelta
from pathlib import Path

from scarti.detect import detect_all
from scarti.models import Report
from scarti.narrate import narrate_report
from scarti.render import render_report
from scarti.sources import Series, SeriesData, get_source, load_catalog


def _week_slug(d: date) -> str:
    year, week, _ = d.isocalendar()
    return f"{year}-w{week:02d}"


async def fetch_all(catalog: list[Series]) -> list[SeriesData]:
    """Fetch every READY series from its source, in sequence per source (rate limits).

    Sources are fetched in parallel with each other, but within a source the
    rate limiter serializes requests.
    """
    by_source: dict[str, list[Series]] = {}
    for s in catalog:
        if s.is_ready:
            by_source.setdefault(s.source, []).append(s)

    async def fetch_source(source_name: str, series_list: list[Series]) -> list[SeriesData]:
        src = get_source(source_name)
        try:
            results = []
            for series in series_list:
                try:
                    data = await src.fetch(series)
                    results.append(data)
                except Exception as e:
                    print(f"[warn] {series.id}: {e}")
            return results
        finally:
            await src.aclose()  # type: ignore[attr-defined]

    tasks = [fetch_source(name, lst) for name, lst in by_source.items()]
    chunks = await asyncio.gather(*tasks)
    return [d for chunk in chunks for d in chunk]


async def run_weekly(
    catalog_path: Path,
    *,
    week_of: date | None = None,
    content_dir: Path,
    data_dir: Path,
) -> Report | None:
    """Run the full weekly pipeline. Returns the Report or None if no anomalies."""
    catalog = load_catalog(catalog_path)
    series_by_id = {s.id: s for s in catalog}

    ready = [s for s in catalog if s.is_ready]
    if not ready:
        print("[error] No ready series in catalog — fill in SDMX codes first.")
        return None

    print(f"[info] Fetching {len(ready)} series...")
    datasets = await fetch_all(catalog)
    print(f"[info] Got {len(datasets)} series.")

    anomalies = detect_all(datasets)
    print(f"[info] Detected {len(anomalies)} anomalies.")

    if not anomalies:
        return None

    monday = week_of or (date.today() - timedelta(days=date.today().weekday()))
    slug = _week_slug(monday)

    print(f"[info] Narrating report {slug}...")
    report = narrate_report(
        anomalies,
        series_by_id,
        week_of=monday,
        slug=slug,
    )

    report_path, data_path = render_report(
        report, content_dir=content_dir, data_dir=data_dir
    )
    print(f"[info] Wrote {report_path}")
    print(f"[info] Wrote {data_path}")

    return report


def default_paths() -> tuple[Path, Path]:
    """Resolve site output paths from env vars (with sensible defaults)."""
    root = Path(__file__).resolve().parents[3]
    content = Path(
        os.getenv("SCARTI_SITE_CONTENT_DIR", str(root / "site" / "src" / "content" / "reports"))
    )
    data = Path(
        os.getenv("SCARTI_SITE_DATA_DIR", str(root / "site" / "src" / "data" / "series"))
    )
    return content, data
