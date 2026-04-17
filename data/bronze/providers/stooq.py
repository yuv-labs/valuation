"""Stooq daily price CSV Bronze provider."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, TYPE_CHECKING

import requests

from data.bronze.providers.base import BronzeProvider
from data.bronze.providers.base import ProviderResult
from data.bronze.update import _ensure_dir
from data.bronze.update import _fetch_bytes
from data.bronze.update import _is_fresh
from data.bronze.update import _save_if_needed

if TYPE_CHECKING:
  from data.bronze.cache import BronzeCache

STOOQ_DAILY_CSV_URL_TMPL = 'https://stooq.com/q/d/l/?s={symbol}&i=d'

_CACHE_TTL_DAILY = 1


class StooqProvider(BronzeProvider):
  """Fetches daily OHLCV CSV from Stooq."""

  @property
  def name(self) -> str:
    return 'stooq'

  def fetch(
      self,
      tickers: Iterable[str],
      out_dir: Path,
      *,
      refresh_days: int = 7,
      force: bool = False,
      cache: BronzeCache | None = None,
  ) -> ProviderResult:
    stooq_dir = out_dir / 'stooq' / 'daily'
    _ensure_dir(stooq_dir)

    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; equity-analysis/1.0)',
    }

    fetched = 0
    skipped = 0
    errors: list[str] = []

    for sym in tickers:
      sym_lower = sym.strip().lower()
      url = STOOQ_DAILY_CSV_URL_TMPL.format(symbol=sym_lower)
      out_path = stooq_dir / f'{sym_lower}.csv'

      if not force and _is_fresh(out_path, refresh_days):
        skipped += 1
        continue

      cache_key = f'stooq/daily/{sym_lower}.csv'
      if (not force and cache is not None
          and cache.resolve(cache_key, out_path, _CACHE_TTL_DAILY)):
        fetched += 1
        continue

      try:
        content, fr = _fetch_bytes(session, url, headers=headers)
        did = _save_if_needed(
            out_path, content, fr, refresh_days=refresh_days, force=force)
        if did:
          if cache is not None:
            cache.put(cache_key, content)
          fetched += 1
        else:
          skipped += 1
      except (requests.RequestException, OSError) as e:
        errors.append(f'{sym}: {e}')

    return ProviderResult(
        provider_name=self.name,
        fetched=fetched,
        skipped=skipped,
        errors=errors,
    )
