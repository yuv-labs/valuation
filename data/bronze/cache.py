"""Shared file cache for Bronze API responses across git worktrees."""

from __future__ import annotations

import os
from pathlib import Path

from data.bronze.update import _atomic_write_bytes
from data.bronze.update import _ensure_dir
from data.bronze.update import _is_fresh


def _default_cache_dir() -> Path:
  xdg = os.environ.get('XDG_CACHE_HOME', '')
  base = Path(xdg) if xdg else Path.home() / '.cache'
  return base / 'valuation' / 'bronze'


class BronzeCache:
  """File-based cache that mirrors bronze/out/ directory structure.

  Stored at ~/.cache/valuation/bronze/ (or $XDG_CACHE_HOME/valuation/bronze/).
  Multiple git worktrees share this cache to avoid redundant API calls.
  """

  def __init__(self, cache_dir: Path | None = None) -> None:
    self._dir = cache_dir or _default_cache_dir()

  @property
  def cache_dir(self) -> Path:
    return self._dir

  def get_if_fresh(
      self,
      key: str,
      max_age_days: int | None = None,
  ) -> bytes | None:
    """Return cached bytes if fresh, else None.

    Args:
      key: Relative path within bronze/out/.
      max_age_days: Max age in days. None = permanent.
    """
    path = self._dir / key
    if not path.exists():
      return None
    if max_age_days is not None and not _is_fresh(path, max_age_days):
      return None
    return path.read_bytes()

  def put(self, key: str, content: bytes) -> None:
    """Store bytes in cache with atomic write."""
    path = self._dir / key
    _ensure_dir(path.parent)
    _atomic_write_bytes(path, content)

  def resolve(
      self,
      key: str,
      local_path: Path,
      max_age_days: int | None = None,
  ) -> bool:
    """Copy cached data to local_path if fresh. Returns True on cache hit."""
    cached = self.get_if_fresh(key, max_age_days)
    if cached is None:
      return False
    _ensure_dir(local_path.parent)
    _atomic_write_bytes(local_path, cached)
    return True
