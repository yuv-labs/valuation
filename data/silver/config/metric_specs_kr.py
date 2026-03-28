"""
Korean metric specifications for DART financial statements.

Maps metrics to Korean account names (account_nm) used in DART API.
Both IS (Income Statement) and CIS (Comprehensive Income Statement)
are searched, since some companies report only via CIS (e.g. NAVER).

Validated against: Samsung, SK Hynix, Hyundai, NAVER, Kakao, LG.

Known limitations:
- Financial companies (KB, Shinhan) are not available via DART API.
- account_nm varies across companies; fallback names are provided.
"""

METRIC_SPECS_KR = {
    # -- Income statement / CIS (YTD) --
    'REVENUE': {
        'sj_div': ['IS', 'CIS'],
        'account_names': [
            '매출액',
            '영업수익',
            '수익(매출액)',
        ],
        'unit': 'KRW',
        'is_ytd': True,
    },
    'NET_INCOME': {
        'sj_div': ['IS', 'CIS'],
        'account_names': [
            '당기순이익',
            '당기순이익(손실)',
        ],
        'unit': 'KRW',
        'is_ytd': True,
    },
    'EBIT': {
        'sj_div': ['IS', 'CIS'],
        'account_names': [
            '영업이익',
            '영업이익(손실)',
        ],
        'unit': 'KRW',
        'is_ytd': True,
    },
    'GROSS_PROFIT': {
        'sj_div': ['IS'],
        'account_names': [
            '매출총이익',
        ],
        'unit': 'KRW',
        'is_ytd': True,
    },
    # -- Cash flow statement (YTD) --
    'CFO': {
        'sj_div': ['CF'],
        'account_names': [
            '영업활동현금흐름',
            '영업활동으로인한현금흐름',
            '영업활동으로 인한 현금흐름',
        ],
        'unit': 'KRW',
        'is_ytd': True,
    },
    'CAPEX': {
        'sj_div': ['CF'],
        'account_names': [
            '유형자산의 취득',
        ],
        'unit': 'KRW',
        'is_ytd': True,
        'abs': True,
    },
    # -- Balance sheet (point-in-time) --
    'TOTAL_ASSETS': {
        'sj_div': ['BS'],
        'account_names': [
            '자산총계',
        ],
        'unit': 'KRW',
        'is_ytd': False,
    },
    'TOTAL_EQUITY': {
        'sj_div': ['BS'],
        'account_names': [
            '자본총계',
        ],
        'unit': 'KRW',
        'is_ytd': False,
    },
    'CURRENT_LIABILITIES': {
        'sj_div': ['BS'],
        'account_names': [
            '유동부채',
        ],
        'unit': 'KRW',
        'is_ytd': False,
    },
    'TOTAL_DEBT': {
        'sj_div': ['BS'],
        'account_names': [
            '장기차입금',
            '사채',
        ],
        'unit': 'KRW',
        'is_ytd': False,
    },
    'CASH': {
        'sj_div': ['BS'],
        'account_names': [
            '현금및현금성자산',
        ],
        'unit': 'KRW',
        'is_ytd': False,
    },
}
