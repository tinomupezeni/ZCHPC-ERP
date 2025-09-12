# payroll_utils.py
from decimal import Decimal

from .utils import convert_currency
from erp.models import TaxBracket
from django.utils import timezone

AIDS_LEVY_RATE = Decimal("0.03")  # 3%

def calculate_paye_and_aids(gross_income, currency='USD', rates=None):
    """
    Returns a dict with PAYE and AIDS levy in both currencies.
    gross_income: Decimal
    currency: 'USD' or 'ZWL'
    rates: {'USD': 1, 'ZWL': <rate_to_usd>}
    """
    if rates is None:
        rates = {'USD': 1, 'ZiG': 0.012}  # Example rate: ZiG -> USD

    # Convert all to USD for uniform calculation
    gross_usd = convert_currency(gross_income, currency, 'USD', rates)

    # Fetch active tax brackets in USD
    brackets = TaxBracket.objects.filter(currency='USD', active_from__lte=timezone.now()).order_by('min_income')

    paye_usd = Decimal("0")
    for bracket in brackets:
        if gross_usd > bracket.min_income:
            upper = bracket.max_income if bracket.max_income else gross_usd
            taxable_amount = min(gross_usd, upper) - bracket.min_income
            paye_usd += taxable_amount * bracket.rate - bracket.deduction

    paye_usd = max(paye_usd, 0)

    # AIDS levy 3% of gross
    aids_usd = gross_usd * AIDS_LEVY_RATE

    # Split back to original currency
    paye_original = convert_currency(paye_usd, 'USD', currency, rates)
    aids_original = convert_currency(aids_usd, 'USD', currency, rates)

    return {
        'gross_usd': gross_usd,
        'paye_usd': paye_usd,
        'aids_usd': aids_usd,
        'gross_original': gross_income,
        'paye_original': paye_original,
        'aids_original': aids_original,
    }
