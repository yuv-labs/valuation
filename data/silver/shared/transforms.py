"""
Shared transformation utilities.
"""
from calendar import monthrange
from datetime import date

import pandas as pd

# Non-leap year for consistent day-of-year calculations
_REFERENCE_YEAR = 2001


def _day_of_year(month: int, day: int) -> int:
  """Get day of year (1-366) for given month/day using a reference year."""
  # Clamp day to valid range for the month
  # Use actual days in month for clamping
  days_in_month = monthrange(_REFERENCE_YEAR, month)[1]
  # monthrange raises IllegalMonthError (ValueError) if month is invalid

  return date(_REFERENCE_YEAR, month, min(day,
                                          days_in_month)).timetuple().tm_yday


class TTMCalculator:
  """Calculate TTM (Trailing Twelve Months) values."""

  def calculate(self,
                df: pd.DataFrame,
                value_col: str,
                group_cols: list[str],
                sort_col: str = 'end') -> pd.DataFrame:
    """
    Calculate TTM by rolling 4-quarter sum.

    Args:
        df: Input dataframe
        value_col: Column to calculate TTM for
        group_cols: Columns to group by
        sort_col: Column to sort by (usually 'end')

    Returns:
        DataFrame with ttm_<value_col> column added
    """
    df = df.sort_values(group_cols + [sort_col])

    ttm_col = f'ttm_{value_col}'
    rolling_result = df.groupby(group_cols)[value_col].rolling(4).sum()
    df[ttm_col] = rolling_result.reset_index(level=list(range(len(group_cols))),
                                             drop=True)

    return df


class FiscalYearCalculator:
  """Calculate fiscal year from calendar dates."""

  def calculate(self, facts: pd.DataFrame,
                companies: pd.DataFrame) -> pd.DataFrame:
    """
    Add fiscal_year column based on fye_mmdd.

    Fiscal year is defined as the year when the fiscal period ends.
    For example, if FYE is Sep 26:
    - FY 2019 = period ending on 2019-09-26 (spans 2018-09-27 to 2019-09-26)
    - Dates on or before FYE belong to that calendar year's FY
    - Dates after FYE belong to next calendar year's FY

    A tolerance of ±7 days is applied to handle cases where the actual
    period end date is close to but not exactly on the FYE date
    (e.g., due to weekends or holidays).

    Examples with FYE = Sep 26 (0926):
    - 2019-03-30 (before 0926) → FY 2019
    - 2019-09-26 (on FYE)      → FY 2019
    - 2019-09-28 (within +7)   → FY 2019 (tolerance)
    - 2019-12-28 (after 0926)  → FY 2020

    Args:
        facts: Facts DataFrame with end dates
        companies: Companies DataFrame with fye_mmdd

    Returns:
        Facts DataFrame with fiscal_year column
    """
    facts = facts.copy()
    facts = facts.merge(companies[['cik10', 'fye_mmdd']],
                        on='cik10',
                        how='left')

    facts['end'] = pd.to_datetime(facts['end'])
    facts['year'] = facts['end'].dt.year
    facts['mmdd'] = facts['end'].dt.strftime('%m%d')

    def calc_fiscal_year(row):
      if pd.isna(row['fye_mmdd']):
        return row['year']

      fye_month = int(row['fye_mmdd'][:2])
      fye_day = int(row['fye_mmdd'][2:])
      cur_month = int(row['mmdd'][:2])
      cur_day = int(row['mmdd'][2:])

      fye_doy = _day_of_year(fye_month, fye_day)
      cur_doy = _day_of_year(cur_month, cur_day)

      # Within ±7 days of FYE, or before FYE → current year
      # After FYE (beyond tolerance) → next year
      tolerance = 7
      if cur_doy <= fye_doy + tolerance:
        return row['year']
      return row['year'] + 1

    facts['fiscal_year'] = facts.apply(calc_fiscal_year, axis=1)

    facts = facts.drop(columns=['fye_mmdd', 'year', 'mmdd'])
    return facts


class FiscalQuarterCalculator:
  """Calculate fiscal quarter from calendar dates based on FYE."""

  TOLERANCE = 7  # Days tolerance for quarter boundary matching

  def calculate(self, df: pd.DataFrame, fye_map: dict[str, str]) -> pd.Series:
    """
    Calculate fiscal_quarter based on end date and company's FYE.

    Each quarter end is ~3 months apart from FYE:
    - Q1 end: FYE + 3 months
    - Q2 end: FYE + 6 months
    - Q3 end: FYE + 9 months
    - Q4 end: FYE (fiscal year end)

    A tolerance of ±7 days is applied to handle cases where the actual
    period end date is close to but not exactly on the quarter end date.

    Args:
        df: DataFrame with 'cik10' and 'end' columns
        fye_map: Dict mapping cik10 to fye_mmdd (e.g., '0926' for Sep 26)

    Returns:
        Series with fiscal_quarter values (Q1, Q2, Q3, Q4)
    """

    def get_quarter_boundaries(fye_mmdd: str) -> list[int]:
      """Get day-of-year for each quarter end."""
      if not fye_mmdd or len(str(fye_mmdd)) < 4:
        fye_mmdd = '1231'  # Default to Dec 31

      fye_month = int(str(fye_mmdd)[:2])
      fye_day = int(str(fye_mmdd)[2:4])

      # Q4 end = FYE
      q4_doy = _day_of_year(fye_month, fye_day)

      # Quarter ends are ~3 months apart (wraparound for months > 12)
      def quarter_end_doy(months_after_fye: int) -> int:
        m = ((fye_month + months_after_fye - 1) % 12) + 1
        return _day_of_year(m, fye_day)

      q1_doy = quarter_end_doy(3)
      q2_doy = quarter_end_doy(6)
      q3_doy = quarter_end_doy(9)

      return [q1_doy, q2_doy, q3_doy, q4_doy]

    def calc_quarter(row: pd.Series) -> str:
      cik10 = row['cik10']
      end_date = row['end']

      fye_mmdd = fye_map.get(cik10) or '1231'
      boundaries = get_quarter_boundaries(fye_mmdd)
      q1_doy, q2_doy, q3_doy, q4_doy = boundaries

      cur_doy = _day_of_year(end_date.month, end_date.day)
      tolerance = self.TOLERANCE

      # Check which quarter end the date is closest to (within tolerance)
      if abs(cur_doy - q1_doy) <= tolerance:
        return 'Q1'
      if abs(cur_doy - q2_doy) <= tolerance:
        return 'Q2'
      if abs(cur_doy - q3_doy) <= tolerance:
        return 'Q3'
      if abs(cur_doy - q4_doy) <= tolerance:
        return 'Q4'

      # If not within tolerance of any boundary, determine by position
      # Normalize to fiscal year starting after Q4 end
      days_in_year = 365
      fy_start_doy = (q4_doy % days_in_year) + 1

      # Adjust cur_doy to be relative to FY start
      if cur_doy >= fy_start_doy:
        rel_doy = cur_doy - fy_start_doy
      else:
        rel_doy = (days_in_year - fy_start_doy) + cur_doy

      # Each quarter is ~91 days (365/4)
      quarter_len = days_in_year // 4
      quarter_num = (rel_doy // quarter_len) + 1
      quarter_num = min(quarter_num, 4)  # Cap at Q4

      return f'Q{quarter_num}'

    return df.apply(calc_quarter, axis=1)
