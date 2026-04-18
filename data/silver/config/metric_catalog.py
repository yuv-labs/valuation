"""
Market-agnostic metric catalog.

Defines aggregation behavior (is_ytd, abs) for each standard metric,
independent of any market's source-specific extraction rules.

Gold layer aggregation uses this catalog to determine how to convert
YTD values to quarterly and how to handle sign conventions.
"""

METRIC_CATALOG: dict[str, dict] = {
    'CFO': {'is_ytd': True, 'abs': False},
    'CAPEX': {'is_ytd': True, 'abs': True},
    'SHARES': {'is_ytd': False, 'abs': False},
    'REVENUE': {'is_ytd': True, 'abs': False},
    'NET_INCOME': {'is_ytd': True, 'abs': False},
    'EBIT': {'is_ytd': True, 'abs': False},
    'GROSS_PROFIT': {'is_ytd': True, 'abs': False},
    'TOTAL_EQUITY': {'is_ytd': False, 'abs': False},
    'TOTAL_ASSETS': {'is_ytd': False, 'abs': False},
    'CURRENT_LIABILITIES': {'is_ytd': False, 'abs': False},
    'TOTAL_DEBT': {'is_ytd': False, 'abs': False},
    'CASH': {'is_ytd': False, 'abs': False},
}
