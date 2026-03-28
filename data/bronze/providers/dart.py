"""DART (Korea FSS) Bronze provider."""

from __future__ import annotations

from datetime import datetime
import io
import json
import logging
from pathlib import Path
import time
from typing import Any, Iterable, Optional
from xml.etree import ElementTree
import zipfile

import requests

from data.bronze.providers.base import BronzeProvider
from data.bronze.providers.base import ProviderResult
from data.bronze.update import _atomic_write_bytes
from data.bronze.update import _ensure_dir
from data.bronze.update import _is_fresh
from data.bronze.update import _write_meta

logger = logging.getLogger(__name__)

_CORP_CODE_URL = 'https://opendart.fss.or.kr/api/corpCode.xml'
_FINSTATE_URL = (
    'https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json')

# Report codes: Q1, Q2(半期), Q3, Annual
_REPRT_CODES_ALL = ['11013', '11012', '11014', '11011']
_REPRT_CODE_ANNUAL = '11011'
_REPRT_CODE_TO_QUARTER = {
    '11013': 'Q1',
    '11012': 'Q2',
    '11014': 'Q3',
    '11011': 'Q4',
}

# Default: fetch last 5 years for time-series analysis.
_DEFAULT_HISTORY_YEARS = 5


def _default_bsns_years() -> list[str]:
  """Compute business years to fetch.

  If current month is Jan-Mar, the most recent annual report
  (year-1) may not be filed yet, so start from year-2.
  """
  now = datetime.now()
  latest = now.year - 1 if now.month >= 4 else now.year - 2
  return [str(y) for y in range(
      latest - _DEFAULT_HISTORY_YEARS + 1, latest + 1)]


class DARTProvider(BronzeProvider):
  """Fetches Korean financial statements from DART Open API."""

  def __init__(
      self,
      api_key: str,
      min_interval_sec: float = 0.2,
      bsns_years: Optional[list[str]] = None,
      reprt_codes: Optional[list[str]] = None,
  ) -> None:
    self._api_key = api_key
    self._min_interval = min_interval_sec
    self._bsns_years = bsns_years
    self._reprt_codes = reprt_codes or _REPRT_CODES_ALL

  @property
  def name(self) -> str:
    return 'dart'

  def fetch(
      self,
      tickers: Iterable[str],
      out_dir: Path,
      *,
      refresh_days: int = 7,
      force: bool = False,
  ) -> ProviderResult:
    dart_dir = out_dir / 'dart'
    _ensure_dir(dart_dir / 'finstate')

    fetched = 0
    skipped = 0
    errors: list[str] = []

    # 1) Download corp_codes (stock_code -> corp_code mapping)
    corp_xml_path = dart_dir / 'CORPCODE.xml'
    if force or not _is_fresh(corp_xml_path, refresh_days):
      try:
        self._fetch_corp_codes(corp_xml_path)
        fetched += 1
      except (requests.RequestException, OSError) as exc:
        errors.append(f'corp_codes: {exc}')
        return ProviderResult(
            provider_name=self.name,
            fetched=fetched, skipped=skipped,
            errors=errors)
    else:
      skipped += 1

    # 2) Build stock_code -> corp_code map
    stock_to_corp = _parse_corp_codes(corp_xml_path)

    # 3) Fetch finstate for each ticker × year
    years = self._bsns_years or _default_bsns_years()
    tickers_list = list(tickers)

    for stock_code in tickers_list:
      stock_code = stock_code.strip()
      corp_code = stock_to_corp.get(stock_code)
      if corp_code is None:
        errors.append(
            f'Stock code not found in DART: {stock_code}')
        continue

      for year in years:
        for reprt_code in self._reprt_codes:
          qtr = _REPRT_CODE_TO_QUARTER.get(
              reprt_code, reprt_code)
          out_path = (
              dart_dir / 'finstate'
              / f'{corp_code}_{year}_{qtr}.json')
          if not force and _is_fresh(out_path, refresh_days):
            skipped += 1
            continue

          try:
            data = self._fetch_finstate(
                corp_code, year, reprt_code)

            if data.get('status') != '000':
              logger.debug(
                  '%s/%s/%s: %s', stock_code,
                  year, qtr, data.get('message'))
              skipped += 1
              continue

            content = json.dumps(
                data, ensure_ascii=False,
                indent=2).encode('utf-8')
            _atomic_write_bytes(out_path, content)
            _write_meta(out_path, {
                'corp_code': corp_code,
                'stock_code': stock_code,
                'bsns_year': year,
                'reprt_code': reprt_code,
                'quarter': qtr,
            })
            fetched += 1
            time.sleep(self._min_interval)
          except (requests.RequestException, OSError) as exc:
            errors.append(
                f'{stock_code}/{year}/{qtr}: {exc}')

    return ProviderResult(
        provider_name=self.name,
        fetched=fetched, skipped=skipped,
        errors=errors)

  def _fetch_corp_codes(self, out_path: Path) -> None:
    """Download and extract CORPCODE.xml from zip."""
    resp = requests.get(
        _CORP_CODE_URL,
        params={'crtfc_key': self._api_key},
        timeout=30)
    resp.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
      xml_name = zf.namelist()[0]
      xml_bytes = zf.read(xml_name)

    _atomic_write_bytes(out_path, xml_bytes)

  def _fetch_finstate(
      self,
      corp_code: str,
      bsns_year: str,
      reprt_code: str = _REPRT_CODE_ANNUAL,
  ) -> dict[str, Any]:
    """Fetch financial statement for one company/year/quarter."""
    params = {
        'crtfc_key': self._api_key,
        'corp_code': corp_code,
        'bsns_year': bsns_year,
        'reprt_code': reprt_code,
        'fs_div': 'CFS',
    }
    resp = requests.get(_FINSTATE_URL, params=params, timeout=30)
    resp.raise_for_status()
    result: dict[str, Any] = resp.json()
    return result


def _parse_corp_codes(xml_path: Path) -> dict[str, str]:
  """Parse CORPCODE.xml -> {stock_code: corp_code}."""
  tree = ElementTree.parse(xml_path)  # noqa: S314
  root = tree.getroot()
  result: dict[str, str] = {}
  for item in root.findall('list'):
    corp_code_el = item.find('corp_code')
    stock_code_el = item.find('stock_code')
    if (corp_code_el is not None
        and stock_code_el is not None
        and corp_code_el.text
        and stock_code_el.text
        and stock_code_el.text.strip()):
      result[stock_code_el.text.strip()] = (
          corp_code_el.text.strip())
  return result
