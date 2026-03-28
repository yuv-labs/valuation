"""Base class for Bronze data providers."""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class ProviderResult:
  """Summary of a provider fetch run."""
  provider_name: str
  fetched: int = 0
  skipped: int = 0
  errors: list[str] = field(default_factory=list)


class BronzeProvider(ABC):
  """Abstract base for Bronze layer data sources."""

  @property
  @abstractmethod
  def name(self) -> str:
    """Short identifier for this provider (e.g. 'sec', 'stooq')."""

  @abstractmethod
  def fetch(
      self,
      tickers: Iterable[str],
      out_dir: Path,
      *,
      refresh_days: int = 7,
      force: bool = False,
  ) -> ProviderResult:
    """
    Fetch raw data for the given tickers and write to out_dir.

    Args:
      tickers: Ticker symbols to fetch data for.
      out_dir: Root output directory (provider creates subdirs).
      refresh_days: Skip if file newer than N days. 0 = always.
      force: Always re-download regardless of freshness.

    Returns:
      ProviderResult summarising what happened.
    """
