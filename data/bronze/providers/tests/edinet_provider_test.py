"""Tests for EDINETProvider — public interface only."""

import io
import json
from unittest.mock import patch
import zipfile

from data.bronze.providers.base import BronzeProvider
from data.bronze.providers.base import ProviderResult
from data.bronze.providers.edinet import EDINETProvider

FAKE_EDINET_CODE_CSV = (
    'EDINET code,Type,Listed/Unlisted,Consolidated/Individual,'
    'Capital,Settlement date,Submitter name,'
    'Submitter name (English),Submitter name (Kana),'
    'Address,Industry,Securities code,Corporate number\n'
    'E02529,Corporation,Listed,Consolidated,635400000000,'
    '3月,トヨタ自動車株式会社,TOYOTA MOTOR CORPORATION,'
    'トヨタジドウシャ,愛知県豊田市,Transportation Equipment,72030,'
    '1180301018771\n'
    'E01777,Corporation,Listed,Consolidated,86340000000,'
    '3月,ソニーグループ株式会社,Sony Group Corporation,'
    'ソニーグループ,東京都港区,Electric Appliances,67580,'
    '7010401067252\n'
)

FAKE_DOC_LIST_RESPONSE = json.dumps({
    'metadata': {'status': '200'},
    'results': [
        {
            'docID': 'S100ABC1',
            'edinetCode': 'E02529',
            'secCode': '72030',
            'filerName': 'トヨタ自動車株式会社',
            'docTypeCode': '120',
            'periodStart': '2024-04-01',
            'periodEnd': '2025-03-31',
            'submitDateTime': '2025-06-25 09:00',
        },
    ],
}).encode('utf-8')

FAKE_XBRL_ZIP = b'PK_fake_xbrl_content'


def _make_edinet_code_zip() -> bytes:
  buf = io.BytesIO()
  with zipfile.ZipFile(buf, 'w') as zf:
    zf.writestr('EdinetcodeDlInfo.csv', FAKE_EDINET_CODE_CSV)
  return buf.getvalue()


def _mock_response(content: bytes, status_code: int = 200):
  resp = type('Resp', (), {
      'status_code': status_code,
      'content': content,
      'ok': status_code == 200,
      'raise_for_status': lambda self_: None,
      'json': lambda self_: json.loads(content),
  })()
  return resp


class TestEDINETProviderInterface:

  def test_is_bronze_provider(self):
    provider = EDINETProvider(api_key='test')
    assert isinstance(provider, BronzeProvider)

  def test_name_is_edinet(self):
    provider = EDINETProvider(api_key='test')
    assert provider.name == 'edinet'


class TestEDINETProviderFetch:

  @patch('data.bronze.providers.edinet.requests.get')
  def test_fetches_code_mapping_and_xbrl(
      self, mock_get, tmp_path):
    zip_bytes = _make_edinet_code_zip()

    def side_effect(url, **_kwargs):
      if 'codelist' in url:
        return _mock_response(zip_bytes)
      if 'documents.json' in url:
        return _mock_response(FAKE_DOC_LIST_RESPONSE)
      return _mock_response(FAKE_XBRL_ZIP)

    mock_get.side_effect = side_effect

    provider = EDINETProvider(api_key='test', history_years=1)
    result = provider.fetch(
        ['7203'], tmp_path, refresh_days=0, force=True)

    assert isinstance(result, ProviderResult)
    assert result.provider_name == 'edinet'
    assert not result.errors

    code_file = tmp_path / 'edinet' / 'EdinetcodeDlInfo.csv'
    assert code_file.exists()

  @patch('data.bronze.providers.edinet.requests.get')
  def test_unknown_ticker_reported(
      self, mock_get, tmp_path):
    zip_bytes = _make_edinet_code_zip()

    def side_effect(url, **_kwargs):
      if 'codelist' in url:
        return _mock_response(zip_bytes)
      if 'documents.json' in url:
        return _mock_response(
            json.dumps({'metadata': {'status': '200'},
                        'results': []}).encode())
      return _mock_response(b'', 404)

    mock_get.side_effect = side_effect

    provider = EDINETProvider(api_key='test', history_years=1)
    result = provider.fetch(
        ['9999'], tmp_path, refresh_days=0, force=True)

    assert any('9999' in e for e in result.errors)

  @patch('data.bronze.providers.edinet.requests.get')
  def test_saves_xbrl_to_correct_path(
      self, mock_get, tmp_path):
    zip_bytes = _make_edinet_code_zip()

    def side_effect(url, **_kwargs):
      if 'codelist' in url:
        return _mock_response(zip_bytes)
      if 'documents.json' in url:
        return _mock_response(FAKE_DOC_LIST_RESPONSE)
      return _mock_response(FAKE_XBRL_ZIP)

    mock_get.side_effect = side_effect

    provider = EDINETProvider(api_key='test', history_years=1)
    provider.fetch(
        ['7203'], tmp_path, refresh_days=0, force=True)

    xbrl_dir = tmp_path / 'edinet' / 'xbrl'
    assert xbrl_dir.exists()
    xbrl_files = list(xbrl_dir.glob('*.zip'))
    assert len(xbrl_files) >= 1
