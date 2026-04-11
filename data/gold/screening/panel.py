"""
Screening panel builder.

Produces a wide panel with fundamental ratios for stock screening:
PE, PB, ROE, ROIC, FCF yield, margins, debt ratios, etc.

Unlike valuation/backtest panels (CFO-anchored, 3 metrics),
this panel uses all available metrics and computes derived ratios.
"""

import logging
from pathlib import Path
from typing import Optional

import pandas as pd

from data.gold.config.schemas import PanelSchema
from data.gold.core.base import BasePanelBuilder
from data.gold.transforms import calculate_market_cap
from data.gold.transforms import join_prices_pit

logger = logging.getLogger(__name__)

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
      markets: Optional[list[str]] = None,
  ):
    schema = PanelSchema(
        name=_SCREENING_SCHEMA_NAME,
        description='Screening panel with fundamental ratios',
        columns=[],
        primary_key=['ticker', 'end'],
    )
    super().__init__(
        silver_dir, gold_dir, schema, min_date, markets)

  def build(self) -> pd.DataFrame:
    """Build screening panel (US + optionally KR)."""
    companies, facts, prices = self._load_data()

    # Build quarterly + TTM for all metrics.
    metrics_q = self._build_quarterly_metrics(facts)

    # For Korean annual-only data, TTM is missing because
    # there are no Q1-Q3 filings. Use q_val as ttm_val.
    if 'ttm_val' in metrics_q.columns:
      annual_mask = (
          metrics_q['ttm_val'].isna()
          & metrics_q['fiscal_quarter'].eq('Q4')
          & metrics_q['q_val'].notna())
      metrics_q.loc[annual_mask, 'ttm_val'] = (
          metrics_q.loc[annual_mask, 'q_val'])

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

    # For the latest period per ticker, override with the most
    # recent price so that screening PE/PB reflects current
    # market conditions (not the PIT price at filing date).
    panel = self._override_latest_price(panel, prices)

    panel = panel.drop(columns=['cik10'], errors='ignore')

    if self.min_date:
      panel = panel[panel['end'] >= self.min_date]

    # Compute derived ratios.
    panel = self._compute_ratios(panel)

    # Keep latest filed per (ticker, end).
    panel = panel.sort_values('filed')
    panel = panel.groupby(
        ['ticker', 'end'], as_index=False).tail(1)

    panel = panel.sort_values(
        ['ticker', 'end']).reset_index(drop=True)

    # Rolling metrics require deduplicated, sorted history.
    panel = self._compute_rolling_metrics(panel)
    panel = self._compute_price_metrics(panel, prices)

    self.panel = panel
    return self.panel


  def _build_wide_metrics(
      self, metrics_q: pd.DataFrame) -> pd.DataFrame:
    """Override: use our own pivot instead of CFO-anchored join."""
    return self._pivot_to_wide(metrics_q)

  @staticmethod
  def _override_latest_price(
      panel: pd.DataFrame,
      prices: pd.DataFrame,
  ) -> pd.DataFrame:
    """Replace price with most recent close for latest period."""
    if panel.empty or prices.empty:
      return panel

    panel = panel.copy()
    prices = prices.copy()
    prices['date'] = pd.to_datetime(prices['date'])

    # Normalize price ticker column.
    if 'symbol' in prices.columns:
      prices = prices.rename(columns={'symbol': 'ticker'})
    if 'ticker' in prices.columns:
      prices['ticker'] = (
          prices['ticker'].str.replace('.US', '', regex=False))

    # Get latest price per ticker.
    latest_prices = (
        prices.sort_values('date')
        .groupby('ticker', as_index=False)
        .tail(1)[['ticker', 'date', 'close']]
        .rename(columns={'close': 'latest_price',
                         'date': 'latest_date'}))

    # Identify latest period per ticker in panel.
    latest_end = (
        panel.groupby('ticker')['end']
        .max().reset_index()
        .rename(columns={'end': 'max_end'}))

    panel = panel.merge(latest_end, on='ticker', how='left')
    panel = panel.merge(latest_prices, on='ticker', how='left')

    is_latest = panel['end'] == panel['max_end']
    has_price = panel['latest_price'].notna()
    mask = is_latest & has_price

    panel.loc[mask, 'price'] = panel.loc[mask, 'latest_price']
    if 'shares_q' in panel.columns:
      panel.loc[mask, 'market_cap'] = (
          panel.loc[mask, 'latest_price']
          * panel.loc[mask, 'shares_q'])

    panel = panel.drop(
        columns=['max_end', 'latest_price', 'latest_date'],
        errors='ignore')
    return panel

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

  @staticmethod
  def _compute_rolling_metrics(
      panel: pd.DataFrame,
  ) -> pd.DataFrame:
    """Compute rolling multi-year metrics per ticker.

    Requires panel sorted by (ticker, end) with single-period
    ratios already computed.
    """
    df = panel.copy()
    df['_year'] = df['end'].dt.year

    # Take last row per (ticker, year) for annual snapshots.
    annual = (
        df.sort_values('end')
        .groupby(['ticker', '_year'], as_index=False)
        .tail(1)
        .set_index(['ticker', '_year'])
    )

    # --- Per-ticker annual rolling stats ---
    grouped = annual.groupby('ticker')

    # ROIC 3Y: avg and min
    roic_3y_avg = grouped['roic'].transform(
        lambda s: s.rolling(3, min_periods=3).mean())
    roic_3y_min = grouped['roic'].transform(
        lambda s: s.rolling(3, min_periods=3).min())

    # Gross margin std 3Y
    gp_margin_std_3y = grouped['gp_margin'].transform(
        lambda s: s.rolling(3, min_periods=3).std())

    # PE avg 5Y (min 3 years if insufficient history)
    pe_avg_5y = grouped['pe_ratio'].transform(
        lambda s: s.rolling(5, min_periods=3).mean())

    # FCF = CFO - CAPEX
    for col in ('cfo_ttm', 'capex_ttm', 'net_income_ttm', 'revenue_ttm'):
      if col not in annual.columns:
        raise ValueError(
            f'Missing required column {col!r} in panel. '
            'Ensure _compute_ratios ran before _compute_rolling_metrics.')
    fcf_annual = annual['cfo_ttm'] - annual['capex_ttm']

    # FCF positive 3Y: all 3 years positive
    fcf_positive_3y = fcf_annual.groupby('ticker').transform(
        lambda s: s.rolling(3, min_periods=3).apply(
            lambda w: float(all(v > 0 for v in w)),
            raw=True))

    # FCF/NI ratio 3Y avg: exclude years where NI <= 0.
    ni_annual = annual['net_income_ttm']
    fcf_ni_raw = fcf_annual / ni_annual.replace(0, pd.NA)
    # Mask rows where NI <= 0.
    fcf_ni_raw = fcf_ni_raw.where(ni_annual > 0)
    fcf_ni_ratio_3y_avg = fcf_ni_raw.groupby('ticker').transform(
        lambda s: s.rolling(3, min_periods=2).mean())

    # Revenue CAGR 3Y
    revenue_annual = annual['revenue_ttm']
    revenue_3y_ago = revenue_annual.groupby('ticker').shift(3)
    revenue_cagr_3y = (
        (revenue_annual / revenue_3y_ago.replace(0, pd.NA))
        ** (1 / 3) - 1)

    # Assign back to annual index.
    annual['roic_3y_avg'] = roic_3y_avg
    annual['roic_3y_min'] = roic_3y_min
    annual['gp_margin_std_3y'] = gp_margin_std_3y
    annual['pe_avg_5y'] = pe_avg_5y
    annual['fcf_positive_3y'] = fcf_positive_3y.astype('boolean')
    annual['fcf_ni_ratio_3y_avg'] = fcf_ni_ratio_3y_avg
    annual['revenue_cagr_3y'] = revenue_cagr_3y

    # Map annual rolling metrics back to all panel rows.
    rolling_cols = [
        'roic_3y_avg', 'roic_3y_min', 'gp_margin_std_3y',
        'pe_avg_5y', 'fcf_positive_3y', 'fcf_ni_ratio_3y_avg',
        'revenue_cagr_3y',
    ]
    rolling_lookup = annual[rolling_cols].reset_index()
    df = df.merge(
        rolling_lookup, on=['ticker', '_year'], how='left')
    df = df.drop(columns=['_year'])

    return df

  @staticmethod
  def _compute_price_metrics(
      panel: pd.DataFrame,
      prices: pd.DataFrame,
  ) -> pd.DataFrame:
    """Compute 52-week high drawdown from price history."""
    if panel.empty or prices.empty:
      panel['pct_from_52w_high'] = pd.NA
      return panel

    prices = prices.copy()
    prices['date'] = pd.to_datetime(prices['date'])

    # Normalize ticker column.
    if 'symbol' in prices.columns:
      prices = prices.rename(columns={'symbol': 'ticker'})
    if 'ticker' in prices.columns:
      prices['ticker'] = (
          prices['ticker'].str.replace('.US', '', regex=False))

    # Use 'high' if available, otherwise 'close'.
    if 'high' in prices.columns:
      prices['_high'] = prices['high']
    else:
      prices['_high'] = prices['close']
    prices = prices[['ticker', 'date', 'close', '_high']].copy()
    prices = prices.sort_values(['ticker', 'date'])

    # 52-week (252 trading day) rolling max.
    prices['_52w_high'] = (
        prices.groupby('ticker')['_high']
        .transform(lambda s: s.rolling(252, min_periods=60).max()))

    # Latest price and 52w high per ticker.
    latest_prices = (
        prices.sort_values('date')
        .groupby('ticker', as_index=False)
        .tail(1)[['ticker', 'close', '_52w_high']]
        .rename(columns={'close': '_latest_close'}))

    df = panel.merge(latest_prices, on='ticker', how='left')

    # For the latest period per ticker, compute drawdown.
    latest_end = (
        df.groupby('ticker')['end']
        .max().reset_index()
        .rename(columns={'end': '_max_end'}))
    df = df.merge(latest_end, on='ticker', how='left')

    is_latest = df['end'] == df['_max_end']

    df['pct_from_52w_high'] = pd.NA
    if '_latest_close' in df.columns and '_52w_high' in df.columns:
      drawdown = (
          df['_latest_close'] / df['_52w_high'].replace(0, pd.NA)
      ) - 1
      df.loc[is_latest, 'pct_from_52w_high'] = (
          drawdown[is_latest])

    df = df.drop(
        columns=['_max_end', '_52w_high', '_latest_close'],
        errors='ignore')
    return df
