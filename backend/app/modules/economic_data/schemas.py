from typing import Literal, Optional

from pydantic import BaseModel

RegionT = Literal["ES", "EA", "US", "GLOBAL"]
IndicatorTypeT = Literal[
    "inflation",
    "core_inflation",
    "unemployment",
    "gdp",
    "policy_rate",
    "bond_10y",
    "euribor",
    "index",
    "forex",
]
InterpretationT = Literal["favorable", "neutral", "adverse", "no_data"]


class IndicatorOut(BaseModel):
    series_id: str
    region: RegionT
    indicator: IndicatorTypeT
    name: str
    value: Optional[float]
    prev_value: Optional[float]
    change: Optional[float]
    period: str
    unit: str
    source: str
    observation_date: str
    is_stale: bool = False


class RegionSnapshotOut(BaseModel):
    region: RegionT
    indicators: list[IndicatorOut]


class MacroSnapshotOut(BaseModel):
    spain: RegionSnapshotOut
    eurozone: RegionSnapshotOut
    us: RegionSnapshotOut
    last_refreshed: str


class ImpactItem(BaseModel):
    title: str
    macro_value: Optional[float]
    personal_value: Optional[float]
    delta: Optional[float]
    interpretation: InterpretationT
    description: str


class PersonalImpactOut(BaseModel):
    inflation_vs_savings: ImpactItem
    rates_vs_liquidity: ImpactItem
    market_vs_portfolio: ImpactItem
    purchasing_power: ImpactItem
