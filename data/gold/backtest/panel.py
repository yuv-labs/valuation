"""Backtest panel builder — all filed versions for PIT analysis."""

from pathlib import Path
from typing import Optional

import pandas as pd

from data.gold.config.schemas import BACKTEST_PANEL_SCHEMA
from data.gold.core.base import BasePanelBuilder
from data.gold.transforms import calculate_market_cap
from data.gold.transforms import join_prices_pit
from data.gold.valuation.panel import ValuationPanelBuilder


class BacktestPanelBuilder(BasePanelBuilder):
  """
  Builds backtest panel with all filed versions for PIT analysis.

  Primary key: (ticker, end, filed)
  """

  REQUIRED_METRICS = ['CFO', 'CAPEX', 'SHARES']

  def __init__(
      self,
      silver_dir: Path,
      gold_dir: Path,
      min_date: Optional[str] = None,
      markets: Optional[list[str]] = None,
      preloaded_data=None,
  ):
    super().__init__(
        silver_dir, gold_dir, BACKTEST_PANEL_SCHEMA,
        min_date, markets, preloaded_data=preloaded_data)

  def build(self) -> pd.DataFrame:
    """Build backtest panel with all PIT versions."""
    companies, facts, prices = self._load_data()

    metrics_q = self._build_quarterly_metrics(facts)
    metrics_wide = self._build_wide_metrics(metrics_q)

    # Merge additional metrics (revenue, ebit, balance sheet).
    builder = ValuationPanelBuilder(self.silver_dir, self.gold_dir)
    metrics_wide = builder.merge_extra_metrics(
        metrics_q, metrics_wide)

    merge_cols = ['cik10', 'ticker']
    if 'market' in companies.columns:
      merge_cols.append('market')
    metrics_wide = metrics_wide.merge(
        companies[merge_cols],
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
        ['ticker', 'end', 'filed']).reset_index(drop=True)
    return self.panel
