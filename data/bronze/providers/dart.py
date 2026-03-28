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

# Annual report
_REPRT_CODE_ANNUAL = '11011'


class DARTProvider(BronzeProvider):
  """Fetches Korean financial statements from DART Open API."""

  def __init__(
      self,
      api_key: str,
      min_interval_sec: float = 0.2,
  ) -> None:
    self._api_key = api_key
    self._min_interval = min_interval_sec

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

    # 3) Fetch finstate for each ticker (stock_code)
    tickers_list = list(tickers)
    for stock_code in tickers_list:
      stock_code = stock_code.strip()
      corp_code = stock_to_corp.get(stock_code)
      if corp_code is None:
        errors.append(
            f'Stock code not found in DART: {stock_code}')
        continue

      out_path = dart_dir / 'finstate' / f'{corp_code}.json'
      if not force and _is_fresh(out_path, refresh_days):
        skipped += 1
        continue

      try:
        data = self._fetch_finstate(corp_code)
        content = json.dumps(
            data, ensure_ascii=False, indent=2).encode('utf-8')
        _atomic_write_bytes(out_path, content)
        _write_meta(out_path, {
            'corp_code': corp_code,
            'stock_code': stock_code,
            'fetched_at_utc': '',
        })
        fetched += 1
        time.sleep(self._min_interval)
      except (requests.RequestException, OSError) as exc:
        errors.append(f'{stock_code}: {exc}')

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
      bsns_year: Optional[str] = None,
  ) -> dict[str, Any]:
    """Fetch full financial statement for one company."""
    if bsns_year is None:
      bsns_year = str(datetime.now().year - 1)

    params = {
        'crtfc_key': self._api_key,
        'corp_code': corp_code,
        'bsns_year': bsns_year,
        'reprt_code': _REPRT_CODE_ANNUAL,
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
