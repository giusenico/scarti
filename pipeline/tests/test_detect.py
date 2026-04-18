"""Detection logic tests using synthetic data — no network."""
from __future__ import annotations

import numpy as np
import pytest

from scarti.detect.detector import detect_anomaly
from scarti.detect.mod_zscore import modified_zscore
from scarti.detect.yoy import mom_change, yoy_change
from scarti.sources.base import Observation, Series, SeriesData


def _mk_series(frequency: str = "M") -> Series:
    return Series(
        id="test.synthetic",
        source="istat",
        title_it="Test",
        title_en="Test",
        category="test",
        unit="idx",
        frequency=frequency,  # type: ignore[arg-type]
        seasonally_adjusted=True,
        direction_good="up",
        sdmx_dataflow="X",
        sdmx_key="Y",
        source_url="https://example.com",
    )


def _obs(values: list[float], frequency: str = "M") -> list[Observation]:
    periods: list[str] = []
    year, month = 2019, 1
    for _ in values:
        if frequency == "M":
            periods.append(f"{year:04d}-{month:02d}")
            month += 1
            if month > 12:
                month = 1
                year += 1
        else:
            periods.append(f"{year}-Q{((month - 1) // 3) + 1}")
            month += 3
            if month > 12:
                month = 1
                year += 1
    return [Observation(period=p, value=v) for p, v in zip(periods, values, strict=True)]


def test_mod_zscore_flat_series_is_none():
    # Zero MAD (constant) → cannot compute robust z-score.
    assert modified_zscore([10.0] * 48) is None


def test_mod_zscore_spike_is_large():
    rng = np.random.default_rng(42)
    values = (100 + rng.normal(0, 1, 60)).tolist()
    values[-1] = 120.0  # 20 sigma-ish spike
    result = modified_zscore(values)
    assert result is not None
    assert result.zscore > 10


def test_mom_and_yoy():
    values = list(range(1, 25))  # 1..24, monthly
    assert mom_change(values) == pytest.approx(100 / 23, rel=1e-3)
    yoy = yoy_change(values, period=12, history_years=10)
    assert yoy is not None
    assert yoy.last_yoy_pct > 0


def test_detect_anomaly_on_calm_series_is_none():
    rng = np.random.default_rng(0)
    # Seasonal-ish pattern, no recent break.
    values = [100 + 5 * np.sin(i / 12 * 2 * np.pi) + rng.normal(0, 0.5) for i in range(60)]
    data = SeriesData(series=_mk_series(), observations=_obs(values))
    assert detect_anomaly(data) is None


def test_detect_anomaly_on_breaking_series_fires():
    rng = np.random.default_rng(1)
    values = [100 + 5 * np.sin(i / 12 * 2 * np.pi) + rng.normal(0, 0.5) for i in range(60)]
    values[-1] += 15  # sharp break
    data = SeriesData(series=_mk_series(), observations=_obs(values))
    anomaly = detect_anomaly(data)
    assert anomaly is not None
    assert anomaly.direction == "up"
    assert anomaly.severity in ("moderate", "strong", "extreme")
    assert abs(anomaly.zscore or 0) >= 2.0


def test_detect_anomaly_short_series_is_none():
    data = SeriesData(series=_mk_series(), observations=_obs([1.0, 2.0, 3.0]))
    assert detect_anomaly(data) is None
