"""Fear score — measures how much panic is priced into a stock."""

import pandas as pd

from screening.scorers._utils import safe_float


class FearScorer:
  """Score 0-100: higher = more fear/panic priced in."""

  def score(self, row: pd.Series) -> float:
    s = 0.0

    pct = safe_float(row.get('pct_from_52w_high'))
    if pct is not None:
      if pct <= -40:
        s += 30
      elif pct <= -30:
        s += 22
      elif pct <= -20:
        s += 15
      elif pct <= -10:
        s += 7

    pe = safe_float(row.get('pe_ratio'))
    pe_avg = safe_float(row.get('pe_avg_5y'))
    if pe is not None and pe_avg is not None and pe_avg > 0:
      ratio = pe / pe_avg
      if ratio < 0.5:
        s += 25
      elif ratio < 0.7:
        s += 18
      elif ratio < 0.85:
        s += 10

    fcf = safe_float(row.get('fcf_yield'))
    if fcf is not None:
      if fcf > 0.10:
        s += 20
      elif fcf > 0.07:
        s += 14
      elif fcf > 0.05:
        s += 8

    if pe is not None:
      if 0 < pe <= 8:
        s += 15
      elif 0 < pe <= 12:
        s += 8

    return min(s, 100.0)
