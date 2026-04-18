"""Tests for Gold layer transform functions."""

import pandas as pd

from data.gold.transforms import join_prices_latest
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


class TestJoinPricesLatest:

  def test_attaches_latest_price(self):
    panel = pd.DataFrame({
        'ticker': ['AAPL', 'AAPL'],
        'end': pd.to_datetime(['2024-03-31', '2024-06-30']),
        'shares_q': [1000, 1000],
    })
    prices = pd.DataFrame({
        'symbol': ['AAPL.US'] * 5,
        'date': pd.to_datetime([
            '2024-04-01', '2024-05-01', '2024-06-01',
            '2024-07-01', '2024-08-01',
        ]),
        'close': [170, 172, 175, 178, 180],
    })
    result = join_prices_latest(panel, prices)
    assert result['price_latest'].iloc[0] == 180.0
    assert result['price_latest'].iloc[1] == 180.0
    assert result['date_latest'].iloc[0] == pd.Timestamp('2024-08-01')

  def test_strips_market_suffix(self):
    panel = pd.DataFrame({
        'ticker': ['7203'],
        'end': [pd.Timestamp('2024-06-30')],
        'shares_q': [500],
    })
    prices = pd.DataFrame({
        'symbol': ['7203.JP'] * 2,
        'date': pd.to_datetime(['2024-07-01', '2024-08-01']),
        'close': [3000, 3100],
    })
    result = join_prices_latest(panel, prices)
    assert result['price_latest'].iloc[0] == 3100.0

  def test_multiple_tickers(self):
    panel = pd.DataFrame({
        'ticker': ['AAPL', 'TSLA'],
        'end': pd.to_datetime(['2024-06-30', '2024-06-30']),
        'shares_q': [1000, 500],
    })
    prices = pd.DataFrame({
        'symbol': ['AAPL.US', 'AAPL.US', 'TSLA.US', 'TSLA.US'],
        'date': pd.to_datetime([
            '2024-07-01', '2024-08-01',
            '2024-07-01', '2024-08-01',
        ]),
        'close': [170, 180, 250, 260],
    })
    result = join_prices_latest(panel, prices)
    aapl = result[result['ticker'] == 'AAPL'].iloc[0]
    tsla = result[result['ticker'] == 'TSLA'].iloc[0]
    assert aapl['price_latest'] == 180.0
    assert tsla['price_latest'] == 260.0

  def test_calculates_market_cap_latest(self):
    panel = pd.DataFrame({
        'ticker': ['AAPL'],
        'end': [pd.Timestamp('2024-06-30')],
        'shares_q': [1000],
    })
    prices = pd.DataFrame({
        'symbol': ['AAPL.US'],
        'date': [pd.Timestamp('2024-08-01')],
        'close': [180.0],
    })
    result = join_prices_latest(panel, prices)
    assert result['market_cap_latest'].iloc[0] == 180_000.0

  def test_bare_ticker_without_suffix(self):
    panel = pd.DataFrame({
        'ticker': ['005930'],
        'end': [pd.Timestamp('2024-06-30')],
        'shares_q': [100],
    })
    prices = pd.DataFrame({
        'symbol': ['005930'],
        'date': [pd.Timestamp('2024-08-01')],
        'close': [72000],
    })
    result = join_prices_latest(panel, prices)
    assert result['price_latest'].iloc[0] == 72000
