"""Integration tests for screening.run — public interface."""

from pathlib import Path

import pandas as pd
import pytest

GOLD_DIR = Path('data/gold/out')
HAS_PANEL = (GOLD_DIR / 'screening_panel.parquet').exists()


@pytest.mark.skipif(not HAS_PANEL, reason='No screening panel')
class TestRunScreening:

  def test_returns_dataframe_with_expected_columns(self):
    from screening.domain import \
        Track  # pylint: disable=import-outside-toplevel
    from screening.run import \
        run_screening  # pylint: disable=import-outside-toplevel
    df = run_screening(
        gold_dir=GOLD_DIR,
        silver_dir=Path('data/silver/out'),
        track=Track.FULL,
        top_n=10,
        min_market_cap_us=2e9,
        min_market_cap_kr=5e11,
    )
    assert isinstance(df, pd.DataFrame)
    if not df.empty:
      for col in ['ticker', 'name', 'market',
                   'moat_score', 'opportunity_score']:
        assert col in df.columns, f'Missing: {col}'

  def test_track_moat_returns_moat_score(self):
    from screening.domain import \
        Track  # pylint: disable=import-outside-toplevel
    from screening.run import \
        run_screening  # pylint: disable=import-outside-toplevel
    df = run_screening(
        gold_dir=GOLD_DIR,
        silver_dir=Path('data/silver/out'),
        track=Track.MOAT,
        top_n=10,
        min_market_cap_us=2e9,
        min_market_cap_kr=5e11,
    )
    assert isinstance(df, pd.DataFrame)
    if not df.empty:
      assert 'moat_score' in df.columns

  def test_filters_small_caps(self):
    from screening.domain import \
        Track  # pylint: disable=import-outside-toplevel
    from screening.run import \
        run_screening  # pylint: disable=import-outside-toplevel
    df = run_screening(
        gold_dir=GOLD_DIR,
        silver_dir=Path('data/silver/out'),
        track=Track.FULL,
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
