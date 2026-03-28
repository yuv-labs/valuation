"""Composite opportunity score."""


class CompositeScorer:
  """Combine fear and quality into an opportunity score (0-100)."""

  def __init__(self, fear_weight: float = 0.4,
               quality_weight: float = 0.6):
    self._fw = fear_weight
    self._qw = quality_weight

  def score(self, fear: float, quality: float) -> float:
    raw = self._fw * fear + self._qw * quality
    return min(max(raw, 0.0), 100.0)
