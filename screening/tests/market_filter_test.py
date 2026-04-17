"""Tests for market-aware filtering in screening."""

import pandas as pd

from screening.run import _filter_market_cap


class TestFilterMarketCap:

  def _make_panel(self, rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows)

  def test_filters_us_by_threshold(self):
    df = self._make_panel([
        {'ticker': 'AAPL', 'market': 'US', 'market_cap': 3e12},
        {'ticker': 'TINY', 'market': 'US', 'market_cap': 1e8},
    ])
    result = _filter_market_cap(df, min_market_cap_us=2e9,
                                min_market_cap_kr=5e11)
    assert set(result['ticker']) == {'AAPL'}

  def test_filters_kr_by_threshold(self):
    df = self._make_panel([
        {'ticker': '005930', 'market': 'KR', 'market_cap': 4e14},
        {'ticker': '999999', 'market': 'KR', 'market_cap': 1e10},
    ])
    result = _filter_market_cap(df, min_market_cap_us=2e9,
                                min_market_cap_kr=5e11)
    assert set(result['ticker']) == {'005930'}

  def test_filters_jp_by_threshold(self):
    df = self._make_panel([
        {'ticker': '7203', 'market': 'JP', 'market_cap': 6e13},
        {'ticker': '9999', 'market': 'JP', 'market_cap': 1e10},
    ])
    result = _filter_market_cap(
        df, min_market_cap_us=2e9, min_market_cap_kr=5e11,
        min_market_cap_jp=1e11)
    assert set(result['ticker']) == {'7203'}

  def test_uses_market_column_not_isdigit(self):
    """Market column drives filtering, not ticker format."""
    df = self._make_panel([
        {'ticker': '600519', 'market': 'CN', 'market_cap': 2e12},
        {'ticker': '005930', 'market': 'KR', 'market_cap': 4e14},
    ])
    result = _filter_market_cap(
        df, min_market_cap_us=2e9, min_market_cap_kr=5e11)
    assert 'KR' in set(result['market'])
    assert '600519' not in set(result['ticker'])

  def test_mixed_markets(self):
    df = self._make_panel([
        {'ticker': 'AAPL', 'market': 'US', 'market_cap': 3e12},
        {'ticker': '005930', 'market': 'KR', 'market_cap': 4e14},
        {'ticker': '7203', 'market': 'JP', 'market_cap': 6e13},
    ])
    result = _filter_market_cap(
        df, min_market_cap_us=2e9, min_market_cap_kr=5e11,
        min_market_cap_jp=1e11)
    assert len(result) == 3
