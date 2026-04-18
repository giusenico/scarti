"""Domain models shared across pipeline stages."""
from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

from scarti.sources.base import Observation, Series

Severity = Literal["moderate", "strong", "extreme"]
Direction = Literal["up", "down"]
DetectionMethod = Literal["mod_zscore_stl", "mod_zscore", "yoy_percentile"]


class Anomaly(BaseModel):
    series_id: str
    period: str
    value: float

    method: DetectionMethod
    zscore: float | None = None          # signed, on residual when STL used
    baseline_center: float | None = None  # median (MAD) or mean (z-score)
    baseline_scale: float | None = None   # MAD*1.4826 or std

    severity: Severity
    direction: Direction

    mom_change_pct: float | None = None
    yoy_change_pct: float | None = None
    yoy_percentile: float | None = None  # 0-100, only for yoy_percentile method

    history: list[Observation] = Field(default_factory=list)

    def is_stronger_than(self, other: Anomaly) -> bool:
        return abs(self.zscore or 0) > abs(other.zscore or 0)


class ReportLocaleBody(BaseModel):
    headline: str
    lede: str
    sections: list[SectionBody]


class SectionBody(BaseModel):
    anomaly_index: int  # index into Report.anomalies
    body: str           # markdown paragraph(s)


class Report(BaseModel):
    slug: str                         # "2026-w16"
    week_of: date
    generated_at: datetime
    anomalies: list[Anomaly]
    it: ReportLocaleBody
    en: ReportLocaleBody
    series_meta: dict[str, Series]    # keyed by series_id, for rendering

    def chart_payload(self) -> dict:
        """JSON payload for the frontend — series history for charts."""
        return {
            a.series_id: {
                "series_id": a.series_id,
                "title_it": self.series_meta[a.series_id].title_it,
                "title_en": self.series_meta[a.series_id].title_en,
                "unit": self.series_meta[a.series_id].unit,
                "anomaly_period": a.period,
                "anomaly_value": a.value,
                "history": [o.model_dump() for o in a.history],
            }
            for a in self.anomalies
        }


ReportLocaleBody.model_rebuild()
