"""Growth and financial health signal filter."""

import pandas as pd

from screening.filters.base import Filter
from screening.scorers._utils import safe_float


class GrowthFilter(Filter):
  """Keep stocks with enough growth/health signals."""

  def __init__(self, min_signals: int = 1):
    self._min = min_signals

  def apply(self, df: pd.DataFrame) -> pd.DataFrame:
    scores = df.apply(self._count, axis=1)
    return df[scores >= self._min].copy()

  @staticmethod
  def _count(row: pd.Series) -> int:
    n = 0
    cagr = safe_float(row.get('revenue_cagr_3y'))
    if cagr is not None and cagr > 0.05:
      n += 1

    dte = safe_float(row.get('debt_to_equity'))
    if dte is not None and dte < 1.0:
      n += 1

    fcf_pos = row.get('fcf_positive_3y')
    if fcf_pos is True:
      n += 1

    return n
