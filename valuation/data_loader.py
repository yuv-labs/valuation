"""
Caching data loader for valuation data.

Provides efficient loading and caching of Gold panel and price data
to avoid repeated file I/O in batch processing scenarios.

Usage:
  # Single valuation (no caching needed)
  result = run_valuation(ticker='AAPL', as_of_date='2024-12-31')

  # Batch valuation (with caching)
  loader = ValuationDataLoader()
  for ticker in tickers:
    result = run_valuation(ticker, as_of_date, loader=loader)
"""

from pathlib import Path
from typing import Optional

import pandas as pd


class ValuationDataLoader:
  """
  Cached data loader for valuation operations.

  Loads and caches:
  - Gold panel (with split adjustments)
  - Price data

  This avoids repeated file I/O when running multiple valuations.
  """

  def __init__(
      self,
      gold_path: Path = Path('data/gold/out/valuation_panel.parquet'),
      silver_dir: Path = Path('data/silver/out'),
  ):
    """
    Initialize data loader.

    Args:
      gold_path: Path to Gold panel parquet file
      silver_dir: Path to Silver layer output directory
    """
    self.gold_path = gold_path
    self.silver_dir = silver_dir

    self._panel: Optional[pd.DataFrame] = None
    self._prices: Optional[pd.DataFrame] = None

  def load_panel(self) -> pd.DataFrame:
    """
    Load and cache Gold panel with split adjustments.

    Returns:
      DataFrame with split-adjusted shares

    Raises:
      FileNotFoundError: If Gold panel does not exist
    """
    if self._panel is not None:
      return self._panel

    if not self.gold_path.exists():
      raise FileNotFoundError(f'Gold panel not found: {self.gold_path}. '
                              'Run "python -m data.gold.build" first.')

    panel = pd.read_parquet(self.gold_path)
    panel['end'] = pd.to_datetime(panel['end'])
    panel['filed'] = pd.to_datetime(panel['filed'])

    # Apply split adjustments
    panel = self._adjust_for_splits(panel)

    self._panel = panel
    return panel

  def load_prices(self) -> pd.DataFrame:
    """
    Load and cache price data.

    Returns:
      DataFrame with daily price data

    Raises:
      FileNotFoundError: If price data does not exist
    """
    if self._prices is not None:
      return self._prices

    parts: list[pd.DataFrame] = []
    for price_path in sorted(self.silver_dir.glob('*/prices_daily.parquet')):
      df = pd.read_parquet(price_path)
      df['date'] = pd.to_datetime(df['date'])
      parts.append(df)

    if not parts:
      raise FileNotFoundError(
          f'No price data found in {self.silver_dir}/*/prices_daily.parquet')

    prices = pd.concat(parts, ignore_index=True)
    self._prices = prices
    return prices

  def clear_cache(self) -> None:
    """Clear all cached data."""
    self._panel = None
    self._prices = None

  @staticmethod
  def _adjust_for_splits(panel: pd.DataFrame) -> pd.DataFrame:
    """
    Adjust shares for stock splits across all tickers.

    Uses original filings (fy == fiscal_year) to detect splits, then
    applies value-based adjustment to handle inconsistent SEC reporting
    where some comparative disclosures use pre-split values.

    Args:
      panel: Raw Gold panel data

    Returns:
      Panel with split-adjusted shares
    """
    adjusted_parts = []

    for ticker in panel['ticker'].unique():
      ticker_data = panel[panel['ticker'] == ticker].copy()

      shares_missing = ('shares_q' not in ticker_data.columns or
                        ticker_data['shares_q'].isna().all())
      if shares_missing:
        adjusted_parts.append(ticker_data)
        continue

      has_fy_cols = ('fy' in ticker_data.columns and
                     'fiscal_year' in ticker_data.columns)
      if has_fy_cols:
        original_only = ticker_data[ticker_data['fy'] ==
                                    ticker_data['fiscal_year']]
      else:
        original_only = ticker_data.drop_duplicates('end', keep='first')

      original_only = original_only.sort_values('end')

      if len(original_only) < 2:
        adjusted_parts.append(ticker_data)
        continue

      original_only = original_only.copy()
      original_only['shares_ratio'] = (original_only['shares_q'] /
                                       original_only['shares_q'].shift(1))

      splits = original_only[(original_only['shares_ratio'] > 2) |
                             (original_only['shares_ratio'] < 0.5)].copy()

      if splits.empty:
        adjusted_parts.append(ticker_data)
        continue

      for _, split_row in splits.iloc[::-1].iterrows():
        split_date = split_row['end']
        split_ratio = split_row['shares_ratio']
        post_split_shares = split_row['shares_q']

        pre_split_rows = ticker_data['end'] < split_date
        for idx in ticker_data[pre_split_rows].index:
          current_shares = ticker_data.loc[idx, 'shares_q']
          if pd.isna(current_shares):
            continue

          expected_post_split = current_shares * split_ratio
          ratio_to_reference = expected_post_split / post_split_shares

          if 0.5 < ratio_to_reference < 2.0:
            ticker_data.loc[idx, 'shares_q'] = expected_post_split

      adjusted_parts.append(ticker_data)

    result: pd.DataFrame = pd.concat(adjusted_parts, ignore_index=True)
    return result
