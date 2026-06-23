from pydantic import BaseModel


class CategorySpending(BaseModel):
    category_id: str | None
    category: str
    amount: str
    percentage: float


class OverviewOut(BaseModel):
    net_worth: str
    liquidity: str
    investments: str
    monthly_income: str
    monthly_expense: str
    monthly_savings: str
    savings_rate: float
    currency: str


class SpendingOut(BaseModel):
    month: str
    total_expense: str
    total_income: str
    by_category: list[CategorySpending]
