from decimal import Decimal
from fastapi import HTTPException
from app.db.models.expense import ExpenseStatus, ExpenseCategory
from typing import List

class ExpenseRulesEngine:
    @staticmethod
    def validate_expense_transition(current: ExpenseStatus, requested: ExpenseStatus) -> None:
        valid = {
            ExpenseStatus.DRAFT: [ExpenseStatus.SUBMITTED],
            ExpenseStatus.SUBMITTED: [ExpenseStatus.MANAGER_APPROVED, ExpenseStatus.REJECTED],
            ExpenseStatus.MANAGER_APPROVED: [ExpenseStatus.FINANCE_APPROVED, ExpenseStatus.REJECTED],
            ExpenseStatus.FINANCE_APPROVED: [ExpenseStatus.SETTLED, ExpenseStatus.REJECTED],
            ExpenseStatus.REJECTED: [],
            ExpenseStatus.SETTLED: []
        }
        if requested not in valid.get(current, []):
            raise HTTPException(status_code=400, detail=f"Invalid expense transition: {current.value} -> {requested.value}")

    @staticmethod
    def validate_item_amounts(items: List[dict]) -> Decimal:
        total = Decimal('0.00')
        for item in items:
            amount = item.get("amount")
            if not isinstance(amount, Decimal):
                amount = Decimal(str(amount))
            if amount <= Decimal('0.00'):
                raise HTTPException(status_code=400, detail="Expense item amounts must be strictly positive")
            total += amount
        return total

    @staticmethod
    def validate_category_limits(amount: Decimal, category: ExpenseCategory) -> None:
        if not category.active_status:
            raise HTTPException(status_code=400, detail=f"Expense category '{category.name}' is inactive")
        if category.daily_limit and amount > category.daily_limit:
            raise HTTPException(status_code=400, detail=f"Amount exceeds daily limit for '{category.name}'")
        # In a real system, monthly limits require querying historical claims. For this rule, we validate the simple item threshold.
