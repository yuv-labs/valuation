"""Tests for market-aware price symbol lookup."""

from valuation.run import PRICE_SUFFIX


class TestPriceSuffix:

  def test_us_suffix(self):
    assert PRICE_SUFFIX['us'] == '.US'

  def test_kr_no_suffix(self):
    assert PRICE_SUFFIX['kr'] == ''

  def test_jp_suffix(self):
    assert PRICE_SUFFIX['jp'] == '.JP'

  def test_symbol_construction_us(self):
    ticker = 'AAPL'
    symbol = f"{ticker}{PRICE_SUFFIX['us']}"
    assert symbol == 'AAPL.US'

  def test_symbol_construction_kr(self):
    ticker = '005930'
    symbol = f"{ticker}{PRICE_SUFFIX['kr']}"
    assert symbol == '005930'

  def test_symbol_construction_jp(self):
    ticker = '7203'
    symbol = f"{ticker}{PRICE_SUFFIX['jp']}"
    assert symbol == '7203.JP'
