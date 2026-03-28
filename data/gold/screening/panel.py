"""
Screening panel builder.

Produces a wide panel with fundamental ratios for stock screening:
PE, PB, ROE, ROIC, FCF yield, margins, debt ratios, etc.

Unlike valuation/backtest panels (CFO-anchored, 3 metrics),
this panel uses all available metrics and computes derived ratios.
"""

from pathlib import Path
from typing import Optional

import pandas as pd

from data.gold.config.schemas import PanelSchema
from data.gold.core.base import BasePanelBuilder
from data.gold.transforms import calculate_market_cap
from data.gold.transforms import join_prices_pit

# Metrics we need for screening ratios.
_TTM_METRICS = [
    'REVENUE', 'NET_INCOME', 'EBIT', 'GROSS_PROFIT',
    'CFO', 'CAPEX',
]
_POINT_IN_TIME_METRICS = [
    'TOTAL_EQUITY', 'TOTAL_ASSETS', 'CURRENT_LIABILITIES',
    'TOTAL_DEBT', 'CASH', 'SHARES',
]
_ALL_METRICS = _TTM_METRICS + _POINT_IN_TIME_METRICS

# Schema is not strictly enforced here; we validate in tests.
_SCREENING_SCHEMA_NAME = 'screening_panel'


class ScreeningPanelBuilder(BasePanelBuilder):
  """
  Build screening panel with fundamental ratios.

  Primary key: (ticker, end) — latest filed version only.
  """

  REQUIRED_METRICS = _ALL_METRICS

  def __init__(
      self,
      silver_dir: Path,
      gold_dir: Path,
      min_date: Optional[str] = None,
  ):
    schema = PanelSchema(
        name=_SCREENING_SCHEMA_NAME,
        description='Screening panel with fundamental ratios',
        columns=[],
        primary_key=['ticker', 'end'],
    )
    super().__init__(silver_dir, gold_dir, schema, min_date)

  def build(self) -> pd.DataFrame:
    """Build screening panel."""
    companies, facts, prices = self._load_data()

    # Build quarterly + TTM for all metrics.
    metrics_q = self._build_quarterly_metrics(facts)

    # Pivot to wide: one row per (cik10, end), latest filed.
    wide = self._pivot_to_wide(metrics_q)

    # Join with company tickers.
    wide = wide.merge(
        companies[['cik10', 'ticker']],
        on='cik10', how='left',
    )
    wide = wide.dropna(subset=['ticker'])

    # Join prices (PIT: first price after filed date).
    panel = join_prices_pit(wide, prices, ticker_col='ticker')
    panel = calculate_market_cap(
        panel, shares_col='shares_q', price_col='price')
    panel = panel.drop(columns=['cik10'], errors='ignore')

    if self.min_date:
      panel = panel[panel['end'] >= self.min_date]

    # Compute derived ratios.
    panel = self._compute_ratios(panel)

    # Keep latest filed per (ticker, end).
    panel = panel.sort_values('filed')
    panel = panel.groupby(
        ['ticker', 'end'], as_index=False).tail(1)

    self.panel = panel.sort_values(
        ['ticker', 'end']).reset_index(drop=True)
    return self.panel

  def _build_wide_metrics(
      self, metrics_q: pd.DataFrame) -> pd.DataFrame:
    """Override: use our own pivot instead of CFO-anchored join."""
    return self._pivot_to_wide(metrics_q)

  def _pivot_to_wide(
      self, metrics_q: pd.DataFrame) -> pd.DataFrame:
    """
    Pivot metrics_q to wide format.

    For each (cik10, end), take the latest filed version of each
    metric and spread into columns.
    """
    if metrics_q.empty:
      return pd.DataFrame()

    relevant = metrics_q[
        metrics_q['metric'].isin(_ALL_METRICS)].copy()

    if relevant.empty:
      return pd.DataFrame()

    # For each (cik10, metric, end), keep latest filed.
    relevant = relevant.sort_values('filed')
    latest = relevant.groupby(
        ['cik10', 'metric', 'end'], as_index=False).tail(1)

    # Build column mapping: metric -> column names.
    col_map = {}
    for metric in _TTM_METRICS:
      col_map[metric] = {
          'q_val': f'{metric.lower()}_q',
          'ttm_val': f'{metric.lower()}_ttm',
      }
    for metric in _POINT_IN_TIME_METRICS:
      col_map[metric] = {
          'q_val': f'{metric.lower()}_q',
      }
    # Special case: SHARES stays as shares_q.
    col_map['SHARES'] = {'q_val': 'shares_q'}

    # Pivot each metric separately, then merge on (cik10, end).
    # Note: we merge WITHOUT filed to avoid row fragmentation when
    # different metrics have different filed dates for the same end
    # (e.g. amended filings 10-K/A).
    merge_cols = ['cik10', 'end']
    fiscal_cols = ['fiscal_year', 'fiscal_quarter']

    parts: list[pd.DataFrame] = []
    for metric in _ALL_METRICS:
      mdf = latest[latest['metric'] == metric].copy()
      if mdf.empty:
        continue

      rename = col_map.get(metric, {})
      keep_cols = list(merge_cols)
      if not parts:
        keep_cols += fiscal_cols

      for src, dst in rename.items():
        if src in mdf.columns:
          mdf = mdf.rename(columns={src: dst})
          keep_cols.append(dst)

      avail = [c for c in keep_cols if c in mdf.columns]
      parts.append(mdf[avail])

    if not parts:
      return pd.DataFrame()

    result = parts[0]
    for part in parts[1:]:
      on = [c for c in merge_cols if c in part.columns]
      result = result.merge(part, on=on, how='outer')

    # Add filed as max(filed) per (cik10, end) from the latest
    # values we already filtered.
    filed_per_end = (
        latest.groupby(['cik10', 'end'])['filed']
        .max()
        .reset_index())
    result = result.merge(
        filed_per_end, on=['cik10', 'end'], how='left')

    return result

  @staticmethod
  def _compute_ratios(panel: pd.DataFrame) -> pd.DataFrame:
    """Compute derived financial ratios."""
    df = panel.copy()

    mcap = df.get('market_cap')
    ni = df.get('net_income_ttm')
    equity = df.get('total_equity_q')
    assets = df.get('total_assets_q')
    cur_liab = df.get('current_liabilities_q')
    cash = df.get('cash_q')
    ebit = df.get('ebit_ttm')
    revenue = df.get('revenue_ttm')
    gp = df.get('gross_profit_ttm')
    cfo = df.get('cfo_ttm')
    capex = df.get('capex_ttm')
    debt = df.get('total_debt_q')

    # PE ratio = market_cap / net_income_ttm
    if mcap is not None and ni is not None:
      df['pe_ratio'] = mcap / ni.replace(0, pd.NA)
    else:
      df['pe_ratio'] = pd.NA

    # PB ratio = market_cap / total_equity
    if mcap is not None and equity is not None:
      df['pb_ratio'] = mcap / equity.replace(0, pd.NA)
    else:
      df['pb_ratio'] = pd.NA

    # ROE = net_income_ttm / total_equity
    if ni is not None and equity is not None:
      df['roe'] = ni / equity.replace(0, pd.NA)
    else:
      df['roe'] = pd.NA

    # ROIC = EBIT * (1 - tax_rate) / invested_capital
    # Approximate tax_rate = 0.25
    if (ebit is not None and assets is not None
        and cur_liab is not None):
      cash_s = cash if cash is not None else pd.Series(0, index=df.index)
      invested = assets - cur_liab - cash_s
      nopat = ebit * 0.75
      df['roic'] = nopat / invested.replace(0, pd.NA)
    else:
      df['roic'] = pd.NA

    # Debt to equity
    if debt is not None and equity is not None:
      df['debt_to_equity'] = debt / equity.replace(0, pd.NA)
    else:
      df['debt_to_equity'] = pd.NA

    # FCF yield = (CFO - CAPEX) / market_cap
    if cfo is not None and capex is not None and mcap is not None:
      fcf = cfo - capex
      df['fcf_yield'] = fcf / mcap.replace(0, pd.NA)
    else:
      df['fcf_yield'] = pd.NA

    # Operating margin = EBIT / Revenue
    if ebit is not None and revenue is not None:
      df['op_margin'] = ebit / revenue.replace(0, pd.NA)
    else:
      df['op_margin'] = pd.NA

    # Gross profit margin = GP / Revenue
    if gp is not None and revenue is not None:
      df['gp_margin'] = gp / revenue.replace(0, pd.NA)
    else:
      df['gp_margin'] = pd.NA

    return df
