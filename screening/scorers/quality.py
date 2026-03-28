"""Quality score — measures moat strength and growth."""

import pandas as pd

from screening.scorers._utils import safe_float


class QualityScorer:
  """Score 0-100: higher = stronger fundamentals."""

  def score(self, row: pd.Series) -> float:
    s = 0.0

    roic = safe_float(row.get('roic'))
    if roic is not None:
      if roic > 0.20:
        s += 25
      elif roic > 0.15:
        s += 20
      elif roic > 0.10:
        s += 14

    roe = safe_float(row.get('roe'))
    if roe is not None:
      if roe > 0.20:
        s += 25
      elif roe > 0.15:
        s += 20
      elif roe > 0.12:
        s += 14

    cagr = safe_float(row.get('revenue_cagr_3y'))
    if cagr is not None:
      if cagr > 0.15:
        s += 20
      elif cagr > 0.10:
        s += 15
      elif cagr > 0.05:
        s += 10

    dte = safe_float(row.get('debt_to_equity'))
    if dte is not None:
      if dte < 0.3:
        s += 15
      elif dte < 0.6:
        s += 12
      elif dte < 1.0:
        s += 8

    fcf_pos = row.get('fcf_positive_3y')
    if fcf_pos is True:
      s += 15

    return min(s, 100.0)
