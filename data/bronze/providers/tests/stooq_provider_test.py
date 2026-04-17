"""Tests for StooqProvider — public interface only."""

from unittest.mock import patch

from data.bronze.cache import BronzeCache
from data.bronze.providers.base import BronzeProvider
from data.bronze.providers.base import ProviderResult
from data.bronze.providers.stooq import StooqProvider

FAKE_CSV = (
    b'Date,Open,High,Low,Close,Volume\n'
    b'2026-01-02,150.0,155.0,149.0,153.0,1000000\n')


def _make_fetch_result(url, content):
  from data.bronze.update import \
      FetchResult  # pylint: disable=import-outside-toplevel
  return FetchResult(
      url=url,
      status_code=200,
      nbytes=len(content),
      fetched_at_utc='2026-01-01T00:00:00+00:00',
  )


def _mock_fetch_bytes(url_to_content):

  def side_effect(session, url, **kwargs):  # pylint: disable=unused-argument
    for pattern, content in url_to_content.items():
      if pattern in url:
        return content, _make_fetch_result(url, content)
    raise ValueError(f'Unexpected URL: {url}')

  return side_effect


class TestStooqProviderInterface:

  def test_is_bronze_provider(self):
    provider = StooqProvider()
    assert isinstance(provider, BronzeProvider)

  def test_name_is_stooq(self):
    provider = StooqProvider()
    assert provider.name == 'stooq'


class TestStooqProviderFetch:

  @patch('data.bronze.providers.stooq._fetch_bytes')
  def test_fetches_daily_csv(self, mock_fetch, tmp_path):
    mock_fetch.side_effect = _mock_fetch_bytes({
        'stooq.com': FAKE_CSV,
    })

    provider = StooqProvider()
    result = provider.fetch(
        ['AAPL.US'], tmp_path, refresh_days=0, force=True)

    assert isinstance(result, ProviderResult)
    assert result.provider_name == 'stooq'
    assert result.fetched >= 1

    csv_file = tmp_path / 'stooq' / 'daily' / 'aapl.us.csv'
    assert csv_file.exists()
    assert csv_file.read_bytes() == FAKE_CSV

  @patch('data.bronze.providers.stooq._fetch_bytes')
  def test_skips_fresh_files(self, mock_fetch, tmp_path):
    mock_fetch.side_effect = _mock_fetch_bytes({
        'stooq.com': FAKE_CSV,
    })

    provider = StooqProvider()
    provider.fetch(
        ['AAPL.US'], tmp_path, refresh_days=7, force=True)

    result = provider.fetch(
        ['AAPL.US'], tmp_path, refresh_days=7, force=False)
    assert result.skipped >= 1

  @patch('data.bronze.providers.stooq._fetch_bytes')
  def test_stores_fetched_data_in_cache(self, mock_fetch, tmp_path):
    mock_fetch.side_effect = _mock_fetch_bytes({
        'stooq.com': FAKE_CSV,
    })

    cache = BronzeCache(cache_dir=tmp_path / 'cache')
    provider = StooqProvider()
    provider.fetch(
        ['AAPL.US'], tmp_path / 'out', refresh_days=0, force=True,
        cache=cache)

    assert cache.get_if_fresh(
        'stooq/daily/aapl.us.csv', max_age_days=None) == FAKE_CSV

  @patch('data.bronze.providers.stooq._fetch_bytes')
  def test_restores_from_cache_without_api_call(self, mock_fetch, tmp_path):
    mock_fetch.side_effect = _mock_fetch_bytes({
        'stooq.com': FAKE_CSV,
    })

    cache = BronzeCache(cache_dir=tmp_path / 'cache')
    provider = StooqProvider()

    provider.fetch(
        ['AAPL.US'], tmp_path / 'out1', refresh_days=0, force=True,
        cache=cache)
    calls_after_first = mock_fetch.call_count

    provider.fetch(
        ['AAPL.US'], tmp_path / 'out2', refresh_days=0, force=False,
        cache=cache)

    assert (tmp_path / 'out2' / 'stooq' / 'daily'
            / 'aapl.us.csv').exists()
    assert mock_fetch.call_count == calls_after_first
