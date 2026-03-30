"""Tests for screening scorers — public interface only."""

import pandas as pd

from screening.scorers.base import Scorer
from screening.scorers.composite import CompositeScorer
from screening.scorers.fear import FearScorer
from screening.scorers.quality import QualityScorer


def _make_series(**kwargs):
  return pd.Series(kwargs)


class TestScorerInterface:

  def test_fear_scorer_is_scorer(self):
    assert isinstance(FearScorer(), Scorer)

  def test_quality_scorer_is_scorer(self):
    assert isinstance(QualityScorer(), Scorer)

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


class TestQualityScorer:

  def test_returns_float_between_0_and_100(self):
    row = _make_series(
        roic=0.15,
        roe=0.18,
        revenue_cagr_3y=0.10,
        debt_to_equity=0.3,
        fcf_positive_3y=True,
    )
    score = QualityScorer().score(row)
    assert isinstance(score, float)
    assert 0 <= score <= 100

  def test_high_quality_for_strong_company(self):
    row = _make_series(
        roic=0.25,
        roe=0.22,
        revenue_cagr_3y=0.15,
        debt_to_equity=0.2,
        fcf_positive_3y=True,
    )
    assert QualityScorer().score(row) >= 60

  def test_low_quality_for_weak_company(self):
    row = _make_series(
        roic=0.02,
        roe=0.03,
        revenue_cagr_3y=-0.05,
        debt_to_equity=3.0,
        fcf_positive_3y=False,
    )
    assert QualityScorer().score(row) <= 20


class TestCompositeScorer:

  def test_returns_float_between_0_and_100(self):
    score = CompositeScorer().score(fear=50.0, quality=70.0)
    assert isinstance(score, float)
    assert 0 <= score <= 100

  def test_high_fear_and_quality_gives_high_opportunity(self):
    score = CompositeScorer().score(fear=80.0, quality=90.0)
    assert score >= 70

  def test_low_fear_low_quality_gives_low_opportunity(self):
    score = CompositeScorer().score(fear=10.0, quality=10.0)
    assert score <= 20
