"""Base class for screening filters."""

from abc import ABC
from abc import abstractmethod

import pandas as pd


class Filter(ABC):
  """A filter that narrows a DataFrame of stock candidates."""

  @abstractmethod
  def apply(self, df: pd.DataFrame) -> pd.DataFrame:
    """Return rows that pass this filter."""
