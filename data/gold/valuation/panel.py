"""Valuation panel builder — latest version for current DCF."""

from pathlib import Path
from typing import Optional

import pandas as pd

from data.gold.config.schemas import VALUATION_PANEL_SCHEMA
from data.gold.core.base import BasePanelBuilder
from data.gold.transforms import calculate_market_cap
from data.gold.transforms import join_prices_pit


class ValuationPanelBuilder(BasePanelBuilder):
  """
  Builds valuation panel with latest filed version only.

  Primary key: (ticker, end)
  """

  REQUIRED_METRICS = ['CFO', 'CAPEX', 'SHARES']

  def __init__(
      self,
      silver_dir: Path,
      gold_dir: Path,
      min_date: Optional[str] = None,
  ):
    super().__init__(
        silver_dir, gold_dir, VALUATION_PANEL_SCHEMA, min_date)

  def build(self) -> pd.DataFrame:
    """Build valuation panel with latest version per period."""
    companies, facts, prices = self._load_data()

    metrics_q = self._build_quarterly_metrics(facts)
    metrics_wide = self._build_wide_metrics(metrics_q)

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

    self.panel = panel.sort_values(
        ['ticker', 'end']).reset_index(drop=True)
    return self.panel
