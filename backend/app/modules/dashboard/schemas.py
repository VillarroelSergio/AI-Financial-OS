from pydantic import BaseModel


class CategorySpending(BaseModel):
    category_id: str | None
    category: str
    amount: str
    percentage: float


class CategoryTransaction(BaseModel):
    id: str
    date: str
    description: str
    account_name: str
    amount: str
    currency: str
    category: str
    type: str
    notes: str | None = None


class CategorySpendingDetailOut(BaseModel):
    category_id: str | None
    category: str
    period: str
    period_type: str
    total: str
    percentage: float
    transaction_count: int
    average_transaction: str
    transactions: list[CategoryTransaction]


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
    period_type: str = "month"
    total_expense: str
    total_income: str
    net_savings: str
    savings_rate: float
    transaction_count: int
    average_daily_expense: str
    by_category: list[CategorySpending]


class SpendingYearsOut(BaseModel):
    years: list[int]
