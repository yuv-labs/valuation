"""Tests for SECProvider — public interface only."""

import json
from unittest.mock import patch

from data.bronze.providers.base import BronzeProvider
from data.bronze.providers.base import ProviderResult
from data.bronze.providers.sec import SECProvider

# -- Fixtures ---------------------------------------------------------------

FAKE_COMPANY_TICKERS = json.dumps({
    '0': {
        'cik_str': 320193,
        'ticker': 'AAPL',
        'title': 'Apple Inc.'
    },
    '1': {
        'cik_str': 789019,
        'ticker': 'MSFT',
        'title': 'Microsoft Corp'
    },
}).encode('utf-8')

FAKE_COMPANYFACTS = json.dumps({
    'cik': 320193,
    'entityName': 'Apple Inc.',
    'facts': {}
}).encode('utf-8')

FAKE_SUBMISSIONS = json.dumps({
    'cik': '320193',
    'filings': {}
}).encode('utf-8')


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
  """Create a side_effect for _fetch_bytes."""

  def side_effect(session, url, **kwargs):  # pylint: disable=unused-argument
    for pattern, content in url_to_content.items():
      if pattern in url:
        return content, _make_fetch_result(url, content)
    raise ValueError(f'Unexpected URL: {url}')

  return side_effect


# -- Tests ------------------------------------------------------------------


class TestSECProviderInterface:
  """SECProvider must satisfy the BronzeProvider contract."""

  def test_is_bronze_provider(self):
    provider = SECProvider(user_agent='test agent')
    assert isinstance(provider, BronzeProvider)

  def test_name_is_sec(self):
    provider = SECProvider(user_agent='test agent')
    assert provider.name == 'sec'


class TestSECProviderFetch:
  """SECProvider.fetch() writes expected files to out_dir."""

  @patch('data.bronze.providers.sec._fetch_bytes')
  def test_fetches_company_tickers_and_companyfacts(self, mock_fetch, tmp_path):
    mock_fetch.side_effect = _mock_fetch_bytes({
        'company_tickers.json': FAKE_COMPANY_TICKERS,
        'companyfacts': FAKE_COMPANYFACTS,
    })

    provider = SECProvider(user_agent='test agent', min_interval_sec=0)
    result = provider.fetch(['AAPL'], tmp_path, refresh_days=0, force=True)

    assert isinstance(result, ProviderResult)
    assert result.provider_name == 'sec'
    assert result.fetched >= 1
    assert not result.errors

    # company_tickers.json should exist
    tickers_file = tmp_path / 'sec' / 'company_tickers.json'
    assert tickers_file.exists()

    # companyfacts for AAPL should exist
    cik10 = '0000320193'
    cf_file = tmp_path / 'sec' / 'companyfacts' / f'CIK{cik10}.json'
    assert cf_file.exists()

  @patch('data.bronze.providers.sec._fetch_bytes')
  def test_unknown_ticker_is_reported_in_errors(self, mock_fetch, tmp_path):
    mock_fetch.side_effect = _mock_fetch_bytes({
        'company_tickers.json': FAKE_COMPANY_TICKERS,
    })

    provider = SECProvider(user_agent='test agent', min_interval_sec=0)
    result = provider.fetch(['ZZZZ'], tmp_path, refresh_days=0, force=True)

    assert any('ZZZZ' in e for e in result.errors)

  @patch('data.bronze.providers.sec._fetch_bytes')
  def test_skips_fresh_files(self, mock_fetch, tmp_path):
    mock_fetch.side_effect = _mock_fetch_bytes({
        'company_tickers.json': FAKE_COMPANY_TICKERS,
        'companyfacts': FAKE_COMPANYFACTS,
    })

    provider = SECProvider(user_agent='test agent', min_interval_sec=0)

    # First fetch
    provider.fetch(['AAPL'], tmp_path, refresh_days=7, force=True)
    call_count_after_first = mock_fetch.call_count

    # Second fetch — should skip fresh files
    result = provider.fetch(['AAPL'], tmp_path, refresh_days=7, force=False)

    assert result.skipped >= 1
    # No new fetch calls should have been made for companyfacts
    assert mock_fetch.call_count == call_count_after_first

  @patch('data.bronze.providers.sec._fetch_bytes')
  def test_includes_submissions_when_requested(self, mock_fetch, tmp_path):
    mock_fetch.side_effect = _mock_fetch_bytes({
        'company_tickers.json': FAKE_COMPANY_TICKERS,
        'companyfacts': FAKE_COMPANYFACTS,
        'submissions': FAKE_SUBMISSIONS,
    })

    provider = SECProvider(
        user_agent='test agent',
        min_interval_sec=0,
        include_submissions=True,
    )
    provider.fetch(['AAPL'], tmp_path, refresh_days=0, force=True)

    cik10 = '0000320193'
    sub_file = (
        tmp_path / 'sec' / 'submissions' / f'CIK{cik10}.json')
    assert sub_file.exists()
