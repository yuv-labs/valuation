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
    'CFO', 'CAPEX', 'RD', 'DIVIDENDS_PAID',
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
      preloaded_data=None,
  ):
    schema = PanelSchema(
        name=_SCREENING_SCHEMA_NAME,
        description='Screening panel with fundamental ratios',
        columns=[],
        primary_key=['ticker', 'end'],
    )
    super().__init__(
        silver_dir, gold_dir, schema, min_date, markets,
        preloaded_data=preloaded_data)

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
    merge_cols = ['cik10', 'ticker']
    if 'market' in companies.columns:
      merge_cols.append('market')
    wide = wide.merge(
        companies[merge_cols],
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

    # Track classification + trust + quant scores + gates.
    panel = self._compute_track_signals(panel)
    panel = self._compute_trust_signals(panel)
    panel = self._compute_quant_scores(panel)
    panel = self._apply_gates(panel)

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
          prices['ticker'].str.replace(r'\.\w+$', '', regex=True))

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

    # ROA = net_income_ttm / total_assets
    if ni is not None and assets is not None:
      df['roa'] = ni / assets.replace(0, pd.NA)
    else:
      df['roa'] = pd.NA

    # R&D to revenue
    rd = df.get('rd_ttm')
    if rd is not None and revenue is not None:
      df['rd_to_revenue'] = rd / revenue.replace(0, pd.NA)
    else:
      df['rd_to_revenue'] = pd.NA

    # CFO to NI ratio
    if cfo is not None and ni is not None:
      df['cfo_to_ni_ratio'] = cfo / ni.replace(0, pd.NA)
    else:
      df['cfo_to_ni_ratio'] = pd.NA

    # Reinvestment rate = (capex + R&D) / CFO
    if capex is not None and cfo is not None:
      reinvest_num = capex.copy()
      if rd is not None:
        reinvest_num = reinvest_num + rd.fillna(0)
      df['reinvestment_rate'] = (
          reinvest_num / cfo.replace(0, pd.NA))
    else:
      df['reinvestment_rate'] = pd.NA

    # Has dividend
    div = df.get('dividends_paid_ttm')
    if div is not None:
      df['has_dividend'] = div > 0
    else:
      df['has_dividend'] = False

    # Debt to assets
    if debt is not None and assets is not None:
      df['debt_to_assets'] = debt / assets.replace(0, pd.NA)
    else:
      df['debt_to_assets'] = pd.NA

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

    # --- 5-year rolling metrics ---

    # ROIC 5Y avg and min
    roic_5y_avg = grouped['roic'].transform(
        lambda s: s.rolling(5, min_periods=5).mean())
    roic_5y_min = grouped['roic'].transform(
        lambda s: s.rolling(5, min_periods=5).min())

    # Revenue CAGR 5Y
    revenue_5y_ago = revenue_annual.groupby('ticker').shift(5)
    revenue_cagr_5y = (
        (revenue_annual / revenue_5y_ago.replace(0, pd.NA))
        ** (1 / 5) - 1)

    # Op margin trend 5Y: (current - 5y_ago) / 5
    op_margin_col = annual.get('op_margin')
    if op_margin_col is not None:
      op_5y_ago = op_margin_col.groupby('ticker').shift(5)
      op_margin_trend_5y = (op_margin_col - op_5y_ago) / 5
    else:
      op_margin_trend_5y = pd.Series(
          pd.NA, index=annual.index)

    # Reinvestment rate 5Y avg
    reinvest_col = annual.get('reinvestment_rate')
    if reinvest_col is not None:
      reinvestment_rate_5y_avg = reinvest_col.groupby(
          'ticker').transform(
          lambda s: s.rolling(5, min_periods=3).mean())
    else:
      reinvestment_rate_5y_avg = pd.Series(
          pd.NA, index=annual.index)

    # Shares 5Y change
    shares_col = annual.get('shares_q')
    if shares_col is not None:
      shares_5y_ago = shares_col.groupby('ticker').shift(5)
      shares_5y_change = (
          (shares_col / shares_5y_ago.replace(0, pd.NA)) - 1)
    else:
      shares_5y_change = pd.Series(pd.NA, index=annual.index)

    # ROIC trend: rising / stable / declining
    def _roic_trend(current, avg_5y):
      if pd.isna(current) or pd.isna(avg_5y) or avg_5y == 0:
        return pd.NA
      ratio = current / avg_5y
      if ratio > 1.1:
        return 'rising'
      if ratio < 0.9:
        return 'declining'
      return 'stable'

    roic_trend = pd.Series(
        [_roic_trend(c, a) for c, a in zip(
            annual['roic'], roic_5y_avg)],
        index=annual.index)

    # Assign back to annual index.
    annual['roic_3y_avg'] = roic_3y_avg
    annual['roic_3y_min'] = roic_3y_min
    annual['gp_margin_std_3y'] = gp_margin_std_3y
    annual['pe_avg_5y'] = pe_avg_5y
    annual['fcf_positive_3y'] = fcf_positive_3y.astype('boolean')
    annual['fcf_ni_ratio_3y_avg'] = fcf_ni_ratio_3y_avg
    annual['revenue_cagr_3y'] = revenue_cagr_3y
    annual['roic_5y_avg'] = roic_5y_avg
    annual['roic_5y_min'] = roic_5y_min
    annual['revenue_cagr_5y'] = revenue_cagr_5y
    annual['op_margin_trend_5y'] = op_margin_trend_5y
    annual['reinvestment_rate_5y_avg'] = reinvestment_rate_5y_avg
    annual['shares_5y_change'] = shares_5y_change
    annual['roic_trend'] = roic_trend

    # Map annual rolling metrics back to all panel rows.
    rolling_cols = [
        'roic_3y_avg', 'roic_3y_min', 'gp_margin_std_3y',
        'pe_avg_5y', 'fcf_positive_3y', 'fcf_ni_ratio_3y_avg',
        'revenue_cagr_3y',
        'roic_5y_avg', 'roic_5y_min', 'revenue_cagr_5y',
        'op_margin_trend_5y', 'reinvestment_rate_5y_avg',
        'shares_5y_change', 'roic_trend',
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
          prices['ticker'].str.replace(r'\.\w+$', '', regex=True))

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

  # ── Track classification thresholds (tunable) ──────────────

  _REINVEST_BUFFETT = 0.30
  _REINVEST_FISHER = 0.50
  _CAGR_BUFFETT = 0.08
  _CAGR_FISHER = 0.15

  # Fisher tier thresholds: (low, high) boundaries for 0/1/2.
  _FISHER_TIERS = {
      'revenue_cagr_5y': (0.05, 0.15, 3),
      'rd_to_revenue': (0.0, 0.05, 1),
      'op_margin': (0.05, 0.15, 3),
      'op_margin_trend_5y': (-0.001, 0.001, 2),
      'cfo_to_ni_ratio': (0.5, 1.0, 2),
  }
  _FISHER_MAX = sum(2 * w for _, _, w in _FISHER_TIERS.values())

  # Buffett tier thresholds.
  _BUFFETT_TIERS = {
      'fcf_yield': (0.03, 0.07, 3),
      'fcf_positive_3y': (0.5, 1.0, 2),
      'shares_5y_change': (0.01, -0.01, 2),
      'roic': (0.10, 0.25, 3),
      'debt_to_assets': (0.50, 0.30, 1),
  }
  _BUFFETT_MAX = sum(2 * w for _, _, w in _BUFFETT_TIERS.values())

  @staticmethod
  def _compute_track_signals(
      panel: pd.DataFrame,
  ) -> pd.DataFrame:
    """Assign buffett / fisher / mixed track label."""
    df = panel.copy()

    def _axis_a(trend):
      if pd.isna(trend):
        return pd.NA
      return 'fisher' if trend == 'rising' else 'buffett'

    def _axis_bc(val, lo, hi):
      if pd.isna(val):
        return pd.NA
      if val < lo:
        return 'buffett'
      if val > hi:
        return 'fisher'
      return 'mixed'

    df['axis_a_roic'] = df.get(
        'roic_trend', pd.Series(pd.NA, index=df.index)).map(
        _axis_a)

    reinvest = df.get(
        'reinvestment_rate_5y_avg',
        pd.Series(pd.NA, index=df.index))
    df['axis_b_reinvest'] = reinvest.apply(
        lambda v: _axis_bc(
            v,
            ScreeningPanelBuilder._REINVEST_BUFFETT,
            ScreeningPanelBuilder._REINVEST_FISHER))

    cagr = df.get(
        'revenue_cagr_5y',
        pd.Series(pd.NA, index=df.index))
    df['axis_c_growth'] = cagr.apply(
        lambda v: _axis_bc(
            v,
            ScreeningPanelBuilder._CAGR_BUFFETT,
            ScreeningPanelBuilder._CAGR_FISHER))

    def _composite(row):
      axes = [row.get('axis_a_roic'),
              row.get('axis_b_reinvest'),
              row.get('axis_c_growth')]
      axes = [a for a in axes if not pd.isna(a)]
      if not axes:
        return pd.NA
      n_b = sum(1 for a in axes if a == 'buffett')
      n_f = sum(1 for a in axes if a == 'fisher')
      if n_b >= 2 and n_f == 0:
        return 'buffett'
      if n_f >= 2 and n_b == 0:
        return 'fisher'
      return 'mixed'

    df['track_signal'] = df.apply(_composite, axis=1)
    return df

  @staticmethod
  def _compute_trust_signals(
      panel: pd.DataFrame,
  ) -> pd.DataFrame:
    """Compute 1-minute trust test scores."""
    df = panel.copy()
    roe = df.get('roe', pd.Series(pd.NA, index=df.index))
    roa = df.get('roa', pd.Series(pd.NA, index=df.index))
    cfo_ni = df.get(
        'cfo_to_ni_ratio', pd.Series(pd.NA, index=df.index))
    has_div = df.get(
        'has_dividend', pd.Series(False, index=df.index))

    df['trust_roe_pass'] = (roe >= 0.10).fillna(False)
    df['trust_roa_pass'] = (roa >= 0.07).fillna(False)
    df['trust_cfo_ni_pass'] = (cfo_ni >= 0.8).fillna(False)
    df['trust_dividend_exists'] = has_div.fillna(False)

    df['trust_score'] = (
        df['trust_roe_pass'].astype('int64')
        + df['trust_roa_pass'].astype('int64')
        + df['trust_cfo_ni_pass'].astype('int64')
        + df['trust_dividend_exists'].astype('int64'))

    return df

  @staticmethod
  def _tier_score(val, lo, hi, weight, inverted=False):
    """Score a value as 0/1/2 tier × weight."""
    if pd.isna(val):
      return 0
    if inverted:
      if val <= hi:
        return 2 * weight
      if val <= lo:
        return 1 * weight
      return 0
    if val >= hi:
      return 2 * weight
    if val >= lo:
      return 1 * weight
    return 0

  @staticmethod
  def _compute_quant_scores(
      panel: pd.DataFrame,
  ) -> pd.DataFrame:
    """Compute Fisher and Buffett tier-weighted scores."""
    df = panel.copy()
    ts = ScreeningPanelBuilder._tier_score

    # Fisher score
    fisher_scores = []
    for _, row in df.iterrows():
      s = 0
      for col, (lo, hi, w) in (
          ScreeningPanelBuilder._FISHER_TIERS.items()):
        s += ts(row.get(col), lo, hi, w)
      fisher_scores.append(s)
    df['fisher_quant_score'] = fisher_scores

    # Buffett score
    buffett_scores = []
    for _, row in df.iterrows():
      s = 0
      # fcf_yield: higher is better
      s += ts(row.get('fcf_yield'), 0.03, 0.07, 3)
      # fcf_positive_3y: True=1.0, False=0.0
      fcf_pos = row.get('fcf_positive_3y')
      if pd.isna(fcf_pos) or fcf_pos is None:
        fcf_val = 0.0
      else:
        fcf_val = 1.0 if fcf_pos else 0.0
      s += ts(fcf_val, 0.5, 1.0, 2)
      # shares_5y_change: lower (more negative) is better
      s += ts(row.get('shares_5y_change'), 0.01, -0.01, 2,
              inverted=True)
      # roic: higher is better
      s += ts(row.get('roic'), 0.10, 0.25, 3)
      # debt_to_assets: lower is better
      s += ts(row.get('debt_to_assets'), 0.50, 0.30, 1,
              inverted=True)
      buffett_scores.append(s)
    df['buffett_quant_score'] = buffett_scores

    return df

  @staticmethod
  def _apply_gates(
      panel: pd.DataFrame,
  ) -> pd.DataFrame:
    """Mark rows that pass/fail screening gates."""
    df = panel.copy()

    trust = df.get('trust_score', pd.Series(0, index=df.index))
    d2a = df.get(
        'debt_to_assets', pd.Series(pd.NA, index=df.index))

    gate = pd.Series(True, index=df.index)

    # Gate: trust_score >= 3
    gate = gate & (trust >= 3)

    # Gate: debt_to_assets <= 0.8
    gate = gate & ((d2a <= 0.8) | d2a.isna())

    # Gate: no consecutive ROIC negative (2 years)
    if 'roic' in df.columns and 'ticker' in df.columns:
      sorted_df = df.sort_values(['ticker', 'end'])
      prev_roic = sorted_df.groupby('ticker')['roic'].shift(1)
      consecutive_neg = (
          (sorted_df['roic'] < 0) & (prev_roic < 0))
      # Propagate: if any pair in ticker is consecutive neg,
      # flag the latest row for that ticker.
      tickers_with_consec = sorted_df.loc[
          consecutive_neg, 'ticker'].unique()
      gate = gate & ~df['ticker'].isin(tickers_with_consec)

    df['gate_pass'] = gate
    return df
