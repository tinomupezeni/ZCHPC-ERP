# utils.py
def convert_currency(amount, from_currency, to_currency, rates):
    """
    Convert amount from one currency to another using provided rates dict.
    Example rates: {'USD': 1, 'ZWL': 0.012} -> ZWL to USD = amount * 0.012
    """
    if from_currency == to_currency:
        return amount
    return amount * rates[to_currency] / rates[from_currency]
