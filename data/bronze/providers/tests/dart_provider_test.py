"""Tests for DARTProvider — public interface only."""

import io
import json
from unittest.mock import patch
import zipfile

from data.bronze.providers.base import BronzeProvider
from data.bronze.providers.base import ProviderResult
from data.bronze.providers.dart import DARTProvider

FAKE_CORP_CODES_XML = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<result>'
    '<list>'
    '<corp_code>00126380</corp_code>'
    '<corp_name>Samsung</corp_name>'
    '<stock_code>005930</stock_code>'
    '<modify_date>20240101</modify_date>'
    '</list>'
    '<list>'
    '<corp_code>00164779</corp_code>'
    '<corp_name>SKHynix</corp_name>'
    '<stock_code>000660</stock_code>'
    '<modify_date>20240101</modify_date>'
    '</list>'
    '</result>'
).encode('utf-8')

FAKE_FINSTATE_RESPONSE = json.dumps({
    'status': '000',
    'message': 'ok',
    'list': [{
        'sj_div': 'BS',
        'account_nm': 'total_assets',
        'thstrm_amount': '100000000',
    }],
}).encode('utf-8')


def _make_corp_zip() -> bytes:
  buf = io.BytesIO()
  with zipfile.ZipFile(buf, 'w') as zf:
    zf.writestr('CORPCODE.xml', FAKE_CORP_CODES_XML)
  return buf.getvalue()


def _mock_response(content: bytes, is_json: bool = False):
  """Create a mock requests.Response."""
  resp = type('Resp', (), {
      'status_code': 200,
      'content': content,
      'json': lambda self_: json.loads(content) if is_json
              else None,
      'raise_for_status': lambda self_: None,
  })()
  return resp


class TestDARTProviderInterface:

  def test_is_bronze_provider(self):
    provider = DARTProvider(api_key='test')
    assert isinstance(provider, BronzeProvider)

  def test_name_is_dart(self):
    provider = DARTProvider(api_key='test')
    assert provider.name == 'dart'


class TestDARTProviderFetch:

  @patch('data.bronze.providers.dart.requests.get')
  def test_fetches_corp_codes_and_finstate(
      self, mock_get, tmp_path):
    """Provider should save corp_codes and finstate JSON."""
    zip_bytes = _make_corp_zip()

    def side_effect(url, **_kwargs):
      if 'corpCode' in url:
        return _mock_response(zip_bytes)
      return _mock_response(FAKE_FINSTATE_RESPONSE,
                            is_json=True)

    mock_get.side_effect = side_effect

    provider = DARTProvider(api_key='test')
    result = provider.fetch(
        ['005930'], tmp_path, refresh_days=0, force=True)

    assert isinstance(result, ProviderResult)
    assert result.provider_name == 'dart'
    assert not result.errors

    corp_file = tmp_path / 'dart' / 'CORPCODE.xml'
    assert corp_file.exists()

  @patch('data.bronze.providers.dart.requests.get')
  def test_unknown_stock_code_reported(
      self, mock_get, tmp_path):
    """Unknown stock codes should appear in errors."""
    zip_bytes = _make_corp_zip()

    def side_effect(url, **_kwargs):  # pylint: disable=unused-argument
      return _mock_response(zip_bytes)

    mock_get.side_effect = side_effect

    provider = DARTProvider(api_key='test')
    result = provider.fetch(
        ['999999'], tmp_path, refresh_days=0, force=True)

    assert any('999999' in e for e in result.errors)
