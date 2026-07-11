"""Contratos del submódulo net_worth (INS-4). Importes como string decimal."""
from __future__ import annotations

from pydantic import BaseModel


class BalanceLineOut(BaseModel):
    key: str          # liquidez | remuneradas | inversion_cash | cartera | fondos | otros | <liability>
    label: str
    amount: str       # decimal-as-string EUR


class BalanceSheetOut(BaseModel):
    month: str
    assets: list[BalanceLineOut]
    liabilities: list[BalanceLineOut]
    total_assets: str
    total_liabilities: str
    net_worth: str
    portfolio_cost: str          # coste de la cartera de mercado (base)
    portfolio_gain: str          # market_value − coste (nominal, sin IPC)
    net_worth_change: str | None  # vs snapshot del mes anterior, o null si no hay
    currency: str = "EUR"


class ReadinessItemOut(BaseModel):
    key: str
    label: str
    status: str        # ok | stale | missing
    detail: str = ""
    cta_route: str | None = None


class ReadinessOut(BaseModel):
    month: str
    items: list[ReadinessItemOut]
    ready: bool                 # todos los items en ok → cierre completo habilitado
    snapshot_exists: bool
    snapshot_state: str | None  # complete | partial | null


class SnapshotOut(BaseModel):
    id: str
    month: str
    snapshot_date: str
    total_assets: str
    total_liabilities: str
    net_worth: str
    data_state: str
    missing_items: list[str] = []
    currency: str = "EUR"
    created_at: str


class SnapshotCreate(BaseModel):
    month: str
    force_partial: bool = False
