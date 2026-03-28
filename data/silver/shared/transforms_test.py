import pandas as pd

from data.silver.shared.transforms import _day_of_year
from data.silver.shared.transforms import FiscalQuarterCalculator
from data.silver.shared.transforms import FiscalYearCalculator
from data.silver.shared.transforms import TTMCalculator


class TestDayOfYear:

  def test_normal_dates(self):
    # Normal year (2001 is reference)
    assert _day_of_year(1, 1) == 1
    assert _day_of_year(12, 31) == 365

  def test_leap_year_feb29(self):
    # Feb 29 should map to Feb 28 in reference year
    # 2001 is not a leap year, so Feb 29 is invalid for it
    # The implementation clamps day to 28 for Feb
    assert _day_of_year(2, 29) == _day_of_year(2, 28)

  def test_invalid_dates(self):
    # Invalid day should be clamped
    # April 31 -> April 30 (which is day 120 in non-leap year)
    # April has 30 days. April 30 is day 31+28+31+30 = 120
    assert _day_of_year(4, 31) == 120

    # Feb 30 -> Feb 28 (day 59)
    assert _day_of_year(2, 30) == 59


class TestTTMCalculator:

  def test_calculate_simple(self):
    df = pd.DataFrame({
        'ticker': ['A'] * 5,
        'end':
            pd.to_datetime([
                '2020-03-31', '2020-06-30', '2020-09-30', '2020-12-31',
                '2021-03-31'
            ]),
        'value': [10.0, 20.0, 30.0, 40.0, 50.0]
    })

    calc = TTMCalculator()
    result = calc.calculate(df, 'value', ['ticker'], 'end')

    # First 3 should be NaN (window=4)
    assert pd.isna(result.iloc[0]['ttm_value'])
    assert pd.isna(result.iloc[1]['ttm_value'])
    assert pd.isna(result.iloc[2]['ttm_value'])

    # 4th element: 10+20+30+40 = 100
    assert result.iloc[3]['ttm_value'] == 100.0

    # 5th element: 20+30+40+50 = 140
    assert result.iloc[4]['ttm_value'] == 140.0

  def test_calculate_multiple_groups(self):
    # Create data for two tickers
    df = pd.DataFrame({
        'ticker': ['A'] * 4 + ['B'] * 4,
        'end':
            pd.to_datetime(
                ['2020-03-31', '2020-06-30', '2020-09-30', '2020-12-31'] * 2),
        'value': [1.0] * 4 + [2.0] * 4
    })

    calc = TTMCalculator()
    result = calc.calculate(df, 'value', ['ticker'], 'end')

    # Check A: 1+1+1+1 = 4
    assert result[result['ticker'] == 'A']['ttm_value'].iloc[-1] == 4.0
    # Check B: 2+2+2+2 = 8
    assert result[result['ticker'] == 'B']['ttm_value'].iloc[-1] == 8.0


class TestFiscalYearCalculator:

  def test_calculate_standard_fye(self):
    # FYE 1231
    facts = pd.DataFrame({
        'cik10': ['001', '001', '001'],
        'end': pd.to_datetime(['2020-12-31', '2020-06-30', '2021-01-01'])
    })
    companies = pd.DataFrame({'cik10': ['001'], 'fye_mmdd': ['1231']})

    calc = FiscalYearCalculator()
    result = calc.calculate(facts, companies)

    assert result.iloc[0]['fiscal_year'] == 2020  # On FYE
    assert result.iloc[1]['fiscal_year'] == 2020  # Before FYE
    assert result.iloc[2]['fiscal_year'] == 2021  # After FYE (next year)

  def test_calculate_midyear_fye(self):
    # FYE 0926 (Apple style)
    facts = pd.DataFrame({
        'cik10': ['002', '002', '002', '002'],
        'end':
            pd.to_datetime(
                ['2019-09-26', '2019-09-28', '2019-09-30', '2019-03-30'])
    })
    companies = pd.DataFrame({'cik10': ['002'], 'fye_mmdd': ['0926']})

    calc = FiscalYearCalculator()
    result = calc.calculate(facts, companies)

    # 2019-09-26 is FYE -> 2019
    assert result.iloc[0]['fiscal_year'] == 2019
    # 2019-09-28 is FYE+2 -> 2019 (within tolerance)
    assert result.iloc[1]['fiscal_year'] == 2019
    # 2019-09-30 is FYE+4 -> 2019 (still within tolerance?)
    # Let's check tolerance. Logic: if cur_doy <= fye_doy + 7 -> current year.
    # 0926 is day 269. 0930 is day 273. 273 <= 269+7 (276). Yes.
    assert result.iloc[2]['fiscal_year'] == 2019
    # 2019-03-30 is well before -> 2019
    assert result.iloc[3]['fiscal_year'] == 2019

  def test_calculate_tolerance_boundary(self):
    # FYE 0926
    facts = pd.DataFrame({
        'cik10': ['003', '003'],
        'end':
            pd.to_datetime(['2019-10-03', '2019-10-04'])  # +7 days, +8 days
    })
    companies = pd.DataFrame({'cik10': ['003'], 'fye_mmdd': ['0926']})

    calc = FiscalYearCalculator()
    result = calc.calculate(facts, companies)

    # 0926 (269) + 7 = 276 (Oct 3) -> Should be 2019
    assert result.iloc[0]['fiscal_year'] == 2019
    # 0926 (269) + 8 = 277 (Oct 4) -> Should be 2020
    assert result.iloc[1]['fiscal_year'] == 2020


class TestFiscalQuarterCalculator:

  def test_calculate_q4_match(self):
    # FYE 1231, End 1231
    df = pd.DataFrame({'cik10': ['001'], 'end': pd.to_datetime(['2020-12-31'])})
    fye_map = {'001': '1231'}

    calc = FiscalQuarterCalculator()
    result = calc.calculate(df, fye_map)

    assert result.iloc[0] == 'Q4'

  def test_calculate_q1_match(self):
    # FYE 1231 -> Q1 end is 0331
    df = pd.DataFrame({'cik10': ['001'], 'end': pd.to_datetime(['2020-03-31'])})
    fye_map = {'001': '1231'}

    calc = FiscalQuarterCalculator()
    result = calc.calculate(df, fye_map)

    assert result.iloc[0] == 'Q1'

  def test_calculate_tolerance(self):
    # FYE 1231 -> Q1 end 0331. Test 0407 (+7 days)
    df = pd.DataFrame({
        'cik10': ['001', '001'],
        'end': pd.to_datetime(['2020-04-07', '2020-04-08'])
    })
    fye_map = {'001': '1231'}

    calc = FiscalQuarterCalculator()
    result = calc.calculate(df, fye_map)

    assert result.iloc[0] == 'Q1'  # Within tolerance

    # 0408 is +8 days -> falls into Q2 bucket?
    # Q2 end is 0630. 0408 is closer to Q1 (0331) than Q2 (0630).
    # But logic falls back to relative position if not within tolerance.
    # It's definitely Q2 by time elapsed.
    assert result.iloc[1] == 'Q2'
