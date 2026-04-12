"""Moat health filter — RATIONALE Tier 2 (min 2 of available)."""

import pandas as pd

from screening.filters.base import Filter
from screening.scorers._utils import safe_float


class MoatHealthFilter(Filter):
  """Keep stocks with enough moat health/durability signals.

  Tier 2 assesses whether the moat is likely to persist:
  - Gross margin > 30%
  - Gross margin std 3Y < 5%
  - Debt-to-equity < 1.0
  - Capex/Depreciation < 1.5  (inactive until DEPRECIATION added)

  min_signals defaults to 2. With 3 active signals (no depreciation
  data), this is 2-of-3. When capex/depreciation is added (Phase 5),
  it becomes 2-of-4 automatically.
  """

  def __init__(self, min_signals: int = 2):
    self._min = min_signals

  def apply(self, df: pd.DataFrame) -> pd.DataFrame:
    counts = df.apply(self._count, axis=1)
    return df[counts >= self._min].copy()

  @staticmethod
  def _count(row: pd.Series) -> int:
    n = 0

    gp_margin = safe_float(row.get('gp_margin'))
    if gp_margin is not None and gp_margin > 0.30:
      n += 1

    gp_std = safe_float(row.get('gp_margin_std_3y'))
    if gp_std is not None and gp_std < 0.05:
      n += 1

    dte = safe_float(row.get('debt_to_equity'))
    if dte is not None and dte < 1.0:
      n += 1

    # Phase 5: uncomment when capex_depreciation_ratio is available.
    # capex_dep = safe_float(row.get('capex_depreciation_ratio'))
    # if capex_dep is not None and capex_dep < 1.5:
    #   n += 1

    return n
