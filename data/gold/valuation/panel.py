"""Valuation panel builder — latest version for current DCF.

Supports both US (SEC) and Korean (DART) data via market sources.
"""

import logging
from pathlib import Path
from typing import Optional

import pandas as pd

from data.gold.config.schemas import VALUATION_PANEL_SCHEMA
from data.gold.core.base import BasePanelBuilder
from data.gold.transforms import calculate_market_cap
from data.gold.transforms import join_prices_pit

logger = logging.getLogger(__name__)


class ValuationPanelBuilder(BasePanelBuilder):
  """
  Builds valuation panel with latest filed version only.

  Primary key: (ticker, end)
  """

  REQUIRED_METRICS = ['CFO', 'CAPEX', 'SHARES']

  # Additional metrics for normalized earnings policies.
  _EXTRA_TTM_METRICS = ['REVENUE', 'EBIT', 'NET_INCOME']
  _EXTRA_PIT_METRICS = [
      'TOTAL_ASSETS', 'TOTAL_EQUITY', 'CURRENT_LIABILITIES', 'CASH',
  ]

  def __init__(
      self,
      silver_dir: Path,
      gold_dir: Path,
      min_date: Optional[str] = None,
      markets: Optional[list[str]] = None,
  ):
    super().__init__(
        silver_dir, gold_dir, VALUATION_PANEL_SCHEMA,
        min_date, markets)

  def build(self) -> pd.DataFrame:
    """Build valuation panel with latest version per period."""
    companies, facts, prices = self._load_data()

    metrics_q = self._build_quarterly_metrics(facts)
    metrics_wide = self._build_wide_metrics(metrics_q)

    # Merge additional metrics (revenue, ebit, balance sheet).
    metrics_wide = self.merge_extra_metrics(
        metrics_q, metrics_wide)

    # Keep only latest filed version per (cik10, end)
    metrics_wide = metrics_wide.sort_values('filed')
    metrics_wide = metrics_wide.groupby(
        ['cik10', 'end'], as_index=False).tail(1)

    metrics_wide = metrics_wide.merge(
        companies[['cik10', 'ticker']],
        on='cik10',
        how='left',
    )
    metrics_wide = metrics_wide.dropna(subset=['ticker'])

    panel = join_prices_pit(
        metrics_wide, prices, ticker_col='ticker')
    panel = calculate_market_cap(panel)
    panel = panel.drop(columns=['cik10'], errors='ignore')

    if self.min_date:
      panel = panel[panel['end'] >= self.min_date]

    # Ensure all columns from schema exist (even if all NaN).
    for col in self.schema.column_names():
      if col not in panel.columns:
        panel[col] = pd.NA

    self.panel = panel.sort_values(
        ['ticker', 'end']).reset_index(drop=True)
    return self.panel

  def merge_extra_metrics(self, metrics_q: pd.DataFrame,
                          metrics_wide: pd.DataFrame) -> pd.DataFrame:
    """Merge revenue/EBIT/balance sheet metrics onto the wide panel.

    For TTM metrics (REVENUE, EBIT): takes ttm_val.
    For PIT metrics (TOTAL_ASSETS, etc.): takes q_val.
    Joins on (cik10, end) with the latest filed version per metric.
    """
    all_extra = self._EXTRA_TTM_METRICS + self._EXTRA_PIT_METRICS
    extra = metrics_q[metrics_q['metric'].isin(all_extra)].copy()
    if extra.empty:
      return metrics_wide

    # Keep latest filed per (cik10, metric, end).
    extra = extra.sort_values('filed')
    extra = extra.groupby(
        ['cik10', 'metric', 'end'], as_index=False).tail(1)

    # Pivot each metric into a column.
    for metric in self._EXTRA_TTM_METRICS:
      mdf = extra[extra['metric'] == metric]
      if mdf.empty:
        continue
      col_name = f'{metric.lower()}_ttm'
      mdf = mdf[['cik10', 'end', 'ttm_val']].rename(
          columns={'ttm_val': col_name})
      metrics_wide = metrics_wide.merge(
          mdf, on=['cik10', 'end'], how='left')

    for metric in self._EXTRA_PIT_METRICS:
      mdf = extra[extra['metric'] == metric]
      if mdf.empty:
        continue
      col_name = f'{metric.lower()}_q'
      mdf = mdf[['cik10', 'end', 'q_val']].rename(
          columns={'q_val': col_name})
      metrics_wide = metrics_wide.merge(
          mdf, on=['cik10', 'end'], how='left')

    return metrics_wide
