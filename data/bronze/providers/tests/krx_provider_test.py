"""Tests for KRXProvider — public interface only."""

from unittest.mock import patch

import pandas as pd

from data.bronze.providers.base import BronzeProvider
from data.bronze.providers.base import ProviderResult
from data.bronze.providers.krx import KRXProvider

FAKE_OHLCV = pd.DataFrame({
    'Date': pd.to_datetime(['2026-01-02', '2026-01-03']),
    'Open': [70000, 71000],
    'High': [72000, 73000],
    'Low': [69000, 70000],
    'Close': [71000, 72000],
    'Volume': [1000000, 1200000],
})


class TestKRXProviderInterface:

  def test_is_bronze_provider(self):
    assert isinstance(KRXProvider(), BronzeProvider)

  def test_name_is_krx(self):
    assert KRXProvider().name == 'krx'


class TestKRXProviderFetch:

  @patch('data.bronze.providers.krx._fetch_ohlcv')
  def test_fetches_daily_csv(self, mock_fetch, tmp_path):
    mock_fetch.return_value = FAKE_OHLCV

    provider = KRXProvider()
    result = provider.fetch(
        ['005930'], tmp_path, refresh_days=0, force=True)

    assert isinstance(result, ProviderResult)
    assert result.provider_name == 'krx'
    assert result.fetched >= 1

    csv_file = tmp_path / 'krx' / 'daily' / '005930.csv'
    assert csv_file.exists()

  @patch('data.bronze.providers.krx._fetch_ohlcv')
  def test_skips_fresh_files(self, mock_fetch, tmp_path):
    mock_fetch.return_value = FAKE_OHLCV

    provider = KRXProvider()
    provider.fetch(
        ['005930'], tmp_path, refresh_days=7, force=True)

    result = provider.fetch(
        ['005930'], tmp_path, refresh_days=7, force=False)
    assert result.skipped >= 1
