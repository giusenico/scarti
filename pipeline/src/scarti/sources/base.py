from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field

Frequency = Literal["M", "Q", "A"]
SourceName = Literal["istat", "bankit", "eurostat"]
DirectionGood = Literal["up", "down", "neutral"]


class Series(BaseModel):
    id: str
    source: SourceName
    title_it: str
    title_en: str
    category: str
    unit: str
    frequency: Frequency
    seasonally_adjusted: bool
    direction_good: DirectionGood
    sdmx_dataflow: str
    sdmx_key: str
    source_url: str

    @property
    def is_ready(self) -> bool:
        return self.sdmx_dataflow != "TODO" and self.sdmx_key != "TODO"


class Observation(BaseModel):
    period: str
    value: float | None


class SeriesData(BaseModel):
    series: Series
    observations: list[Observation] = Field(default_factory=list)

    def values(self) -> list[float]:
        return [o.value for o in self.observations if o.value is not None]


class Source(ABC):
    name: SourceName

    @abstractmethod
    async def fetch(self, series: Series, *, months: int = 120) -> SeriesData:
        """Fetch the last `months` observations for the given series.

        Implementations must return observations sorted ascending by period
        and must drop the trailing observation if the upstream API is known
        to return a spurious extra point (see ISTAT endPeriod bug).
        """


def load_catalog(path: Path | str) -> list[Series]:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return [Series(**s) for s in raw["series"]]
