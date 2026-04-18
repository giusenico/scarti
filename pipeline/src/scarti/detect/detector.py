"""Orchestrator: given a SeriesData, return an Anomaly (or None)."""
from __future__ import annotations

from scarti.detect.mod_zscore import modified_zscore
from scarti.detect.stl import stl_mod_zscore
from scarti.detect.yoy import mom_change, yoy_change
from scarti.models import Anomaly, DetectionMethod, Direction, Severity
from scarti.sources.base import SeriesData

# Thresholds on |modified z-score|.
MODERATE = 2.0
STRONG = 3.0
EXTREME = 4.0


def _severity(zscore: float) -> Severity | None:
    z = abs(zscore)
    if z >= EXTREME:
        return "extreme"
    if z >= STRONG:
        return "strong"
    if z >= MODERATE:
        return "moderate"
    return None


def _period_for(frequency: str) -> int:
    return {"M": 12, "Q": 4, "A": 1}.get(frequency, 12)


def detect_anomaly(data: SeriesData, *, baseline_months: int = 60) -> Anomaly | None:
    """Return an Anomaly iff the latest observation is statistically notable.

    The method used (STL residual vs. raw modified z-score) is chosen
    automatically based on data length and frequency.
    """
    series = data.series
    values = data.values()
    if len(values) < 12:
        return None

    values = values[-baseline_months:]
    period = _period_for(series.frequency)

    method: DetectionMethod
    zscore: float
    center: float
    scale: float

    # Prefer STL residual for sub-annual series with enough history.
    if series.frequency in ("M", "Q"):
        stl = stl_mod_zscore(values, period=period)
        if stl is not None:
            method = "mod_zscore_stl"
            zscore = stl.zscore
            center = stl.residual_median
            scale = stl.residual_mad
        else:
            mz = modified_zscore(values)
            if mz is None:
                return None
            method = "mod_zscore"
            zscore = mz.zscore
            center = mz.median
            scale = mz.mad
    else:
        mz = modified_zscore(values)
        if mz is None:
            return None
        method = "mod_zscore"
        zscore = mz.zscore
        center = mz.median
        scale = mz.mad

    severity = _severity(zscore)
    if severity is None:
        return None

    direction: Direction = "up" if zscore > 0 else "down"
    yoy = yoy_change(values, period=period)
    mom = mom_change(values)

    return Anomaly(
        series_id=series.id,
        period=data.observations[-1].period,
        value=values[-1],
        method=method,
        zscore=zscore,
        baseline_center=center,
        baseline_scale=scale,
        severity=severity,
        direction=direction,
        mom_change_pct=mom,
        yoy_change_pct=yoy.last_yoy_pct if yoy else None,
        yoy_percentile=yoy.percentile if yoy else None,
        history=data.observations[-baseline_months:],
    )


def detect_all(datasets: list[SeriesData]) -> list[Anomaly]:
    """Run detection on every series, return only the ones that fired, sorted by |z|."""
    anomalies = [a for d in datasets if (a := detect_anomaly(d)) is not None]
    anomalies.sort(key=lambda a: abs(a.zscore or 0), reverse=True)
    return anomalies
