from pydantic import BaseModel


class QuoteOut(BaseModel):
    symbol: str
    name: str
    category: str
    price: float | None
    change_pct: float | None
    currency: str
    sparkline: list[float]
    last_updated: str
    market_open: bool
