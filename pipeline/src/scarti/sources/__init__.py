from scarti.sources.bankit import BankITSource
from scarti.sources.base import Observation, Series, SeriesData, Source, load_catalog
from scarti.sources.istat import ISTATSource

__all__ = [
    "BankITSource",
    "ISTATSource",
    "Observation",
    "Series",
    "SeriesData",
    "Source",
    "load_catalog",
]


def get_source(name: str) -> Source:
    if name == "istat":
        return ISTATSource()
    if name == "bankit":
        return BankITSource()
    raise ValueError(f"Unknown source: {name}")
