from decimal import Decimal, ROUND_HALF_UP

class PayrollRulesEngine:
    @staticmethod
    def calculate_lop_deduction(gross_salary: Decimal, scheduled_working_days: int, lop_days: int) -> Decimal:
        if scheduled_working_days <= 0:
            return Decimal('0.00')
        if lop_days <= 0:
            return Decimal('0.00')
            
        daily_rate = gross_salary / Decimal(scheduled_working_days)
        deduction = daily_rate * Decimal(lop_days)
        return deduction.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    @staticmethod
    def calculate_net_pay(gross_earnings: Decimal, total_deductions: Decimal) -> Decimal:
        net = gross_earnings - total_deductions
        if net < Decimal('0.00'):
            return Decimal('0.00')
        return net.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
