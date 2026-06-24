from fastapi import APIRouter

from app.modules.market_data.router import get_quotes
from app.modules.market_data.schemas import QuoteOut

router = APIRouter()


@router.get("/quotes", response_model=list[QuoteOut])
def list_quotes(category: str | None = None):
    return get_quotes(category)
