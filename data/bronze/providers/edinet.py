"""EDINET (Japan FSA) Bronze provider."""

from __future__ import annotations

import csv
from datetime import datetime
import io
import logging
from pathlib import Path
import time
from typing import Iterable
import zipfile

import requests

from data.bronze.providers.base import BronzeProvider
from data.bronze.providers.base import ProviderResult
from data.bronze.update import _atomic_write_bytes
from data.bronze.update import _ensure_dir
from data.bronze.update import _is_fresh
from data.bronze.update import _write_meta

logger = logging.getLogger(__name__)

_EDINET_CODE_URL = (
    'https://disclosure2dl.edinet-fsa.go.jp'
    '/searchdocument/codelist/Edinetcode.zip')
_DOC_LIST_URL = (
    'https://api.edinet-fsa.go.jp/api/v2/documents.json')
_DOC_DOWNLOAD_URL = (
    'https://api.edinet-fsa.go.jp/api/v2/documents/{doc_id}')

_DEFAULT_HISTORY_YEARS = 5

_DOC_TYPE_ANNUAL = '120'
_DOC_TYPE_QUARTERLY = '130'
_DOC_TYPE_SEMIANNUAL = '140'
_TARGET_DOC_TYPES = {_DOC_TYPE_ANNUAL, _DOC_TYPE_QUARTERLY,
                     _DOC_TYPE_SEMIANNUAL}


class EDINETProvider(BronzeProvider):
  """Fetches Japanese financial XBRL filings from EDINET."""

  def __init__(
      self,
      api_key: str,
      min_interval_sec: float = 0.5,
      history_years: int = _DEFAULT_HISTORY_YEARS,
  ) -> None:
    self._api_key = api_key
    self._min_interval = min_interval_sec
    self._history_years = history_years

  @property
  def name(self) -> str:
    return 'edinet'

  def fetch(
      self,
      tickers: Iterable[str],
      out_dir: Path,
      *,
      refresh_days: int = 7,
      force: bool = False,
  ) -> ProviderResult:
    edinet_dir = out_dir / 'edinet'
    _ensure_dir(edinet_dir / 'xbrl')

    fetched = 0
    skipped = 0
    errors: list[str] = []

    csv_path = edinet_dir / 'EdinetcodeDlInfo.csv'
    if force or not _is_fresh(csv_path, refresh_days):
      try:
        self._fetch_edinet_codes(csv_path)
        fetched += 1
      except (requests.RequestException, OSError) as exc:
        errors.append(f'edinet_codes: {exc}')
        return ProviderResult(
            provider_name=self.name,
            fetched=fetched, skipped=skipped,
            errors=errors)
    else:
      skipped += 1

    sec_to_edinet = _parse_edinet_codes(csv_path)

    tickers_list = list(tickers)
    for ticker in tickers_list:
      ticker = ticker.strip()
      sec_code = f'{ticker}0' if len(ticker) == 4 else ticker
      edinet_code = sec_to_edinet.get(sec_code)
      if edinet_code is None:
        errors.append(f'Ticker not found in EDINET: {ticker}')
        continue

      try:
        n = self._fetch_filings_for(
            edinet_code, edinet_dir,
            refresh_days=refresh_days, force=force)
        fetched += n
      except (requests.RequestException, OSError) as exc:
        errors.append(f'{ticker}: {exc}')

    return ProviderResult(
        provider_name=self.name,
        fetched=fetched, skipped=skipped,
        errors=errors)

  def _fetch_edinet_codes(self, csv_path: Path) -> None:
    resp = requests.get(_EDINET_CODE_URL, timeout=30)
    resp.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
      for name in zf.namelist():
        if name.endswith('.csv'):
          csv_bytes = zf.read(name)
          _atomic_write_bytes(csv_path, csv_bytes)
          _write_meta(csv_path, {
              'url': _EDINET_CODE_URL,
              'status_code': resp.status_code,
              'nbytes': len(csv_bytes),
          })
          return

    raise ValueError('No CSV found in EDINET code zip')

  def _fetch_filings_for(
      self,
      edinet_code: str,
      edinet_dir: Path,
      *,
      refresh_days: int,
      force: bool,
  ) -> int:
    fetched = 0
    doc_ids = self._search_documents(edinet_code)

    for doc in doc_ids:
      doc_id = doc['docID']
      period_end = doc.get('periodEnd', 'unknown')
      doc_type = doc.get('docTypeCode', '')

      out_path = (edinet_dir / 'xbrl'
                  / f'{edinet_code}_{period_end}_{doc_type}.zip')

      if not force and _is_fresh(out_path, refresh_days):
        continue

      time.sleep(self._min_interval)

      url = _DOC_DOWNLOAD_URL.format(doc_id=doc_id)
      params: dict[str, str] = {
          'type': '5', 'Subscription-Key': self._api_key}
      resp = requests.get(url, params=params, timeout=60)
      resp.raise_for_status()

      _atomic_write_bytes(out_path, resp.content)
      _write_meta(out_path, {
          'url': url,
          'doc_id': doc_id,
          'period_end': period_end,
          'status_code': resp.status_code,
          'nbytes': len(resp.content),
      })
      fetched += 1

    return fetched

  def _search_documents(self, edinet_code: str) -> list[dict]:
    """Search EDINET document list for filings by edinet_code.

    EDINET API returns filings submitted on an exact date.
    Annual reports are typically filed ~3 months after FYE,
    so we scan the primary filing windows (June/July for March FYE,
    etc.) day by day.
    """
    now = datetime.now()
    results: list[dict] = []
    seen_doc_ids: set[str] = set()

    for year_offset in range(self._history_years):
      year = now.year - year_offset
      for filing_month in [6, 7, 8, 11, 12, 2, 3, 5]:
        for day in [15, 20, 25, 28]:
          date_str = f'{year}-{filing_month:02d}-{day:02d}'
          time.sleep(self._min_interval)

          doc_params: dict[str, str] = {
              'date': date_str,
              'type': '2',
              'Subscription-Key': self._api_key,
          }
          resp = requests.get(
              _DOC_LIST_URL, params=doc_params, timeout=30)
          if not resp.ok:
            logger.debug('EDINET API %s: %d', date_str,
                         resp.status_code)
            continue

          try:
            data = resp.json()
          except (ValueError, AttributeError):
            data = {}
          for doc in data.get('results', []):
            doc_id = doc.get('docID', '')
            if (doc.get('edinetCode') == edinet_code
                and doc.get('docTypeCode') in _TARGET_DOC_TYPES
                and doc_id not in seen_doc_ids):
              results.append(doc)
              seen_doc_ids.add(doc_id)

    return results


def _parse_edinet_codes(csv_path: Path) -> dict[str, str]:
  """Parse EDINET code CSV: securities_code -> edinet_code."""
  if not csv_path.exists():
    return {}

  result: dict[str, str] = {}
  text = csv_path.read_bytes().decode('utf-8-sig')
  reader = csv.DictReader(io.StringIO(text))

  for row in reader:
    edinet_code = (row.get('EDINET code')
                   or row.get('EDINETコード', '')).strip()
    sec_code = (row.get('Securities code')
                or row.get('証券コード', '')).strip()
    if edinet_code and sec_code:
      result[sec_code] = edinet_code

  return result
