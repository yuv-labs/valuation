"""Shared ticker classification utilities."""
import re

_KR_TICKER_RE = re.compile(r'^\d{4}[A-Z0-9]\d$')


def is_kr_ticker(ticker: str) -> bool:
  """Return True if ticker matches KR format (e.g. 000270, 0126Z0)."""
  return bool(_KR_TICKER_RE.match(str(ticker)))
