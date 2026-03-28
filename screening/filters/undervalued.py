"""Undervaluation signal filter."""

import pandas as pd

from screening.filters.base import Filter
from screening.scorers._utils import safe_float


class UndervaluedFilter(Filter):
  """Keep stocks with enough undervaluation signals."""

  def __init__(self, min_signals: int = 2):
    self._min = min_signals

  def apply(self, df: pd.DataFrame) -> pd.DataFrame:
    scores = df.apply(self._count, axis=1)
    return df[scores >= self._min].copy()

  @staticmethod
  def _count(row: pd.Series) -> int:
    n = 0
    pe = safe_float(row.get('pe_ratio'))
    if pe is not None and 0 < pe <= 10:
      n += 1

    pct = safe_float(row.get('pct_from_52w_high'))
    if pct is not None and pct <= -20:
      n += 1

    fcf = safe_float(row.get('fcf_yield'))
    if fcf is not None and fcf > 0.05:
      n += 1

    pe_avg = safe_float(row.get('pe_avg_5y'))
    if (pe is not None and pe_avg is not None
        and pe_avg > 0 and pe < pe_avg * 0.7):
      n += 1

    return n
