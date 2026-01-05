import pandas as pd

from data.silver.shared.transforms import FiscalQuarterCalculator
from data.silver.shared.transforms import FiscalYearCalculator
from data.silver.shared.transforms import TTMCalculator
from data.silver.shared.transforms import _day_of_year


class TestDayOfYear:
  """Tests for _day_of_year helper."""

  def test_leap_day_clamps_to_feb_28(self):
    """Feb 29 maps to Feb 28 in reference year."""
    assert _day_of_year(2, 29) == _day_of_year(2, 28)

  def test_march_first_day_of_year(self):
    """Non-leap year should have March 1 as day 60."""
    assert _day_of_year(3, 1) == 60


class TestTTMCalculator:
  """Tests for TTMCalculator."""

  def test_calculate_rolls_four_quarters_per_group(self):
    """Rolling sum is per group and respects sort order."""
    df = pd.DataFrame([
        {
            'cik10': '0001',
            'end': pd.Timestamp('2023-12-31'),
            'value': 40,
        },
        {
            'cik10': '0001',
            'end': pd.Timestamp('2023-03-31'),
            'value': 10,
        },
        {
            'cik10': '0001',
            'end': pd.Timestamp('2023-09-30'),
            'value': 30,
        },
        {
            'cik10': '0001',
            'end': pd.Timestamp('2024-03-31'),
            'value': 50,
        },
        {
            'cik10': '0001',
            'end': pd.Timestamp('2023-06-30'),
            'value': 20,
        },
        {
            'cik10': '0002',
            'end': pd.Timestamp('2023-03-31'),
            'value': 5,
        },
        {
            'cik10': '0002',
            'end': pd.Timestamp('2023-06-30'),
            'value': 5,
        },
        {
            'cik10': '0002',
            'end': pd.Timestamp('2023-09-30'),
            'value': 5,
        },
        {
            'cik10': '0002',
            'end': pd.Timestamp('2023-12-31'),
            'value': 5,
        },
    ])

    result = TTMCalculator().calculate(df, 'value', ['cik10'])

    group_a = result[result['cik10'] == '0001']
    group_b = result[result['cik10'] == '0002']

    ttm_a = group_a.sort_values('end')['ttm_value'].tolist()
    ttm_b = group_b.sort_values('end')['ttm_value'].tolist()

    assert pd.isna(ttm_a[0])
    assert pd.isna(ttm_a[1])
    assert pd.isna(ttm_a[2])
    assert ttm_a[3] == 100
    assert ttm_a[4] == 140

    assert pd.isna(ttm_b[0])
    assert pd.isna(ttm_b[1])
    assert pd.isna(ttm_b[2])
    assert ttm_b[3] == 20


class TestFiscalYearCalculator:
  """Tests for FiscalYearCalculator."""

  def test_calculate_handles_fye_tolerance_and_missing(self):
    """Fiscal year uses tolerance and defaults to calendar year."""
    facts = pd.DataFrame([
        {
            'cik10': '0001',
            'end': '2023-09-30',
        },
        {
            'cik10': '0001',
            'end': '2023-10-05',
        },
        {
            'cik10': '0001',
            'end': '2023-10-08',
        },
        {
            'cik10': '0001',
            'end': '2023-03-31',
        },
        {
            'cik10': '0002',
            'end': '2023-12-31',
        },
    ])
    companies = pd.DataFrame([
        {
            'cik10': '0001',
            'fye_mmdd': '0930',
        },
        {
            'cik10': '0002',
            'fye_mmdd': None,
        },
    ])

    result = FiscalYearCalculator().calculate(facts, companies)

    fy = result['fiscal_year'].tolist()
    assert fy == [2023, 2023, 2024, 2023, 2023]


class TestFiscalQuarterCalculator:
  """Tests for FiscalQuarterCalculator."""

  def test_calculate_quarter_boundaries_and_defaults(self):
    """Quarter calculation respects FYE boundaries and defaults."""
    df = pd.DataFrame([
        {
            'cik10': '0001',
            'end': pd.Timestamp('2023-12-30'),
        },
        {
            'cik10': '0001',
            'end': pd.Timestamp('2024-03-30'),
        },
        {
            'cik10': '0001',
            'end': pd.Timestamp('2024-06-30'),
        },
        {
            'cik10': '0001',
            'end': pd.Timestamp('2023-09-30'),
        },
        {
            'cik10': '0001',
            'end': pd.Timestamp('2023-11-15'),
        },
        {
            'cik10': '0002',
            'end': pd.Timestamp('2023-04-01'),
        },
    ])
    fye_map = {
        '0001': '0930',
        '0002': '6',
    }

    quarters = FiscalQuarterCalculator().calculate(df, fye_map).tolist()

    assert quarters == ['Q1', 'Q2', 'Q3', 'Q4', 'Q1', 'Q1']
