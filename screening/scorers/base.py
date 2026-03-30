"""Base class for screening scorers."""

from abc import ABC
from abc import abstractmethod

import pandas as pd


class Scorer(ABC):
  """A scorer that assigns a 0-100 score to a stock candidate."""

  @abstractmethod
  def score(self, row: pd.Series) -> float:
    """Return a score between 0 and 100."""
