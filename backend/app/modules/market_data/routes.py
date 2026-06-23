from fastapi import APIRouter

from app.modules.market_data.schemas import QuoteOut
from app.modules.market_data.service import get_quotes

router = APIRouter()


@router.get("/quotes", response_model=list[QuoteOut])
def list_quotes(category: str | None = None):
    return get_quotes(category)
