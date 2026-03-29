"""Utility script to view historical metrics (ROE, ROIC, etc.) for a ticker."""
import argparse
from pathlib import Path
from typing import Any

import pandas as pd


def run() -> None:
  """Main entry point for historical metrics viewer."""
  parser = argparse.ArgumentParser(description='View ticker historical metrics')
  parser.add_argument(
      '--ticker', type=str, required=True, help='Ticker to view (e.g. 000270)')
  parser.add_argument(
      '--path',
      type=Path,
      default=Path('data/gold/out/valuation_panel.parquet'),
      help='Path to gold panel')
  parser.add_argument(
      '--years', type=int, default=5, help='Years of history to show')

  args = parser.parse_args()

  if not args.path.exists():
    print(f'Error: {args.path} not found')
    return

  df = pd.read_parquet(args.path)
  ticker_df = df[df['ticker'] == args.ticker]
  ticker_df = ticker_df.sort_values('end', ascending=False)

  if ticker_df.empty:
    print(f'No data found for {args.ticker}')
    return

  # Calculate Ratios
  # ROE = Net Income / Total Equity
  has_ni = 'net_income_ttm' in ticker_df.columns
  has_eq = 'total_equity_q' in ticker_df.columns
  if has_ni and has_eq:
    ticker_df['ROE'] = (
        ticker_df['net_income_ttm'] /
        ticker_df['total_equity_q'].replace(0, pd.NA))

  # EBIT Margin = EBIT / Revenue
  if 'ebit_ttm' in ticker_df.columns and 'revenue_ttm' in ticker_df.columns:
    ticker_df['EBIT_Margin'] = (
        ticker_df['ebit_ttm'] / ticker_df['revenue_ttm'].replace(0, pd.NA))

  # ROIC (Simplified: NOPAT (EBIT*0.75) / (Assets - CurLiab - Cash))
  req_cols = [
      'ebit_ttm', 'total_assets_q', 'current_liabilities_q', 'cash_q'
  ]
  if all(c in ticker_df.columns for c in req_cols):
    invested_capital = (
        ticker_df['total_assets_q'] - ticker_df['current_liabilities_q'] -
        ticker_df['cash_q'].fillna(0))
    ticker_df['ROIC'] = (ticker_df['ebit_ttm'] * 0.75) / invested_capital.replace(
        0, pd.NA)

  cols = [
      'end', 'ticker', 'revenue_ttm', 'ebit_ttm', 'net_income_ttm',
      'total_equity_q', 'ROE', 'ROIC', 'EBIT_Margin'
  ]
  available_cols = [c for c in cols if c in ticker_df.columns]

  display_df = ticker_df[available_cols].head(args.years * 4)  # quarterly data

  print(f'\n[Historical Metrics for {args.ticker}]')

  # Format for display
  def format_val(val: Any) -> str:
    if pd.isna(val):
      return '-'
    if isinstance(val, (float, int)):
      if abs(val) < 2:
        return f'{val:.1%}'  # ratio
      if abs(val) > 1e12:
        return f'{val / 1e12:.1f}T'
      if abs(val) > 1e8:
        return f'{val / 1e8:.1f}억'
    return str(val)

  print(
      display_df.to_string(
          index=False,
          formatters={
              'revenue_ttm': format_val,
              'ebit_ttm': format_val,
              'net_income_ttm': format_val,
              'total_equity_q': format_val,
              'ROE': format_val,
              'ROIC': format_val,
              'EBIT_Margin': format_val,
          }))


if __name__ == '__main__':
  run()
