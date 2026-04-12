"""Moat score — measures economic moat strength and durability."""

import pandas as pd

from screening.scorers._utils import safe_float
from screening.scorers.base import Scorer


class MoatScorer(Scorer):
  """Score 0-100: higher = stronger economic moat.

  Components (aligned with RATIONALE Tier 1 + Tier 2):
  - ROIC 3Y avg        (0-25)
  - ROIC 3Y min        (0-15)
  - FCF/NI 3Y avg      (0-20)
  - Gross margin        (0-15)
  - Gross margin std 3Y (0-10, lower = better)
  - Debt-to-equity      (0-15, lower = better)
  """

  def score(self, row: pd.Series) -> float:
    s = 0.0

    roic_avg = safe_float(row.get('roic_3y_avg'))
    if roic_avg is not None:
      if roic_avg > 0.20:
        s += 25
      elif roic_avg > 0.15:
        s += 20
      elif roic_avg > 0.10:
        s += 14

    roic_min = safe_float(row.get('roic_3y_min'))
    if roic_min is not None:
      if roic_min > 0.15:
        s += 15
      elif roic_min > 0.10:
        s += 12
      elif roic_min > 0.07:
        s += 8

    fcf_ni = safe_float(row.get('fcf_ni_ratio_3y_avg'))
    if fcf_ni is not None:
      if fcf_ni > 1.0:
        s += 20
      elif fcf_ni > 0.8:
        s += 14
      elif fcf_ni > 0.6:
        s += 8

    gp = safe_float(row.get('gp_margin'))
    if gp is not None:
      if gp > 0.50:
        s += 15
      elif gp > 0.40:
        s += 12
      elif gp > 0.30:
        s += 8

    gp_std = safe_float(row.get('gp_margin_std_3y'))
    if gp_std is not None:
      if gp_std < 0.02:
        s += 10
      elif gp_std < 0.05:
        s += 7
      elif gp_std < 0.08:
        s += 3

    dte = safe_float(row.get('debt_to_equity'))
    if dte is not None:
      if dte < 0.3:
        s += 15
      elif dte < 0.6:
        s += 12
      elif dte < 1.0:
        s += 8

    return min(s, 100.0)
