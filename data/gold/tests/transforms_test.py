"""Tests for Gold layer transform functions."""

import pandas as pd

from data.gold.transforms import join_prices_pit


class TestPriceSymbolNormalization:
  """join_prices_pit should strip market suffixes from price symbols."""

  def _make_metrics(self, ticker: str) -> pd.DataFrame:
    return pd.DataFrame({
        'ticker': [ticker],
        'end': [pd.Timestamp('2024-06-30')],
        'filed': [pd.Timestamp('2024-08-01')],
        'cfo_q': [100.0],
    })

  def _make_prices(self, symbol: str) -> pd.DataFrame:
    return pd.DataFrame({
        'symbol': [symbol] * 3,
        'date': pd.to_datetime(
            ['2024-07-31', '2024-08-01', '2024-08-02']),
        'close': [150.0, 152.0, 151.0],
    })

  def test_strips_us_suffix(self):
    metrics = self._make_metrics('AAPL')
    prices = self._make_prices('AAPL.US')
    result = join_prices_pit(metrics, prices)
    assert len(result) == 1
    assert result.iloc[0]['price'] == 152.0

  def test_strips_jp_suffix(self):
    metrics = self._make_metrics('7203')
    prices = self._make_prices('7203.JP')
    result = join_prices_pit(metrics, prices)
    assert len(result) == 1
    assert result.iloc[0]['price'] == 152.0

  def test_strips_ss_suffix(self):
    metrics = self._make_metrics('600519')
    prices = self._make_prices('600519.SS')
    result = join_prices_pit(metrics, prices)
    assert len(result) == 1

  def test_strips_de_suffix(self):
    metrics = self._make_metrics('SAP')
    prices = self._make_prices('SAP.DE')
    result = join_prices_pit(metrics, prices)
    assert len(result) == 1

  def test_bare_ticker_without_suffix(self):
    metrics = self._make_metrics('005930')
    prices = self._make_prices('005930')
    result = join_prices_pit(metrics, prices)
    assert len(result) == 1
    assert result.iloc[0]['price'] == 152.0


class TestJoinPricesPitEdgeCases:

  def test_multiple_tickers_merged_at_once(self):
    metrics = pd.DataFrame({
        'ticker': ['AAPL', 'AAPL', 'TSLA'],
        'end': pd.to_datetime(
            ['2024-03-31', '2024-06-30', '2024-03-31']),
        'filed': pd.to_datetime(
            ['2024-05-01', '2024-08-01', '2024-05-15']),
        'cfo_q': [100, 200, 50],
    })
    prices = pd.DataFrame({
        'symbol': ['AAPL.US'] * 3 + ['TSLA.US'] * 3,
        'date': pd.to_datetime(
            ['2024-05-01', '2024-05-02', '2024-08-01',
             '2024-05-15', '2024-05-16', '2024-08-01']),
        'close': [170, 171, 175, 180, 181, 185],
    })
    result = join_prices_pit(metrics, prices)
    assert len(result) == 3
    assert set(result['ticker']) == {'AAPL', 'TSLA'}

  def test_nat_filed_rows_preserved(self):
    metrics = pd.DataFrame({
        'ticker': ['AAPL', 'AAPL'],
        'end': pd.to_datetime(['2024-03-31', '2024-06-30']),
        'filed': [pd.Timestamp('2024-05-01'), pd.NaT],
        'cfo_q': [100, 200],
    })
    prices = pd.DataFrame({
        'symbol': ['AAPL.US'] * 2,
        'date': pd.to_datetime(['2024-05-01', '2024-05-02']),
        'close': [170, 171],
    })
    result = join_prices_pit(metrics, prices)
    assert len(result) == 2
    matched = result[result['price'].notna()]
    assert len(matched) == 1

  def test_unsorted_prices_handled(self):
    metrics = pd.DataFrame({
        'ticker': ['AAPL'],
        'end': [pd.Timestamp('2024-06-30')],
        'filed': [pd.Timestamp('2024-08-01')],
        'cfo_q': [100],
    })
    prices = pd.DataFrame({
        'symbol': ['AAPL.US'] * 3,
        'date': pd.to_datetime(
            ['2024-08-03', '2024-08-01', '2024-07-31']),
        'close': [153, 152, 150],
    })
    result = join_prices_pit(metrics, prices)
    assert len(result) == 1
    assert result.iloc[0]['price'] == 152.0
