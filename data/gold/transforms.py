"""
Shared transformation functions for Gold layer panels.

These functions handle common operations like pivoting metrics
and joining with price data using point-in-time logic.
"""

import pandas as pd


def join_metrics_by_cfo_filed(metrics_q: pd.DataFrame) -> pd.DataFrame:
  """
  Join metrics using CFO's filed date as the reference point.

  For each CFO filing, finds the most recent CAPEX and SHARES values
  that were available at that time (filed <= CFO filed date).

  This ensures PIT-correct data: only information known at the
  CFO filing date is used.

  Args:
    metrics_q: Long-format metrics with columns:
               cik10, metric, end, filed, q_val, ttm_val

  Returns:
    Wide-format DataFrame with columns:
    cik10, end, filed, cfo_q, cfo_ttm, capex_q, capex_ttm, shares_q
  """
  cfo = metrics_q[metrics_q['metric'] == 'CFO'].copy()
  capex = metrics_q[metrics_q['metric'] == 'CAPEX'].copy()
  shares = metrics_q[metrics_q['metric'] == 'SHARES'].copy()

  cfo = cfo.rename(columns={'q_val': 'cfo_q', 'ttm_val': 'cfo_ttm'})
  cfo = cfo.drop(columns=['metric'], errors='ignore')
  cfo['end'] = pd.to_datetime(cfo['end'])
  cfo['filed'] = pd.to_datetime(cfo['filed'])
  # Preserve fiscal columns from CFO (reference metric)
  fiscal_cols = ['fiscal_year', 'fiscal_quarter']
  for col in fiscal_cols:
    if col not in cfo.columns:
      cfo[col] = None

  capex = capex.rename(columns={
      'q_val': 'capex_q',
      'ttm_val': 'capex_ttm',
      'filed': 'filed_capex'
  })
  capex = capex.drop(columns=['metric'])
  capex['end'] = pd.to_datetime(capex['end'])
  capex['filed_capex'] = pd.to_datetime(capex['filed_capex'])

  shares = shares.rename(columns={'q_val': 'shares_q', 'filed': 'filed_shares'})
  shares = shares.drop(columns=['metric', 'ttm_val'], errors='ignore')
  shares['end'] = pd.to_datetime(shares['end'])
  shares['filed_shares'] = pd.to_datetime(shares['filed_shares'])

  result_parts = []

  for cik in cfo['cik10'].unique():
    cfo_cik = cfo[cfo['cik10'] == cik]
    capex_cik = capex[capex['cik10'] == cik]
    shares_cik = shares[shares['cik10'] == cik]

    for end_date in cfo_cik['end'].unique():
      cfo_end = cfo_cik[cfo_cik['end'] == end_date].sort_values('filed')
      capex_end = capex_cik[capex_cik['end'] == end_date].sort_values(
          'filed_capex')
      shares_end = shares_cik[shares_cik['end'] == end_date].sort_values(
          'filed_shares')

      if cfo_end.empty:
        continue

      merged = cfo_end.copy()

      if not capex_end.empty:
        merged = pd.merge_asof(
            merged.sort_values('filed'),
            capex_end[['filed_capex', 'capex_q', 'capex_ttm']],
            left_on='filed',
            right_on='filed_capex',
            direction='backward',
        )
      else:
        merged['capex_q'] = None
        merged['capex_ttm'] = None

      if not shares_end.empty:
        merged = pd.merge_asof(
            merged.sort_values('filed'),
            shares_end[['filed_shares', 'shares_q']],
            left_on='filed',
            right_on='filed_shares',
            direction='backward',
        )
      else:
        merged['shares_q'] = None

      result_parts.append(merged)

  if not result_parts:
    return pd.DataFrame(columns=[
        'cik10', 'end', 'filed', 'fiscal_year', 'fiscal_quarter', 'cfo_q',
        'cfo_ttm', 'capex_q', 'capex_ttm', 'shares_q'
    ])

  cleaned = []
  for df in result_parts:
    if df.empty:
      continue
    df = df.dropna(axis=1, how='all')
    if not df.empty:
      cleaned.append(df)

  if not cleaned:
    return pd.DataFrame(columns=[
        'cik10', 'end', 'filed', 'fiscal_year', 'fiscal_quarter', 'cfo_q',
        'cfo_ttm', 'capex_q', 'capex_ttm', 'shares_q'
    ])

  result: pd.DataFrame = pd.concat(cleaned, ignore_index=True)
  result = result.drop(columns=['filed_capex', 'filed_shares'], errors='ignore')

  return result


def join_prices_pit(
    metrics_wide: pd.DataFrame,
    prices: pd.DataFrame,
    ticker_col: str = 'ticker',
) -> pd.DataFrame:
  """
  Join metrics with prices using point-in-time logic.

  For each metric row, finds the first available price after the filed date.
  This ensures no look-ahead bias in the panel.

  Args:
    metrics_wide: Wide-format metrics with ticker and filed columns
    prices: Daily prices with symbol and date columns
    ticker_col: Name of ticker column in metrics_wide

  Returns:
    Panel with price and date columns added
  """
  metrics_wide = metrics_wide.copy()
  metrics_wide['end'] = pd.to_datetime(metrics_wide['end'])
  metrics_wide['filed'] = pd.to_datetime(metrics_wide['filed'])

  prices = prices.copy()
  prices['date'] = pd.to_datetime(prices['date'])

  prices = prices.rename(columns={'symbol': 'ticker'})
  prices['ticker'] = prices['ticker'].str.replace(r'\.\w+$', '', regex=True)

  panel_parts = []

  for ticker, ticker_metrics in metrics_wide.groupby(ticker_col):
    ticker_prices = prices[prices['ticker'] == ticker].copy()
    if ticker_prices.empty:
      continue

    ticker_prices = ticker_prices.sort_values('date')
    merged = pd.merge_asof(
        ticker_metrics.sort_values('filed'),
        ticker_prices[['date', 'close']],
        left_on='filed',
        right_on='date',
        direction='forward',
    )
    merged = merged.rename(columns={'close': 'price'})
    panel_parts.append(merged)

  if not panel_parts:
    cols = list(metrics_wide.columns) + ['date', 'price']
    return pd.DataFrame(columns=cols)

  return pd.concat(panel_parts, ignore_index=True)


def calculate_market_cap(
    panel: pd.DataFrame,
    shares_col: str = 'shares_q',
    price_col: str = 'price',
) -> pd.DataFrame:
  """
  Calculate market capitalization.

  Args:
    panel: Panel with shares and price columns
    shares_col: Name of shares column
    price_col: Name of price column

  Returns:
    Panel with market_cap column added
  """
  panel = panel.copy()

  if shares_col not in panel.columns or price_col not in panel.columns:
    panel['market_cap'] = None
    return panel

  panel['market_cap'] = panel[shares_col] * panel[price_col]
  return panel
