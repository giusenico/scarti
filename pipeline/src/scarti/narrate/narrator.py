from __future__ import annotations

import json
import os
from datetime import date, datetime, timezone

from scarti.models import Anomaly, Report, ReportLocaleBody
from scarti.narrate.style import OUTPUT_SCHEMA, STYLE_GUIDE_EN, STYLE_GUIDE_IT
from scarti.sources.base import Series

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 4096


def _format_anomaly_for_prompt(index: int, a: Anomaly, series: Series) -> str:
    direction_word = "increase" if a.direction == "up" else "decrease"
    last_12 = a.history[-12:]
    history_lines = "\n".join(
        f"    {o.period}: {o.value}" for o in last_12 if o.value is not None
    )
    yoy_line = (
        f"  YoY change: {a.yoy_change_pct:+.2f}% (stronger than {a.yoy_percentile:.0f}% "
        f"of comparable YoY moves in the last 10 years)"
        if a.yoy_change_pct is not None and a.yoy_percentile is not None
        else ""
    )
    mom_line = f"  MoM change: {a.mom_change_pct:+.2f}%" if a.mom_change_pct is not None else ""

    return f"""Anomaly #{index}
  Series id: {series.id}
  Title (IT): {series.title_it}
  Title (EN): {series.title_en}
  Category: {series.category}
  Unit: {series.unit}
  Frequency: {series.frequency}
  Source: {series.source} — {series.source_url}
  Editorial polarity (direction_good): {series.direction_good}
  Period of anomaly: {a.period}
  Value: {a.value}
  Direction: {a.direction} ({direction_word})
  Severity: {a.severity}  (robust z-score on residual: {a.zscore:+.2f})
  Method: {a.method}
{mom_line}
{yoy_line}
  Last 12 observations:
{history_lines}"""


def _build_user_content(
    anomalies: list[Anomaly], series_by_id: dict[str, Series], week_of: date
) -> str:
    blocks = [
        _format_anomaly_for_prompt(i, a, series_by_id[a.series_id])
        for i, a in enumerate(anomalies)
    ]
    return f"""Week of: {week_of.isoformat()}
Number of anomalies: {len(anomalies)}

{chr(10).join(blocks)}

---
Produce the bilingual report now, following the style guide and the JSON schema."""


def narrate_report(
    anomalies: list[Anomaly],
    series_by_id: dict[str, Series],
    *,
    week_of: date,
    slug: str,
    client=None,
) -> Report:
    """Call Claude API to generate bilingual narrative — returns full Report."""
    if not anomalies:
        raise ValueError("narrate_report requires at least one anomaly")

    try:
        from anthropic import Anthropic
    except ImportError as e:
        raise ImportError(
            "anthropic package required. Install with: pip install -e '.[narrate]'"
        ) from e

    client = client or Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    # System prompt: style guides + schema are stable → cache them.
    # The user message (current anomalies) changes every week → not cached.
    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=[
            {
                "type": "text",
                "text": STYLE_GUIDE_IT + "\n\n---\n\n" + STYLE_GUIDE_EN,
                "cache_control": {"type": "ephemeral"},
            },
            {
                "type": "text",
                "text": OUTPUT_SCHEMA,
                "cache_control": {"type": "ephemeral"},
            },
        ],
        messages=[
            {
                "role": "user",
                "content": _build_user_content(anomalies, series_by_id, week_of),
            }
        ],
    )

    text = "".join(block.text for block in response.content if block.type == "text")
    payload = _extract_json(text)

    return Report(
        slug=slug,
        week_of=week_of,
        generated_at=datetime.now(timezone.utc),
        anomalies=anomalies,
        it=ReportLocaleBody(**payload["it"]),
        en=ReportLocaleBody(**payload["en"]),
        series_meta=series_by_id,
    )


def _extract_json(text: str) -> dict:
    """Tolerant JSON extraction — strips code fences if present."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"No JSON object in model response: {text[:200]}...")
    return json.loads(text[start : end + 1])
