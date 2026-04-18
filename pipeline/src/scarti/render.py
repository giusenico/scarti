"""Render a Report to the Astro site filesystem.

Writes two files per run:
  <site>/src/content/reports/<slug>.json    — structured report consumed by Astro
  <site>/src/data/series/<slug>.json        — chart-ready series history
"""
from __future__ import annotations

import json
from pathlib import Path

from scarti.models import Report


def render_report(
    report: Report,
    *,
    content_dir: Path,
    data_dir: Path,
) -> tuple[Path, Path]:
    content_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    report_path = content_dir / f"{report.slug}.json"
    data_path = data_dir / f"{report.slug}.json"

    report_payload = {
        "slug": report.slug,
        "week_of": report.week_of.isoformat(),
        "generated_at": report.generated_at.isoformat(),
        "anomalies": [a.model_dump(mode="json", exclude={"history"}) for a in report.anomalies],
        "it": report.it.model_dump(),
        "en": report.en.model_dump(),
    }
    report_path.write_text(
        json.dumps(report_payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    data_path.write_text(
        json.dumps(report.chart_payload(), ensure_ascii=False, indent=2), encoding="utf-8"
    )

    return report_path, data_path
