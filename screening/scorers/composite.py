"""Composite opportunity score."""


class CompositeScorer:
  """Combine two component scores into a weighted opportunity score (0-100).

  Default weights are tuned for Track B (opportunity scanner):
  70% fear (price attractiveness) + 30% moat (quality tiebreaker).
  Track A companies already passed moat filters, so fear dominates.
  """

  def __init__(self, fear_weight: float = 0.7,
               moat_weight: float = 0.3):
    self._fw = fear_weight
    self._mw = moat_weight

  def score(self, fear: float, moat: float) -> float:
    raw = self._fw * fear + self._mw * moat
    return min(max(raw, 0.0), 100.0)
