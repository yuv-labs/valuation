"""Opportunity filter — RATIONALE Track B (min 2 of 4)."""

import pandas as pd

from screening.filters.base import Filter
from screening.scorers._utils import safe_float


class OpportunityFilter(Filter):
  """Keep stocks with enough price-opportunity signals.

  Applied to Track A (moat universe) only:
  - PE < 70% of 5Y avg
  - 52W high drawdown <= -20%
  - FCF yield > 5%
  - Absolute PE < 10

  min_signals=2 out of 4. NaN signals are skipped (not counted).
  """

  def __init__(self, min_signals: int = 2):
    self._min = min_signals

  def apply(self, df: pd.DataFrame) -> pd.DataFrame:
    counts = df.apply(self._count, axis=1)
    return df[counts >= self._min].copy()

  @staticmethod
  def _count(row: pd.Series) -> int:
    n = 0

    pe = safe_float(row.get('pe_ratio'))
    pe_avg = safe_float(row.get('pe_avg_5y'))
    if (pe is not None and pe_avg is not None
        and pe_avg > 0 and pe < pe_avg * 0.70):
      n += 1

    pct = safe_float(row.get('pct_from_52w_high'))
    if pct is not None and pct <= -0.20:
      n += 1

    fcf_yield = safe_float(row.get('fcf_yield'))
    if fcf_yield is not None and fcf_yield > 0.05:
      n += 1

    if pe is not None and 0 < pe < 10:
      n += 1

    return n
