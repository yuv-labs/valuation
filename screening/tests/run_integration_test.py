"""Integration tests for screening.run — public interface."""

from pathlib import Path

import pandas as pd
import pytest

GOLD_DIR = Path('data/gold/out')
HAS_PANEL = (GOLD_DIR / 'screening_panel.parquet').exists()


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
    for col in ['ticker', 'name', 'market',
                 'opportunity_score', 'roe_3y_avg']:
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
