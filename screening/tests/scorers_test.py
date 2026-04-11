"""Tests for screening scorers — public interface only."""

import pandas as pd

from screening.scorers.base import Scorer
from screening.scorers.composite import CompositeScorer
from screening.scorers.fear import FearScorer
from screening.scorers.moat import MoatScorer


def _make_series(**kwargs):
  return pd.Series(kwargs)


class TestScorerInterface:

  def test_fear_scorer_is_scorer(self):
    assert isinstance(FearScorer(), Scorer)

  def test_moat_scorer_is_scorer(self):
    assert isinstance(MoatScorer(), Scorer)

  def test_composite_is_not_row_scorer(self):
    """CompositeScorer is a combiner, not a row-level Scorer."""
    assert not isinstance(CompositeScorer(), Scorer)


class TestFearScorer:

  def test_returns_float_between_0_and_100(self):
    row = _make_series(
        pct_from_52w_high=-30.0,
        pe_ratio=8.0,
        pe_avg_5y=20.0,
        fcf_yield=0.08,
    )
    score = FearScorer().score(row)
    assert isinstance(score, float)
    assert 0 <= score <= 100

  def test_high_fear_for_crashed_stock(self):
    row = _make_series(
        pct_from_52w_high=-50.0,
        pe_ratio=5.0,
        pe_avg_5y=25.0,
        fcf_yield=0.12,
    )
    assert FearScorer().score(row) >= 60

  def test_low_fear_for_normal_stock(self):
    row = _make_series(
        pct_from_52w_high=-5.0,
        pe_ratio=20.0,
        pe_avg_5y=22.0,
        fcf_yield=0.02,
    )
    assert FearScorer().score(row) <= 20


class TestMoatScorer:

  def test_returns_float_between_0_and_100(self):
    row = _make_series(
        roic_3y_avg=0.15,
        roic_3y_min=0.10,
        fcf_ni_ratio_3y_avg=0.9,
        gp_margin=0.40,
        gp_margin_std_3y=0.03,
        debt_to_equity=0.5,
    )
    score = MoatScorer().score(row)
    assert isinstance(score, float)
    assert 0 <= score <= 100

  def test_high_score_for_strong_moat(self):
    row = _make_series(
        roic_3y_avg=0.25,
        roic_3y_min=0.18,
        fcf_ni_ratio_3y_avg=1.2,
        gp_margin=0.55,
        gp_margin_std_3y=0.01,
        debt_to_equity=0.2,
    )
    assert MoatScorer().score(row) >= 80

  def test_low_score_for_weak_moat(self):
    row = _make_series(
        roic_3y_avg=0.05,
        roic_3y_min=0.02,
        fcf_ni_ratio_3y_avg=0.3,
        gp_margin=0.15,
        gp_margin_std_3y=0.12,
        debt_to_equity=2.0,
    )
    assert MoatScorer().score(row) <= 20

  def test_handles_nan_gracefully(self):
    row = _make_series(
        roic_3y_avg=None,
        roic_3y_min=None,
        fcf_ni_ratio_3y_avg=None,
        gp_margin=None,
        gp_margin_std_3y=None,
        debt_to_equity=None,
    )
    assert MoatScorer().score(row) == 0.0

  def test_partial_data(self):
    row = _make_series(
        roic_3y_avg=0.18,
        roic_3y_min=None,
        fcf_ni_ratio_3y_avg=1.0,
        gp_margin=0.45,
        gp_margin_std_3y=None,
        debt_to_equity=0.4,
    )
    score = MoatScorer().score(row)
    assert score > 0
    assert score <= 100


class TestCompositeScorer:

  def test_returns_float_between_0_and_100(self):
    score = CompositeScorer().score(fear=50.0, moat=70.0)
    assert isinstance(score, float)
    assert 0 <= score <= 100

  def test_high_fear_and_moat_gives_high_opportunity(self):
    score = CompositeScorer().score(fear=80.0, moat=90.0)
    assert score >= 70

  def test_low_fear_low_moat_gives_low_opportunity(self):
    score = CompositeScorer().score(fear=10.0, moat=10.0)
    assert score <= 20

  def test_default_weights_favor_fear(self):
    """Default: 70% fear + 30% moat."""
    score = CompositeScorer().score(fear=100.0, moat=0.0)
    assert abs(score - 70.0) < 0.01
