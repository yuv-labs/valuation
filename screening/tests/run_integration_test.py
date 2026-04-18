"""Integration tests for screening.run — public interface."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

GOLD_DIR = Path('data/gold/out')
HAS_PANEL = (GOLD_DIR / 'screening_panel.parquet').exists()


class TestTrackBasedSort:
  """Unit tests for track-based sort logic (no real data needed)."""

  @staticmethod
  def _apply_sort(df):
    f_score = df.get(
        'fisher_quant_score',
        pd.Series(0, index=df.index)).fillna(0)
    b_score = df.get(
        'buffett_quant_score',
        pd.Series(0, index=df.index)).fillna(0)
    track = df.get(
        'track_signal',
        pd.Series('', index=df.index)).fillna('')
    df['_sort'] = pd.Series(0.0, index=df.index)
    df.loc[track == 'fisher', '_sort'] = f_score
    df.loc[track == 'buffett', '_sort'] = b_score
    mixed_mask = ~track.isin(['fisher', 'buffett'])
    df.loc[mixed_mask, '_sort'] = pd.concat(
        [f_score[mixed_mask], b_score[mixed_mask]],
        axis=1).max(axis=1)
    return df.sort_values('_sort', ascending=False)

  def test_fisher_sorted_by_fisher_score(self):
    df = pd.DataFrame({
        'ticker': ['A', 'B'],
        'track_signal': ['fisher', 'fisher'],
        'fisher_quant_score': [10, 20],
        'buffett_quant_score': [22, 5],
    })
    result = self._apply_sort(df)
    assert result['ticker'].tolist() == ['B', 'A']

  def test_buffett_sorted_by_buffett_score(self):
    df = pd.DataFrame({
        'ticker': ['A', 'B'],
        'track_signal': ['buffett', 'buffett'],
        'fisher_quant_score': [22, 5],
        'buffett_quant_score': [10, 20],
    })
    result = self._apply_sort(df)
    assert result['ticker'].tolist() == ['B', 'A']

  def test_mixed_sorted_by_max_score(self):
    df = pd.DataFrame({
        'ticker': ['A', 'B'],
        'track_signal': ['mixed', 'mixed'],
        'fisher_quant_score': [15, 5],
        'buffett_quant_score': [5, 18],
    })
    result = self._apply_sort(df)
    assert result['ticker'].tolist() == ['B', 'A']

  def test_nan_scores_treated_as_zero(self):
    df = pd.DataFrame({
        'ticker': ['A', 'B'],
        'track_signal': ['fisher', 'fisher'],
        'fisher_quant_score': [np.nan, 10],
        'buffett_quant_score': [0, 0],
    })
    result = self._apply_sort(df)
    assert result['ticker'].tolist() == ['B', 'A']


@pytest.mark.skipif(not HAS_PANEL, reason='No screening panel')
class TestRunScreening:

  def test_returns_dataframe_with_expected_columns(self):
    from screening.run import \
        run_screening  # pylint: disable=import-outside-toplevel
    df = run_screening(
        gold_dir=GOLD_DIR,
        silver_dir=Path('data/silver/out'),
        top_n=10,
        min_market_cap_us=2e9,
        min_market_cap_kr=5e11,
    )
    assert isinstance(df, pd.DataFrame)
    if not df.empty:
      for col in ['ticker', 'name', 'market',
                   'track_signal', 'fisher_quant_score',
                   'buffett_quant_score', 'moat_score',
                   'opportunity_score']:
        assert col in df.columns, f'Missing: {col}'

  def test_filters_small_caps(self):
    from screening.run import \
        run_screening  # pylint: disable=import-outside-toplevel
    df = run_screening(
        gold_dir=GOLD_DIR,
        silver_dir=Path('data/silver/out'),
        top_n=100,
        min_market_cap_us=2e9,
        min_market_cap_kr=5e11,
    )
    if df.empty:
      return
    kr = df[df['market'] == 'KR']
    us = df[df['market'] == 'US']
    if not kr.empty and 'market_cap' in kr.columns:
      assert kr['market_cap'].dropna().min() >= 5e11
    if not us.empty and 'market_cap' in us.columns:
      assert us['market_cap'].dropna().min() >= 2e9
