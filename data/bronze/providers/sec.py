"""SEC EDGAR Bronze provider."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import requests

from data.bronze.providers.base import BronzeProvider
from data.bronze.providers.base import ProviderResult
from data.bronze.update import _ensure_dir
from data.bronze.update import _fetch_bytes
from data.bronze.update import _is_fresh
from data.bronze.update import _load_ticker_map
from data.bronze.update import _save_if_needed
from data.bronze.update import RateLimiter

SEC_COMPANY_TICKERS_URL = 'https://www.sec.gov/files/company_tickers.json'
SEC_COMPANYFACTS_URL_TMPL = (
    'https://data.sec.gov/api/xbrl/companyfacts/CIK{cik10}.json')
SEC_SUBMISSIONS_URL_TMPL = 'https://data.sec.gov/submissions/CIK{cik10}.json'


class SECProvider(BronzeProvider):
  """Fetches SEC companyfacts and optional submissions."""

  def __init__(
      self,
      user_agent: str,
      min_interval_sec: float = 0.2,
      include_submissions: bool = False,
  ) -> None:
    self._user_agent = user_agent
    self._min_interval_sec = min_interval_sec
    self._include_submissions = include_submissions

  @property
  def name(self) -> str:
    return 'sec'

  def fetch(
      self,
      tickers: Iterable[str],
      out_dir: Path,
      *,
      refresh_days: int = 7,
      force: bool = False,
  ) -> ProviderResult:
    sec_dir = out_dir / 'sec'
    _ensure_dir(sec_dir / 'companyfacts')
    _ensure_dir(sec_dir / 'submissions')

    session = requests.Session()
    headers = {
        'User-Agent': self._user_agent,
        'Accept-Encoding': 'gzip, deflate',
    }
    limiter = RateLimiter(min_interval_sec=self._min_interval_sec)

    fetched = 0
    skipped = 0
    errors: list[str] = []

    # 1) company_tickers.json
    tickers_path = sec_dir / 'company_tickers.json'
    if force or not _is_fresh(tickers_path, refresh_days):
      content, fr = _fetch_bytes(
          session,
          SEC_COMPANY_TICKERS_URL,
          headers=headers,
          limiter=limiter,
      )
      did = _save_if_needed(
          tickers_path, content, fr, refresh_days=refresh_days, force=force)
      if did:
        fetched += 1
      else:
        skipped += 1
    else:
      skipped += 1

    ticker_map = _load_ticker_map(tickers_path.read_bytes())

    # 2) companyfacts (+ optional submissions) per ticker
    for ticker in tickers:
      ticker = ticker.upper().strip()
      if ticker not in ticker_map:
        errors.append(f'Ticker not found in SEC map: {ticker}')
        continue

      cik10 = ticker_map[ticker]

      # companyfacts
      cf_url = SEC_COMPANYFACTS_URL_TMPL.format(cik10=cik10)
      cf_path = sec_dir / 'companyfacts' / f'CIK{cik10}.json'
      if force or not _is_fresh(cf_path, refresh_days):
        content, fr = _fetch_bytes(
            session, cf_url, headers=headers, limiter=limiter)
        did = _save_if_needed(
            cf_path, content, fr, refresh_days=refresh_days, force=force)
        if did:
          fetched += 1
        else:
          skipped += 1
      else:
        skipped += 1

      # submissions
      if self._include_submissions:
        sub_url = SEC_SUBMISSIONS_URL_TMPL.format(cik10=cik10)
        sub_path = sec_dir / 'submissions' / f'CIK{cik10}.json'
        if force or not _is_fresh(sub_path, refresh_days):
          content, fr = _fetch_bytes(
              session, sub_url, headers=headers, limiter=limiter)
          did = _save_if_needed(
              sub_path, content, fr, refresh_days=refresh_days, force=force)
          if did:
            fetched += 1
          else:
            skipped += 1
        else:
          skipped += 1

    return ProviderResult(
        provider_name=self.name,
        fetched=fetched,
        skipped=skipped,
        errors=errors,
    )
