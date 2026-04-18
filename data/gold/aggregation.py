"""
Gold layer aggregation logic.

Converts Silver layer facts (YTD values) into quarterly and TTM values
for model-ready panels.
"""

import logging

import pandas as pd

from data.silver.config.metric_catalog import METRIC_CATALOG

logger = logging.getLogger(__name__)


class YTDToQuarterlyConverter:
  """
  Convert YTD values to quarterly using PIT (Point-in-Time) logic.

  For each row, finds the previous quarter's YTD value that was filed before
  this row's filed date, then subtracts to get the quarterly value.
  """

  def convert(self, facts: pd.DataFrame) -> pd.DataFrame:
    """
    Convert YTD facts to quarterly values.

    Args:
      facts: DataFrame with columns [cik10, metric, end, filed, fy, fp,
             fiscal_year, fiscal_quarter, val]

    Returns:
      DataFrame with same structure but 'val' replaced by 'q_val'
    """
    if facts.empty:
      return pd.DataFrame()

    out_parts: list[pd.DataFrame] = []

    for metric, spec in METRIC_CATALOG.items():
      df = facts[facts['metric'] == metric].copy()
      if df.empty:
        continue

      expect_positive = bool(spec.get('abs', False))

      if bool(spec.get('is_ytd', False)):
        parts = []
        for cik10, g in df.groupby('cik10'):
          qg = self._ytd_to_quarter_pit(g)
          if not qg.empty:
            qg['cik10'] = cik10
            qg['metric'] = metric
            if expect_positive:
              qg = self._handle_negative_values(qg, metric, str(cik10))
            parts.append(qg)

        if parts:
          out_parts.append(pd.concat(parts, ignore_index=True))
      else:
        df = df.rename(columns={'val': 'q_val'})
        if expect_positive:
          df = self._handle_negative_values(df, metric, 'all')
        out_parts.append(df)

    if not out_parts:
      return pd.DataFrame()

    result = pd.concat(out_parts, ignore_index=True)
    result = result.sort_values(['cik10', 'metric',
                                 'end']).reset_index(drop=True)
    return result

  def _handle_negative_values(self, df: pd.DataFrame, metric: str,
                              cik10: str) -> pd.DataFrame:
    """
    Handle negative quarterly values for metrics that should be positive.

    When YTD_current < YTD_previous (due to restatement), q_val becomes
    negative. These values are unreliable, so we set them to NaN.
    """
    if df.empty:
      return df

    result = df.copy()
    negative_mask = result['q_val'] < 0

    if negative_mask.any():
      neg_count = int(negative_mask.sum())
      neg_rows = result.loc[negative_mask, ['end', 'filed', 'q_val']]
      sample = neg_rows.head(3).to_dict('records')
      logger.warning(
          '%s has %d negative q_val (YTD decreased). '
          'Setting to NaN. cik10=%s, sample=%s', metric, neg_count, cik10,
          sample)
      result.loc[negative_mask, 'q_val'] = pd.NA

    return result

  def _ytd_to_quarter_pit(self, df_ytd: pd.DataFrame) -> pd.DataFrame:
    """Convert YTD to quarterly for a single company using PIT logic."""
    if df_ytd.empty:
      return pd.DataFrame()

    df = df_ytd.copy()
    df = df.sort_values('filed')

    prev_fp_map = {'Q2': 'Q1', 'Q3': 'Q2', 'FY': 'Q3'}
    fp_to_fq = {'Q1': 'Q1', 'Q2': 'Q2', 'Q3': 'Q3', 'FY': 'Q4'}

    out_rows = []

    for _, row in df.iterrows():
      fp = str(row['fp'])
      fiscal_year = row['fiscal_year']
      filed = row['filed']
      ytd_val = float(row['val'])

      expected_fq = fp_to_fq.get(fp)
      if expected_fq and row.get('fiscal_quarter') != expected_fq:
        continue

      if fp == 'Q1':
        q_val = ytd_val
      elif fp in prev_fp_map:
        prev_q = prev_fp_map[fp]
        candidates = df[(df['fiscal_year'] == fiscal_year) &
                        (df['fp'] == prev_q) &
                        (df['fiscal_quarter'] == prev_q) &
                        (df['filed'] < filed)]

        if not candidates.empty:
          prev_row = candidates.sort_values('filed').iloc[-1]
          prev_ytd_val = float(prev_row['val'])
          q_val = ytd_val - prev_ytd_val
        else:
          q_val = ytd_val
      else:
        continue

      out_rows.append({
          'end': row['end'],
          'filed': row['filed'],
          'fy': row['fy'],
          'fp': 'Q4' if fp == 'FY' else fp,
          'fiscal_year': fiscal_year,
          'fiscal_quarter': expected_fq,
          'q_val': q_val,
          'tag': row['tag'],
      })

    return pd.DataFrame(out_rows)


class TTMCalculator:
  """
  Calculate TTM (Trailing Twelve Months) from quarterly values using PIT logic.

  For each row, sums the 4 quarters by fiscal_year/fiscal_quarter,
  using only values that were filed on or before the row's filed date.
  """

  def _get_prior_quarters(self, fy: int, fq: str) -> list[tuple[int, str]]:
    """Get the 4 quarters ending at (fy, fq)."""
    quarters = ['Q1', 'Q2', 'Q3', 'Q4']
    q_idx = quarters.index(fq)

    result = []
    for i in range(4):
      offset = q_idx - i
      if offset >= 0:
        result.append((fy, quarters[offset]))
      else:
        result.append((fy - 1, quarters[4 + offset]))

    return result

  def _calculate_group_ttm(self, group: pd.DataFrame) -> pd.Series:
    """Calculate TTM for a single (cik10, metric) group."""
    sorted_group = group.sort_values('filed')
    original_indices = sorted_group.index.tolist()

    quarter_history: dict[tuple[int, str], list[tuple[pd.Timestamp,
                                                      float]]] = {}
    ttm_values = []

    for _, row in sorted_group.iterrows():
      filed = row['filed']
      fy = row['fiscal_year']
      fq = row['fiscal_quarter']
      q_val = row['q_val']

      key = (fy, fq)
      if key not in quarter_history:
        quarter_history[key] = []
      quarter_history[key].append((filed, q_val))

      target_quarters = self._get_prior_quarters(fy, fq)

      q_vals = []
      for t_fy, t_fq in target_quarters:
        t_key = (t_fy, t_fq)
        if t_key in quarter_history:
          valid_vals = [(f, v) for f, v in quarter_history[t_key] if f <= filed]
          if valid_vals:
            _, latest_val = max(valid_vals, key=lambda x: x[0])
            q_vals.append(latest_val)

      if len(q_vals) == 4 and all(pd.notna(v) for v in q_vals):
        ttm_values.append(sum(q_vals))
      else:
        ttm_values.append(float('nan'))

    return pd.Series(ttm_values, index=original_indices, dtype='Float64')

  def calculate(self, quarterly: pd.DataFrame) -> pd.DataFrame:
    """
    Add TTM column to quarterly data.

    Args:
      quarterly: DataFrame with columns [cik10, metric, end, filed,
                 fiscal_year, fiscal_quarter, q_val, ...]

    Returns:
      Same DataFrame with 'ttm_val' column added
    """
    if quarterly.empty:
      return quarterly

    result = quarterly.copy()
    result = result.sort_values(
        ['cik10', 'metric', 'fiscal_year', 'fiscal_quarter', 'filed'])
    result = result.reset_index(drop=True)

    ttm_series_list = []
    for _, group in result.groupby(['cik10', 'metric'], sort=False):
      group_ttm = self._calculate_group_ttm(group)
      ttm_series_list.append(group_ttm)

    if ttm_series_list:
      result['ttm_val'] = pd.concat(ttm_series_list).sort_index()
    else:
      result['ttm_val'] = pd.NA

    return result


def build_quarterly_metrics(facts: pd.DataFrame) -> pd.DataFrame:
  """
  Build quarterly metrics from facts_long.

  Convenience function that combines YTD->Q conversion and TTM calculation.

  Args:
    facts: DataFrame from Silver facts_long.parquet

  Returns:
    DataFrame with columns [cik10, metric, end, filed, fy, fp,
                           fiscal_year, fiscal_quarter, q_val, ttm_val, tag]
  """
  converter = YTDToQuarterlyConverter()
  quarterly = converter.convert(facts)

  if quarterly.empty:
    return pd.DataFrame()

  calculator = TTMCalculator()
  with_ttm = calculator.calculate(quarterly)

  return with_ttm
