"""KRX (Korea Exchange) daily price Bronze provider via pykrx."""

from __future__ import annotations

from datetime import datetime
from datetime import timedelta
from pathlib import Path
from typing import Iterable

import pandas as pd

from data.bronze.providers.base import BronzeProvider
from data.bronze.providers.base import ProviderResult
from data.bronze.update import _ensure_dir
from data.bronze.update import _is_fresh


def _fetch_ohlcv(
    ticker: str,
    start: str,
    end: str,
) -> pd.DataFrame:
  """Fetch OHLCV from KRX via pykrx. Separated for mocking."""
  from pykrx import stock as krx  # pylint: disable=import-outside-toplevel
  result: pd.DataFrame = krx.get_market_ohlcv(start, end, ticker)
  return result


class KRXProvider(BronzeProvider):
  """Fetches daily OHLCV from Korea Exchange via pykrx."""

  def __init__(self, history_days: int = 365 * 5) -> None:
    self._history_days = history_days

  @property
  def name(self) -> str:
    return 'krx'

  def fetch(
      self,
      tickers: Iterable[str],
      out_dir: Path,
      *,
      refresh_days: int = 7,
      force: bool = False,
  ) -> ProviderResult:
    krx_dir = out_dir / 'krx' / 'daily'
    _ensure_dir(krx_dir)

    end = datetime.now().strftime('%Y%m%d')
    start = (datetime.now()
             - timedelta(days=self._history_days)).strftime('%Y%m%d')

    fetched = 0
    skipped = 0
    errors: list[str] = []

    for ticker in tickers:
      ticker = ticker.strip()
      out_path = krx_dir / f'{ticker}.csv'

      if not force and _is_fresh(out_path, refresh_days):
        skipped += 1
        continue

      try:
        ohlcv = _fetch_ohlcv(ticker, start, end)
        if ohlcv.empty:
          errors.append(f'{ticker}: no data from KRX')
          continue

        ohlcv.to_csv(out_path, encoding='utf-8')
        fetched += 1
      except Exception as exc:  # pylint: disable=broad-except
        errors.append(f'{ticker}: {exc}')

    return ProviderResult(
        provider_name=self.name,
        fetched=fetched,
        skipped=skipped,
        errors=errors,
    )
