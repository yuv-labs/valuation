"""Tests for screening filters — public interface only."""

import pandas as pd

from screening.filters.base import Filter
from screening.filters.moat_existence import MoatExistenceFilter
from screening.filters.moat_health import MoatHealthFilter
from screening.filters.opportunity import OpportunityFilter


def _make_row(**kwargs):
  """Create a single-row DataFrame. All values must be explicit."""
  return pd.DataFrame([{'ticker': 'TEST', **kwargs}])


def _make_df(rows):
  """Create DataFrame from list of row-dicts."""
  return pd.concat([_make_row(**r) for r in rows], ignore_index=True)


class TestMoatExistenceFilter:

  def test_is_filter(self):
    assert isinstance(MoatExistenceFilter(), Filter)

  def test_passes_when_all_three_met(self):
    df = _make_row(
        roic_3y_avg=0.15, roic_3y_min=0.09,
        fcf_ni_ratio_3y_avg=0.95)
    assert len(MoatExistenceFilter().apply(df)) == 1

  def test_rejects_when_roic_avg_too_low(self):
    df = _make_row(
        roic_3y_avg=0.08, roic_3y_min=0.09,
        fcf_ni_ratio_3y_avg=0.95)
    assert len(MoatExistenceFilter().apply(df)) == 0

  def test_rejects_when_roic_min_too_low(self):
    df = _make_row(
        roic_3y_avg=0.15, roic_3y_min=0.05,
        fcf_ni_ratio_3y_avg=0.95)
    assert len(MoatExistenceFilter().apply(df)) == 0

  def test_rejects_when_fcf_ni_too_low(self):
    df = _make_row(
        roic_3y_avg=0.15, roic_3y_min=0.09,
        fcf_ni_ratio_3y_avg=0.5)
    assert len(MoatExistenceFilter().apply(df)) == 0

  def test_rejects_when_any_metric_is_nan(self):
    df = _make_row(
        roic_3y_avg=0.15, roic_3y_min=None,
        fcf_ni_ratio_3y_avg=0.95)
    assert len(MoatExistenceFilter().apply(df)) == 0

  def test_boundary_values_not_passing(self):
    """Exactly at threshold should not pass (> not >=)."""
    df = _make_row(
        roic_3y_avg=0.10, roic_3y_min=0.07,
        fcf_ni_ratio_3y_avg=0.8)
    assert len(MoatExistenceFilter().apply(df)) == 0


class TestMoatHealthFilter:

  def test_is_filter(self):
    assert isinstance(MoatHealthFilter(), Filter)

  def test_passes_with_2_of_3_signals(self):
    df = _make_row(
        gp_margin=0.45, gp_margin_std_3y=0.03,
        debt_to_equity=1.5)
    assert len(MoatHealthFilter(min_signals=2).apply(df)) == 1

  def test_rejects_with_only_1_signal(self):
    df = _make_row(
        gp_margin=0.45, gp_margin_std_3y=0.10,
        debt_to_equity=1.5)
    assert len(MoatHealthFilter(min_signals=2).apply(df)) == 0

  def test_passes_all_3_signals(self):
    df = _make_row(
        gp_margin=0.45, gp_margin_std_3y=0.03,
        debt_to_equity=0.5)
    assert len(MoatHealthFilter(min_signals=2).apply(df)) == 1

  def test_rejects_low_margin_company(self):
    df = _make_row(
        gp_margin=0.15, gp_margin_std_3y=0.10,
        debt_to_equity=1.5)
    assert len(MoatHealthFilter(min_signals=2).apply(df)) == 0


class TestOpportunityFilter:

  def test_is_filter(self):
    assert isinstance(OpportunityFilter(), Filter)

  def test_passes_with_low_pe_and_big_drop(self):
    df = _make_row(
        pe_ratio=5.0, pct_from_52w_high=-0.30,
        fcf_yield=0.03, pe_avg_5y=20.0)
    assert len(OpportunityFilter(min_signals=2).apply(df)) == 1

  def test_passes_with_high_fcf_yield_and_pe_below_avg(self):
    df = _make_row(
        pe_ratio=12.0, pct_from_52w_high=-0.10,
        fcf_yield=0.07, pe_avg_5y=20.0)
    assert len(OpportunityFilter(min_signals=2).apply(df)) == 1

  def test_rejects_with_no_signals(self):
    df = _make_row(
        pe_ratio=25.0, pct_from_52w_high=-0.05,
        fcf_yield=0.02, pe_avg_5y=20.0)
    assert len(OpportunityFilter(min_signals=2).apply(df)) == 0

  def test_skips_pe_avg_when_nan(self):
    """When pe_avg_5y is NaN, PE-vs-avg signal is skipped."""
    df = _make_row(
        pe_ratio=5.0, pct_from_52w_high=-0.30,
        fcf_yield=0.02, pe_avg_5y=None)
    assert len(OpportunityFilter(min_signals=2).apply(df)) == 1

  def test_rejects_negative_pe(self):
    """Negative PE (loss-making) should not count as low PE."""
    df = _make_row(
        pe_ratio=-5.0, pct_from_52w_high=-0.05,
        fcf_yield=0.02, pe_avg_5y=20.0)
    assert len(OpportunityFilter(min_signals=2).apply(df)) == 0


class TestTrackABPipeline:
  """Track A → Track B pipeline narrows correctly."""

  def test_moat_then_opportunity(self):
    rows = [
        # Strong moat + cheap
        {'ticker': 'MOAT_CHEAP',
         'roic_3y_avg': 0.18, 'roic_3y_min': 0.12,
         'fcf_ni_ratio_3y_avg': 1.0,
         'gp_margin': 0.45, 'gp_margin_std_3y': 0.02,
         'debt_to_equity': 0.3,
         'pe_ratio': 8.0, 'pct_from_52w_high': -0.25,
         'fcf_yield': 0.07, 'pe_avg_5y': 18.0},
        # Strong moat + expensive
        {'ticker': 'MOAT_PRICEY',
         'roic_3y_avg': 0.20, 'roic_3y_min': 0.15,
         'fcf_ni_ratio_3y_avg': 1.1,
         'gp_margin': 0.50, 'gp_margin_std_3y': 0.01,
         'debt_to_equity': 0.2,
         'pe_ratio': 35.0, 'pct_from_52w_high': -0.02,
         'fcf_yield': 0.02, 'pe_avg_5y': 30.0},
        # No moat
        {'ticker': 'NO_MOAT',
         'roic_3y_avg': 0.05, 'roic_3y_min': 0.02,
         'fcf_ni_ratio_3y_avg': 0.4,
         'gp_margin': 0.15, 'gp_margin_std_3y': 0.12,
         'debt_to_equity': 2.5,
         'pe_ratio': 4.0, 'pct_from_52w_high': -0.40,
         'fcf_yield': 0.10, 'pe_avg_5y': 10.0},
    ]
    df = _make_df(rows)

    # Track A: moat filters
    df_a = MoatExistenceFilter().apply(df)
    df_a = MoatHealthFilter(min_signals=2).apply(df_a)
    assert set(df_a['ticker']) == {'MOAT_CHEAP', 'MOAT_PRICEY'}

    # Track B: opportunity filter on Track A output
    df_b = OpportunityFilter(min_signals=2).apply(df_a)
    assert len(df_b) == 1
    assert df_b.iloc[0]['ticker'] == 'MOAT_CHEAP'
