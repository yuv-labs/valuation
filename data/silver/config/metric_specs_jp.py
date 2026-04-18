"""
Japanese metric specifications for EDINET XBRL.

Maps standardized metric names to EDINET XBRL tags across three
taxonomy families:
- jpcrp_cor: 有価証券報告書 (Annual Securities Report) — business summary
- jpigp_cor: IFRS連結 (IFRS consolidated financial statements)
- jppfs_cor: J-GAAP個別/連結 (J-GAAP individual/consolidated FS)

Tags are listed in priority order: jpcrp_cor SummaryOfBusinessResults
tags are preferred because they carry consolidated figures for both
IFRS and J-GAAP filers in a uniform structure.
"""

# pylint: disable=line-too-long
METRIC_SPECS_JP: dict[str, dict] = {
    'CFO': {
        'taxonomies': {
            'jpcrp_cor': [
                'CashFlowsFromUsedInOperatingActivitiesIFRSSummaryOfBusinessResults',
                'CashFlowsFromUsedInOperatingActivitiesSummaryOfBusinessResults',
            ],
            'jpigp_cor': [
                'NetCashProvidedByUsedInOperatingActivitiesIFRS',
            ],
            'jppfs_cor': [
                'CashAndCashEquivalentsIncreaseDecreaseFromOperatingActivities',
                'NetCashProvidedByUsedInOperatingActivities',
            ],
            'ifrs-full': [
                'CashFlowsFromUsedInOperatingActivities',
            ],
        },
        'unit': 'JPY',
        'is_ytd': True,
        'abs': False,
    },
    'CAPEX': {
        'taxonomies': {
            'jpcrp_cor': [
                'CapitalExpendituresOverviewOfCapitalExpendituresEtc',
            ],
            'jpigp_cor': [
                'PurchaseOfPropertyPlantAndEquipmentIFRS',
            ],
            'jppfs_cor': [
                'PurchaseOfPropertyPlantAndEquipmentAndIntangibleAssetsInvCF',
                'PurchaseOfPropertyPlantAndEquipmentInvCF',
            ],
            'ifrs-full': [
                'PurchaseOfPropertyPlantAndEquipment',
            ],
        },
        'unit': 'JPY',
        'is_ytd': True,
        'abs': True,
    },
    'SHARES': {
        'taxonomies': {
            'jpcrp_cor': [
                'TotalNumberOfIssuedSharesSummaryOfBusinessResults',
                'NumberOfSharesIssuedSharesVotingRights',
            ],
            'jppfs_cor': [
                'IssuedSharesTotalNumberOfSharesIssuedPerShareInformation',
                'TotalNumberOfIssuedShares',
            ],
            'jpigp_cor': [
                'NumberOfSharesIssued',
            ],
            'ifrs-full': [
                'NumberOfSharesIssued',
                'NumberOfSharesOutstanding',
            ],
        },
        'unit': 'shares',
        'is_ytd': False,
        'abs': False,
    },
    'REVENUE': {
        'taxonomies': {
            'jpcrp_cor': [
                'RevenueIFRSSummaryOfBusinessResults',
                'NetSalesSummaryOfBusinessResults',
                'OperatingRevenuesIFRSKeyFinancialData',
                'SalesAndFinancialServicesRevenueIFRSKeyFinancialData',
                'SalesRevenuesIFRS',
            ],
            'jpigp_cor': [
                'RevenueIFRS',
                'TotalNetRevenuesIFRS',
            ],
            'jppfs_cor': [
                'NetSales',
            ],
            'ifrs-full': [
                'Revenue',
            ],
        },
        'unit': 'JPY',
        'is_ytd': True,
        'abs': False,
    },
    'NET_INCOME': {
        'taxonomies': {
            'jpcrp_cor': [
                'ProfitLossAttributableToOwnersOfParentIFRSSummaryOfBusinessResults',
                'NetIncomeLossSummaryOfBusinessResults',
                'ProfitLossAttributableToOwnersOfParentSummaryOfBusinessResults',
            ],
            'jpigp_cor': [
                'ProfitLossAttributableToOwnersOfParentIFRS',
            ],
            'jppfs_cor': [
                'ProfitLossAttributableToOwnersOfParent',
                'NetIncome',
            ],
            'ifrs-full': [
                'ProfitLossAttributableToOwnersOfParent',
                'ProfitLoss',
            ],
        },
        'unit': 'JPY',
        'is_ytd': True,
        'abs': False,
    },
    'EBIT': {
        'taxonomies': {
            'jpcrp_cor': [
                'OperatingIncomeIFRSSummaryOfBusinessResults',
                'OrdinaryIncomeSummaryOfBusinessResults',
                'OperatingIncomeSummaryOfBusinessResults',
            ],
            'jpigp_cor': [
                'OperatingProfitLossIFRS',
                'OperatingIncomeIFRS',
            ],
            'jppfs_cor': [
                'OperatingIncome',
            ],
            'ifrs-full': [
                'ProfitLossFromOperatingActivities',
            ],
        },
        'unit': 'JPY',
        'is_ytd': True,
        'abs': False,
    },
    'GROSS_PROFIT': {
        'taxonomies': {
            'jpcrp_cor': [
                'GrossProfitIFRSSummaryOfBusinessResults',
                'GrossProfitSummaryOfBusinessResults',
            ],
            'jpigp_cor': [
                'GrossProfitIFRS',
            ],
            'jppfs_cor': [
                'GrossProfit',
            ],
            'ifrs-full': [
                'GrossProfit',
            ],
        },
        'unit': 'JPY',
        'is_ytd': True,
        'abs': False,
    },
    'TOTAL_EQUITY': {
        'taxonomies': {
            'jpcrp_cor': [
                'EquityAttributableToOwnersOfParentIFRSSummaryOfBusinessResults',
                'NetAssetsSummaryOfBusinessResults',
            ],
            'jpigp_cor': [
                'EquityAttributableToOwnersOfParentIFRS',
            ],
            'jppfs_cor': [
                'ShareholdersEquity',
                'NetAssets',
            ],
            'ifrs-full': [
                'EquityAttributableToOwnersOfParent',
                'Equity',
            ],
        },
        'unit': 'JPY',
        'is_ytd': False,
        'abs': False,
    },
    'TOTAL_ASSETS': {
        'taxonomies': {
            'jpcrp_cor': [
                'TotalAssetsIFRSSummaryOfBusinessResults',
                'TotalAssetsSummaryOfBusinessResults',
            ],
            'jpigp_cor': [
                'AssetsIFRS',
            ],
            'jppfs_cor': [
                'TotalAssets',
                'Assets',
            ],
            'ifrs-full': [
                'Assets',
            ],
        },
        'unit': 'JPY',
        'is_ytd': False,
        'abs': False,
    },
    'CURRENT_LIABILITIES': {
        'taxonomies': {
            'jpcrp_cor': [
                'CurrentLiabilitiesIFRSSummaryOfBusinessResults',
                'CurrentLiabilitiesSummaryOfBusinessResults',
            ],
            'jpigp_cor': [
                'TotalCurrentLiabilitiesIFRS',
                'CurrentLiabilitiesIFRS',
            ],
            'jppfs_cor': [
                'CurrentLiabilities',
            ],
            'ifrs-full': [
                'CurrentLiabilities',
            ],
        },
        'unit': 'JPY',
        'is_ytd': False,
        'abs': False,
    },
    'TOTAL_DEBT': {
        'taxonomies': {
            'jpcrp_cor': [
                'LongTermDebtIFRSSummaryOfBusinessResults',
                'LongTermDebtSummaryOfBusinessResults',
            ],
            'jpigp_cor': [
                'NonCurrentLabilitiesIFRS',  # Toyota uses this spelling
                'NonCurrentLiabilitiesIFRS',
                'NonCurrentFinancialLiabilitiesIFRS',
                'LongTermBorrowingsIFRS',
            ],
            'jppfs_cor': [
                'LongTermLoansPayable',
                'LongTermBorrowings',
            ],
            'ifrs-full': [
                'NoncurrentFinancialLiabilities',
            ],
        },
        'unit': 'JPY',
        'is_ytd': False,
        'abs': False,
    },
    'CASH': {
        'taxonomies': {
            'jpcrp_cor': [
                'CashAndCashEquivalentsIFRSSummaryOfBusinessResults',
                'CashAndDepositsSummaryOfBusinessResults',
            ],
            'jpigp_cor': [
                'CashAndCashEquivalentsIFRS',
            ],
            'jppfs_cor': [
                'CashAndDeposits',
                'CashAndCashEquivalents',
            ],
            'ifrs-full': [
                'CashAndCashEquivalents',
            ],
        },
        'unit': 'JPY',
        'is_ytd': False,
        'abs': False,
    },
    'RD': {
        'taxonomies': {
            'jpcrp_cor': [
                'ResearchAndDevelopmentExpensesSummaryOfBusinessResults',
            ],
            'jpigp_cor': [
                'ResearchAndDevelopmentExpenseIFRS',
            ],
            'jppfs_cor': [
                'ResearchAndDevelopmentCosts',
            ],
            'ifrs-full': [
                'ResearchAndDevelopmentExpense',
            ],
        },
        'unit': 'JPY',
        'is_ytd': True,
        'abs': False,
    },
    'DIVIDENDS_PAID': {
        'taxonomies': {
            'jpcrp_cor': [
                'CashDividendsPaidSummaryOfBusinessResults',
                'DividendsPaidSummaryOfBusinessResults',
            ],
            'jpigp_cor': [
                'DividendsPaidIFRS',
            ],
            'jppfs_cor': [
                'CashDividendsPaidFinCF',
            ],
            'ifrs-full': [
                'DividendsPaid',
            ],
        },
        'unit': 'JPY',
        'is_ytd': True,
        'abs': True,
    },
}
