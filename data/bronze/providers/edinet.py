"""EDINET (Japan FSA) Bronze provider."""

from __future__ import annotations

import csv
from datetime import date
from datetime import timedelta
import io
import json
import logging
from pathlib import Path
import time
from typing import Iterable, TYPE_CHECKING
import zipfile

import requests

from data.bronze.providers.base import BronzeProvider
from data.bronze.providers.base import ProviderResult
from data.bronze.update import _atomic_write_bytes
from data.bronze.update import _ensure_dir
from data.bronze.update import _is_fresh
from data.bronze.update import _write_meta

if TYPE_CHECKING:
  from data.bronze.cache import BronzeCache

logger = logging.getLogger(__name__)

_EDINET_CODE_URL = (
    'https://disclosure2dl.edinet-fsa.go.jp'
    '/searchdocument/codelist/Edinetcode.zip')
_DOC_LIST_URL = (
    'https://api.edinet-fsa.go.jp/api/v2/documents.json')
_DOC_DOWNLOAD_URL = (
    'https://api.edinet-fsa.go.jp/api/v2/documents/{doc_id}')

_DEFAULT_HISTORY_YEARS = 5

DOC_TYPE_ANNUAL = '120'
DOC_TYPE_QUARTERLY = '130'
DOC_TYPE_SEMIANNUAL = '140'
TARGET_DOC_TYPES = {DOC_TYPE_ANNUAL, DOC_TYPE_QUARTERLY,
                     DOC_TYPE_SEMIANNUAL}

_CACHE_TTL_EDINET_CODES = 30
_CACHE_TTL_XBRL = None  # historical filings are immutable
_CACHE_TTL_DOC_LIST_RECENT = 7
_CACHE_TTL_DOC_LIST_HISTORICAL = None
_RECENT_DAYS_THRESHOLD = 30


class EDINETProvider(BronzeProvider):
  """Fetches Japanese financial XBRL filings from EDINET."""

  def __init__(
      self,
      api_key: str,
      min_interval_sec: float = 0.5,
      history_years: int = _DEFAULT_HISTORY_YEARS,
      doc_types: set[str] | None = None,
  ) -> None:
    self._api_key = api_key
    self._min_interval = min_interval_sec
    self._history_years = history_years
    self._doc_types = doc_types or TARGET_DOC_TYPES

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
      cache: BronzeCache | None = None,
  ) -> ProviderResult:
    edinet_dir = out_dir / 'edinet'
    _ensure_dir(edinet_dir / 'xbrl')

    fetched = 0
    skipped = 0
    errors: list[str] = []

    csv_path = edinet_dir / 'EdinetcodeDlInfo.csv'
    csv_cache_key = 'edinet/EdinetcodeDlInfo.csv'
    if force or not _is_fresh(csv_path, refresh_days):
      if (not force and cache is not None
          and cache.resolve(csv_cache_key, csv_path,
                            _CACHE_TTL_EDINET_CODES)):
        fetched += 1
      else:
        try:
          self._fetch_edinet_codes(csv_path)
          if cache is not None:
            cache.put(csv_cache_key, csv_path.read_bytes())
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

    target_edinet_codes: set[str] = set()
    edinet_to_ticker: dict[str, str] = {}
    for ticker in tickers:
      ticker = ticker.strip()
      sec_code = f'{ticker}0' if len(ticker) == 4 else ticker
      edinet_code = sec_to_edinet.get(sec_code)
      if edinet_code is None:
        errors.append(f'Ticker not found in EDINET: {ticker}')
        continue
      target_edinet_codes.add(edinet_code)
      edinet_to_ticker[edinet_code] = ticker

    docs_by_edinet = self._search_all_documents(
        target_edinet_codes, cache=cache)

    for edinet_code, docs in docs_by_edinet.items():
      ticker = edinet_to_ticker.get(edinet_code, edinet_code)
      try:
        n = self._download_filings(
            docs, edinet_code, edinet_dir,
            refresh_days=refresh_days, force=force,
            cache=cache)
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

  def _search_all_documents(
      self,
      target_edinet_codes: set[str],
      *,
      cache: BronzeCache | None = None,
  ) -> dict[str, list[dict]]:
    """Fetch doc lists by date and match all target tickers at once.

    Scans every calendar day for history_years. Each date is fetched
    once regardless of ticker count, and cached for 7 days.
    """
    today = date.today()
    start = date(today.year - self._history_years, 1, 1)
    results: dict[str, list[dict]] = {c: [] for c in target_edinet_codes}
    seen_doc_ids: set[str] = set()

    current = start
    total_days = (today - start).days
    api_calls = 0
    cache_hits = 0

    while current <= today:
      date_str = current.isoformat()

      doc_cache_key = f'edinet/doclist/{date_str}.json'
      days_ago = (today - current).days
      cache_ttl = (_CACHE_TTL_DOC_LIST_RECENT
                   if days_ago <= _RECENT_DAYS_THRESHOLD
                   else _CACHE_TTL_DOC_LIST_HISTORICAL)
      cached = (cache.get_if_fresh(doc_cache_key, cache_ttl)
                if cache is not None else None)
      if cached is not None:
        cache_hits += 1
        try:
          data = json.loads(cached)
        except (ValueError, TypeError):
          data = {}
      else:
        time.sleep(self._min_interval)
        api_calls += 1

        if api_calls % 100 == 0:
          logger.info('EDINET doc search: %d/%d days '
                      '(%d API, %d cache)',
                      api_calls + cache_hits, total_days,
                      api_calls, cache_hits)

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

        if cache is not None:
          cache.put(doc_cache_key,
                    json.dumps(data).encode('utf-8'))

      for doc in data.get('results', []):
        doc_id = doc.get('docID', '')
        edinet_code = doc.get('edinetCode', '')
        if (edinet_code in target_edinet_codes
            and doc.get('docTypeCode') in self._doc_types
            and doc_id not in seen_doc_ids):
          results[edinet_code].append(doc)
          seen_doc_ids.add(doc_id)

      current += timedelta(days=1)

    logger.info('EDINET doc search done: %d API calls, '
                '%d cache hits, %d docs found',
                api_calls, cache_hits,
                sum(len(v) for v in results.values()))
    return results

  def _download_filings(
      self,
      docs: list[dict],
      edinet_code: str,
      edinet_dir: Path,
      *,
      refresh_days: int,
      force: bool,
      cache: BronzeCache | None = None,
  ) -> int:
    fetched = 0

    for doc in docs:
      doc_id = doc['docID']
      period_end = doc.get('periodEnd', 'unknown')
      doc_type = doc.get('docTypeCode', '')

      filename = f'{edinet_code}_{period_end}_{doc_type}.zip'
      out_path = edinet_dir / 'xbrl' / filename

      if not force and _is_fresh(out_path, refresh_days):
        continue

      xbrl_cache_key = f'edinet/xbrl/{filename}'
      if (not force and cache is not None
          and cache.resolve(xbrl_cache_key, out_path,
                            _CACHE_TTL_XBRL)):
        fetched += 1
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
      if cache is not None:
        cache.put(xbrl_cache_key, resp.content)
      fetched += 1

    return fetched


def read_edinet_code_csv(csv_path: Path) -> csv.DictReader:
  """Read EDINET code CSV handling cp932/utf-8 and metadata header."""
  raw = csv_path.read_bytes()
  for encoding in ('utf-8-sig', 'cp932'):
    try:
      text = raw.decode(encoding)
      break
    except (UnicodeDecodeError, ValueError):
      continue
  else:
    return csv.DictReader(io.StringIO(''))

  lines = text.strip().split('\n')
  if lines and 'ＥＤＩＮＥＴコード' not in lines[0]:
    lines = lines[1:]
  return csv.DictReader(io.StringIO('\n'.join(lines)))


def _parse_edinet_codes(csv_path: Path) -> dict[str, str]:
  """Parse EDINET code CSV: securities_code -> edinet_code."""
  if not csv_path.exists():
    return {}

  result: dict[str, str] = {}
  for row in read_edinet_code_csv(csv_path):
    edinet_code = (row.get('EDINET code')
                   or row.get('ＥＤＩＮＥＴコード', '')).strip()
    sec_code = (row.get('Securities code')
                or row.get('証券コード', '')).strip()
    if edinet_code and sec_code:
      result[sec_code] = edinet_code

  return result
