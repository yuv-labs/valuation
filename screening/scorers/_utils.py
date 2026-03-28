"""Shared utilities for scorers and filters."""

from typing import Any, Optional

import pandas as pd


def safe_float(val: Any) -> Optional[float]:
  """Convert a Series value to float, returning None if NA."""
  if val is None or pd.isna(val):
    return None
  return float(val)
