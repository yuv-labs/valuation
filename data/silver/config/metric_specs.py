"""
Metric specifications.

Defines which minimal facts we extract from SEC companyfacts for Silver.

Metrics fall into two groups:
- Valuation metrics (CFO, CAPEX, SHARES): used by DCF engine.
- Screening metrics (REVENUE, NET_INCOME, etc.): used by screening panel.

The extractor iterates over all specs automatically — adding a metric here
is sufficient to have it extracted, with no pipeline code changes needed.
"""

METRIC_SPECS = {
    'CFO': {
        'namespace': 'us-gaap',
        'tags': [
            'NetCashProvidedByUsedInOperatingActivities',
            'NetCashProvidedByUsedInOperatingActivitiesContinuingOperations',
        ],
        'unit': 'USD',
        'is_ytd': True,
        'abs': False,
    },
    'CAPEX': {
        'namespace': 'us-gaap',
        'tags': [
            'PaymentsToAcquirePropertyPlantAndEquipment',
            'CapitalExpenditures',
            'PaymentsToAcquireProductiveAssets',
            'PaymentsToAcquireOtherProductiveAssets',
            'PaymentsToAcquireMachineryAndEquipment',
            'PaymentsToAcquireOilAndGasPropertyAndEquipment',
        ],
        'unit': 'USD',
        'is_ytd': True,
        'abs': True,
    },
    'SHARES': {
        'namespace': 'us-gaap',
        'tags': [
            'WeightedAverageNumberOfDilutedSharesOutstanding',
            'WeightedAverageNumberOfSharesOutstandingDiluted',
            'CommonStockSharesOutstanding',
            'WeightedAverageNumberOfSharesOutstandingBasic',
        ],
        'unit': 'shares',
        'is_ytd': False,
        'abs': False,
        'normalize_to_actual_count': True,
    },
    # -- Screening metrics (income statement, YTD) --
    'REVENUE': {
        'namespace': 'us-gaap',
        'tags': [
            'Revenues',
            'RevenueFromContractWithCustomerExcludingAssessedTax',
            'SalesRevenueNet',
            'SalesRevenueGoodsNet',
        ],
        'unit': 'USD',
        'is_ytd': True,
        'abs': False,
    },
    'NET_INCOME': {
        'namespace': 'us-gaap',
        'tags': [
            'NetIncomeLoss',
            'ProfitLoss',
        ],
        'unit': 'USD',
        'is_ytd': True,
        'abs': False,
    },
    'EBIT': {
        'namespace': 'us-gaap',
        'tags': [
            'OperatingIncomeLoss',
        ],
        'unit': 'USD',
        'is_ytd': True,
        'abs': False,
    },
    'GROSS_PROFIT': {
        'namespace': 'us-gaap',
        'tags': [
            'GrossProfit',
        ],
        'unit': 'USD',
        'is_ytd': True,
        'abs': False,
    },
    # -- Screening metrics (balance sheet, point-in-time) --
    'TOTAL_EQUITY': {
        'namespace': 'us-gaap',
        'tags': [
            'StockholdersEquity',
            'StockholdersEquityIncludingPortion'
            'AttributableToNoncontrollingInterest',
        ],
        'unit': 'USD',
        'is_ytd': False,
        'abs': False,
    },
    'TOTAL_ASSETS': {
        'namespace': 'us-gaap',
        'tags': [
            'Assets',
        ],
        'unit': 'USD',
        'is_ytd': False,
        'abs': False,
    },
    'CURRENT_LIABILITIES': {
        'namespace': 'us-gaap',
        'tags': [
            'LiabilitiesCurrent',
        ],
        'unit': 'USD',
        'is_ytd': False,
        'abs': False,
    },
    'TOTAL_DEBT': {
        'namespace': 'us-gaap',
        'tags': [
            'LongTermDebt',
            'LongTermDebtAndCapitalLeaseObligations',
            'LongTermDebtNoncurrent',
            'DebtAndCapitalLeaseObligations',
        ],
        'unit': 'USD',
        'is_ytd': False,
        'abs': False,
    },
    'CASH': {
        'namespace': 'us-gaap',
        'tags': [
            'CashAndCashEquivalentsAtCarryingValue',
            'CashCashEquivalentsAndShortTermInvestments',
        ],
        'unit': 'USD',
        'is_ytd': False,
        'abs': False,
    },
}
