"""Economic moat signal filter."""

import pandas as pd

from screening.filters.base import Filter
from screening.scorers._utils import safe_float


class MoatFilter(Filter):
  """Keep stocks with enough moat/quality signals."""

  def __init__(self, min_signals: int = 2):
    self._min = min_signals

  def apply(self, df: pd.DataFrame) -> pd.DataFrame:
    scores = df.apply(self._count, axis=1)
    return df[scores >= self._min].copy()

  @staticmethod
  def _count(row: pd.Series) -> int:
    n = 0
    roic = safe_float(row.get('roic'))
    if roic is not None and roic > 0.10:
      n += 1

    roe = safe_float(row.get('roe'))
    if roe is not None and roe > 0.12:
      n += 1

    op = safe_float(row.get('op_margin'))
    if op is not None and op > 0.15:
      n += 1

    gp_std = safe_float(row.get('gp_margin_std_3y'))
    if gp_std is not None and gp_std < 0.05:
      n += 1

    return n
