"""Moat existence filter — RATIONALE Tier 1 (ALL required)."""

import pandas as pd

from screening.filters.base import Filter
from screening.scorers._utils import safe_float


class MoatExistenceFilter(Filter):
  """Keep stocks that pass ALL Tier 1 moat existence checks.

  Tier 1 measures whether excess returns exist and persist:
  - ROIC 3Y avg > 10%
  - ROIC 3Y min > 7%
  - FCF/NI 3Y avg > 0.8

  ALL three must be satisfied. NaN on any metric = fail.
  """

  def apply(self, df: pd.DataFrame) -> pd.DataFrame:
    mask = df.apply(self._passes, axis=1)
    return df[mask].copy()

  @staticmethod
  def _passes(row: pd.Series) -> bool:
    roic_avg = safe_float(row.get('roic_3y_avg'))
    if roic_avg is None or roic_avg <= 0.10:
      return False

    roic_min = safe_float(row.get('roic_3y_min'))
    if roic_min is None or roic_min <= 0.07:
      return False

    fcf_ni = safe_float(row.get('fcf_ni_ratio_3y_avg'))
    if fcf_ni is None or fcf_ni <= 0.8:
      return False

    return True
