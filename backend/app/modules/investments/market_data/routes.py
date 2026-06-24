from fastapi import APIRouter, HTTPException, status

from app.modules.investments.market_data.router import get_quotes, refresh_quotes
from app.modules.investments.market_data.schemas import QuoteOut

router = APIRouter()


@router.get("/quotes", response_model=list[QuoteOut])
def list_quotes(category: str | None = None):
    return get_quotes(category)


@router.post("/quotes/refresh", response_model=list[QuoteOut])
def refresh_market_quotes(category: str | None = None):
    quotes = refresh_quotes(category)
    if quotes is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya hay una actualización de mercados en curso",
        )
    return quotes
