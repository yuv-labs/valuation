"""
bronze_pipeline.py

Bronze (raw) ingestion pipeline for:
- SEC company_tickers.json
- SEC XBRL Company Facts (companyfacts)
- (Optional) SEC submissions (filing metadata)
- Stooq daily prices CSV

Design goals:
- Raw-only (no transformation): store bytes as received.
- Minimize repeated API calls: skip if file exists and is fresh.
- Write sidecar metadata: fetched_at_utc, url, status_code, size.

References:
- SEC XBRL Company Facts endpoint:
  https://data.sec.gov/api/xbrl/companyfacts/CIK##########.json
- SEC submissions endpoint:
  https://data.sec.gov/submissions/CIK##########.json
- SEC access policy: max 10 req/s + declare User-Agent
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
from datetime import timezone
import json
from pathlib import Path
import re
import time
from typing import Any, Iterable, Optional, TYPE_CHECKING

import requests

if TYPE_CHECKING:
  from data.bronze.cache import BronzeCache

# ---------------------------
# Config
# ---------------------------

SEC_COMPANY_TICKERS_URL = 'https://www.sec.gov/files/company_tickers.json'

SEC_COMPANYFACTS_URL_TMPL = (
    'https://data.sec.gov/api/xbrl/companyfacts/CIK{cik10}.json')
SEC_SUBMISSIONS_URL_TMPL = 'https://data.sec.gov/submissions/CIK{cik10}.json'

# Commonly used by Stooq download button; widely used in practice.
STOOQ_DAILY_CSV_URL_TMPL = 'https://stooq.com/q/d/l/?s={symbol}&i=d'
STOOQ_DAILY_CSV_URL_TMPL_APIKEY = (
    'https://stooq.com/q/d/l/?s={symbol}&i=d&apikey={apikey}')


@dataclass(frozen=True)
class FetchResult:
  url: str
  status_code: int
  nbytes: int
  fetched_at_utc: str


def _utc_now_iso() -> str:
  return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _ensure_dir(path: Path) -> None:
  path.mkdir(parents=True, exist_ok=True)


def _is_fresh(path: Path, refresh_days: int) -> bool:
  if not path.exists():
    return False
  if refresh_days <= 0:
    return False
  age_sec = time.time() - path.stat().st_mtime
  return age_sec < refresh_days * 86400


def _atomic_write_bytes(path: Path, content: bytes) -> None:
  tmp = path.with_suffix(path.suffix + '.tmp')
  tmp.write_bytes(content)
  tmp.replace(path)


def _write_meta(path: Path, meta: dict[str, Any]) -> None:
  meta_path = path.with_suffix(path.suffix + '.meta.json')
  _atomic_write_bytes(
      meta_path,
      json.dumps(meta, ensure_ascii=False, indent=2).encode('utf-8'))


class RateLimiter:
  """Simple min-interval rate limiter."""

  def __init__(self, min_interval_sec: float) -> None:
    self._min_interval = float(min_interval_sec)
    self._last = 0.0

  def wait(self) -> None:
    now = time.time()
    sleep_for = self._min_interval - (now - self._last)
    if sleep_for > 0:
      time.sleep(sleep_for)
    self._last = time.time()


class HTTPStatusError(requests.HTTPError):
  """HTTP error with structured status code for caller inspection."""

  def __init__(self, status_code: int, url: str, body: str):
    super().__init__(f'HTTP {status_code} for {url}: {body}')
    self.status_code = status_code


def _sanitize_url(url: str) -> str:
  """Strip apikey query parameter from URL for safe logging/storage."""
  if 'apikey=' not in url:
    return url
  return re.sub(r'[&?]apikey=[^&]*', '', url)


def _fetch_bytes(
    session: requests.Session,
    url: str,
    *,
    headers: dict[str, str],
    timeout_sec: int = 30,
    retries: int = 3,
    backoff_sec: float = 1.0,
    limiter: Optional[RateLimiter] = None,
) -> tuple[bytes, FetchResult]:
  safe_url = _sanitize_url(url)
  last_err: Optional[Exception] = None
  for attempt in range(retries):
    try:
      if limiter:
        limiter.wait()

      resp = session.get(url, headers=headers, timeout=timeout_sec)
      status = int(resp.status_code)
      content = resp.content

      if status >= 400:
        raise HTTPStatusError(status, safe_url, resp.text[:200])

      return content, FetchResult(
          url=safe_url,
          status_code=status,
          nbytes=len(content),
          fetched_at_utc=_utc_now_iso(),
      )
    except HTTPStatusError as e:
      if e.status_code < 500 and e.status_code != 429:
        raise  # 4xx client errors — don't retry.
      last_err = e
      if attempt < retries - 1:
        time.sleep(backoff_sec * (2**attempt))
      else:
        break
      continue
    except Exception as e:  # pylint: disable=broad-except
      last_err = e
      if attempt < retries - 1:
        time.sleep(backoff_sec * (2**attempt))
      else:
        break
  assert last_err is not None
  raise last_err


def _load_ticker_map(company_tickers_json: bytes) -> dict[str, str]:
  """
  SEC company_tickers.json format:
    {'0':{'cik_str':1652044,'ticker':'GOOGL','title':'Alphabet Inc.'}, ...}
  Returns: { 'GOOGL': '0001652044', ... }
  """
  raw = json.loads(company_tickers_json.decode('utf-8'))
  out: dict[str, str] = {}
  for _, v in raw.items():
    ticker = str(v.get('ticker', '')).upper().strip()
    cik = str(v.get('cik_str', '')).strip()
    if not ticker or not cik:
      continue
    cik10 = cik.zfill(10)
    out[ticker] = cik10
  return out


def _normalize_stooq_symbol(sym: str) -> str:
  # Stooq expects lowercase in many examples; accept either.
  return sym.strip().lower()


def _is_valid_stooq_csv(content: bytes) -> bool:
  """Check if content is a valid Stooq CSV (not an HTML error page)."""
  if not content:
    return False
  first_line = content.split(b'\n', 1)[0].decode('utf-8', errors='ignore')
  return first_line.startswith('Date,')


def _save_if_needed(
    path: Path,
    content: bytes,
    result: FetchResult,
    *,
    refresh_days: int,
    force: bool,
) -> bool:
  """
  Returns True if a download/write happened, False if skipped.
  """
  if not force and _is_fresh(path, refresh_days):
    return False

  _atomic_write_bytes(path, content)
  _write_meta(
      path, {
          'url': result.url,
          'status_code': result.status_code,
          'nbytes': result.nbytes,
          'fetched_at_utc': result.fetched_at_utc,
      })
  return True


def _iter_tickers(values: Iterable[str]) -> Iterable[str]:
  for v in values:
    # allow comma separated
    for t in v.split(','):
      t = t.strip()
      if t:
        yield t.upper()


_CACHE_TTL_SEC_TICKERS = 30
_CACHE_TTL_SEC_FILINGS = 7
_CACHE_TTL_STOOQ_DAILY = 1


def run(
    *,
    out_dir: Path,
    tickers: Iterable[str],
    stooq_symbols: Iterable[str],
    include_submissions: bool,
    refresh_days: int,
    force: bool,
    sec_user_agent: str,
    sec_min_interval_sec: float,
    stooq_apikey: Optional[str] = None,
    cache: Optional['BronzeCache'] = None,
) -> None:
  _ensure_dir(out_dir)

  sec_dir = out_dir / 'sec'
  stooq_dir = out_dir / 'stooq' / 'daily'
  _ensure_dir(sec_dir / 'companyfacts')
  _ensure_dir(sec_dir / 'submissions')
  _ensure_dir(stooq_dir)

  session = requests.Session()

  # SEC headers (declare User-Agent)
  sec_headers = {
      'User-Agent': sec_user_agent,
      'Accept-Encoding': 'gzip, deflate',
  }
  sec_limiter = RateLimiter(min_interval_sec=sec_min_interval_sec)

  # 1) company_tickers.json
  tickers_path = sec_dir / 'company_tickers.json'
  tickers_cache_key = 'sec/company_tickers.json'
  if force or (not _is_fresh(tickers_path, refresh_days)):
    if (not force and cache is not None
        and cache.resolve(
            tickers_cache_key, tickers_path, _CACHE_TTL_SEC_TICKERS)):
      print(f'[SEC] [cache] saved {tickers_path}')
    else:
      content, fr = _fetch_bytes(
          session, SEC_COMPANY_TICKERS_URL,
          headers=sec_headers, limiter=sec_limiter)
      did = _save_if_needed(
          tickers_path, content, fr,
          refresh_days=refresh_days, force=force)
      if did:
        if cache is not None:
          cache.put(tickers_cache_key, content)
        print(f'[SEC] saved {tickers_path} ({fr.nbytes} bytes)')
  else:
    print(f'[SEC] skip fresh {tickers_path}')

  ticker_map = _load_ticker_map(tickers_path.read_bytes())

  # 2) companyfacts (+ optional submissions)
  for ticker in tickers:
    if ticker not in ticker_map:
      print(f'[WARN] ticker not found in SEC map: {ticker}')
      continue

    cik10 = ticker_map[ticker]

    # companyfacts
    cf_url = SEC_COMPANYFACTS_URL_TMPL.format(cik10=cik10)
    cf_path = sec_dir / 'companyfacts' / f'CIK{cik10}.json'
    cf_cache_key = f'sec/companyfacts/CIK{cik10}.json'
    if force or (not _is_fresh(cf_path, refresh_days)):
      if (not force and cache is not None
          and cache.resolve(
              cf_cache_key, cf_path, _CACHE_TTL_SEC_FILINGS)):
        print(f'[SEC] [cache] saved companyfacts {ticker}')
      else:
        try:
          content, fr = _fetch_bytes(
              session, cf_url,
              headers=sec_headers, limiter=sec_limiter)
        except HTTPStatusError as e:
          if e.status_code == 404:
            print(f'[SEC] skip {ticker} (no companyfacts)')
            continue
          raise
        did = _save_if_needed(
            cf_path, content, fr,
            refresh_days=refresh_days, force=force)
        if did:
          if cache is not None:
            cache.put(cf_cache_key, content)
          print(f'[SEC] saved companyfacts '
                f'{ticker} -> {cf_path.name}')
    else:
      print(f'[SEC] skip fresh companyfacts {ticker}')

    # submissions (optional)
    if include_submissions:
      sub_url = SEC_SUBMISSIONS_URL_TMPL.format(cik10=cik10)
      sub_path = sec_dir / 'submissions' / f'CIK{cik10}.json'
      sub_cache_key = f'sec/submissions/CIK{cik10}.json'
      if force or (not _is_fresh(sub_path, refresh_days)):
        if (not force and cache is not None
            and cache.resolve(
                sub_cache_key, sub_path,
                _CACHE_TTL_SEC_FILINGS)):
          print(f'[SEC] [cache] saved submissions {ticker}')
        else:
          content, fr = _fetch_bytes(
              session, sub_url,
              headers=sec_headers, limiter=sec_limiter)
          did = _save_if_needed(
              sub_path, content, fr,
              refresh_days=refresh_days, force=force)
          if did:
            if cache is not None:
              cache.put(sub_cache_key, content)
            print(f'[SEC] saved submissions '
                  f'{ticker} -> {sub_path.name}')
      else:
        print(f'[SEC] skip fresh submissions {ticker}')

  # 3) Stooq daily price CSV
  px_headers = {
      'User-Agent':
          'Mozilla/5.0 (compatible; valuation-research/1.0)'
  }
  for sym in stooq_symbols:
    sym_n = _normalize_stooq_symbol(sym)
    if stooq_apikey:
      url = STOOQ_DAILY_CSV_URL_TMPL_APIKEY.format(
          symbol=sym_n, apikey=stooq_apikey)
    else:
      url = STOOQ_DAILY_CSV_URL_TMPL.format(symbol=sym_n)
    out_path = stooq_dir / f'{sym_n}.csv'

    if not force and _is_fresh(out_path, refresh_days):
      print(f'[STOOQ] skip fresh {out_path.name}')
      continue

    stooq_cache_key = f'stooq/daily/{sym_n}.csv'
    if (not force and cache is not None
        and cache.resolve(
            stooq_cache_key, out_path, _CACHE_TTL_STOOQ_DAILY)):
      print(f'[STOOQ] [cache] saved {out_path.name}')
      continue

    content, fr = _fetch_bytes(
        session, url, headers=px_headers,
        timeout_sec=30, retries=3, backoff_sec=1.0)
    if not _is_valid_stooq_csv(content):
      print(f'[STOOQ] [WARN] invalid CSV for {sym_n}, skipping')
      continue
    did = _save_if_needed(
        out_path, content, fr,
        refresh_days=refresh_days, force=force)
    if did:
      if cache is not None:
        cache.put(stooq_cache_key, content)
      print(f'[STOOQ] saved {out_path.name} '
            f'({fr.nbytes} bytes)')


def _build_argparser() -> argparse.ArgumentParser:
  p = argparse.ArgumentParser(description='Bronze raw ingestion: SEC + Stooq')
  p.add_argument('--out',
                 default='data/bronze/out',
                 help='output root directory')
  p.add_argument('--tickers',
                 nargs='*',
                 help='US tickers for SEC (e.g., GOOGL MSFT)')
  p.add_argument('--tickers-file',
                 type=Path,
                 help='Path to file containing ticker list (one per line)')
  p.add_argument('--include-submissions',
                 action='store_true',
                 help='also fetch SEC submissions JSON')
  p.add_argument(
      '--refresh-days',
      type=int,
      default=7,
      help='skip download if file newer than N days (0 disables freshness)')
  p.add_argument('--force',
                 action='store_true',
                 help='always re-download regardless of freshness')
  p.add_argument(
      '--sec-user-agent',
      required=True,
      help='SEC requires declared User-Agent (company/contact).'
      ' (e.g., "StevenJobs valuation research (stevenjobs@gmail.com)")',
  )
  # SEC max is 10 req/s; keep safer default: 0.2s => 5 req/s
  p.add_argument('--sec-min-interval',
                 type=float,
                 default=0.2,
                 help='min seconds between SEC requests')
  p.add_argument('--stooq-apikey',
                 type=str,
                 default=None,
                 help='Stooq API key for CSV downloads')
  p.add_argument('--cache-dir',
                 type=Path,
                 default=None,
                 help='Shared cache directory')
  p.add_argument('--no-cache',
                 action='store_true',
                 help='Disable shared cache')
  return p


def load_tickers_from_file(path: Path) -> list[str]:
  """Load tickers from file (one per line, # for comments)."""
  if not path.exists():
    raise FileNotFoundError(f'Tickers file not found: {path}')

  with open(path, 'r', encoding='utf-8') as f:
    tickers = [
        line.strip()
        for line in f
        if line.strip() and not line.strip().startswith('#')
    ]

  if not tickers:
    raise ValueError('No tickers found in file')

  return tickers


if __name__ == '__main__':
  from data.bronze.cache import BronzeCache

  args = _build_argparser().parse_args()

  shared_cache: Optional[BronzeCache] = None
  if not args.no_cache:
    shared_cache = BronzeCache(cache_dir=args.cache_dir)
    print(f'[cache] {shared_cache.cache_dir}')

  if args.tickers_file:
    tickers_list = load_tickers_from_file(args.tickers_file)
    print(f'Loaded {len(tickers_list)} tickers from {args.tickers_file}')
  elif args.tickers:
    tickers_list = args.tickers
  else:
    tickers_list = ['GOOGL']
    print('Using default ticker: GOOGL')

  stooq_list = [f'{t}.US' for t in tickers_list]
  run(
      out_dir=Path(args.out),
      tickers=list(_iter_tickers(tickers_list)),
      stooq_symbols=list(_iter_tickers(stooq_list)),
      include_submissions=bool(args.include_submissions),
      refresh_days=int(args.refresh_days),
      force=bool(args.force),
      sec_user_agent=str(args.sec_user_agent),
      sec_min_interval_sec=float(args.sec_min_interval),
      stooq_apikey=args.stooq_apikey,
      cache=shared_cache,
  )
