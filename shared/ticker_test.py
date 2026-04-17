from shared.ticker import is_kr_ticker


class TestIsKrTicker:

  def test_pure_digit_kr(self):
    assert is_kr_ticker('000270')
    assert is_kr_ticker('005850')
    assert is_kr_ticker('192080')

  def test_alphanumeric_kr(self):
    assert is_kr_ticker('0126Z0')
    assert is_kr_ticker('0001A0')
    assert is_kr_ticker('0030R0')

  def test_us_tickers(self):
    assert not is_kr_ticker('AAPL')
    assert not is_kr_ticker('AMZN')
    assert not is_kr_ticker('KR')
    assert not is_kr_ticker('ZTS')

  def test_lowercase_rejected(self):
    assert not is_kr_ticker('0126z0')
    assert not is_kr_ticker('0001a0')

  def test_edge_cases(self):
    assert not is_kr_ticker('')
    assert not is_kr_ticker('00001A')
    assert not is_kr_ticker('12345')
    assert not is_kr_ticker('1234567')
