"""Tests for screening filters — public interface only."""

import pandas as pd

from screening.filters.base import Filter
from screening.filters.growth import GrowthFilter
from screening.filters.moat import MoatFilter
from screening.filters.undervalued import UndervaluedFilter


def _make_row(**kwargs):
  """Create a single-row DataFrame with given columns."""
  defaults = {
      'ticker': 'TEST',
      'pe_ratio': 15.0,
      'pb_ratio': 2.0,
      'pct_from_52w_high': -10.0,
      'fcf_yield': 0.03,
      'roic': 0.12,
      'roe': 0.15,
      'op_margin': 0.20,
      'gp_margin': 0.40,
      'gp_margin_std_3y': 0.02,
      'revenue_cagr_3y': 0.08,
      'debt_to_equity': 0.5,
      'fcf_positive_3y': True,
  }
  defaults.update(kwargs)
  return pd.DataFrame([defaults])


def _make_df(rows):
  """Create DataFrame from list of row-dicts."""
  return pd.concat([_make_row(**r) for r in rows], ignore_index=True)


class TestFilterInterface:
  """All filters must implement the Filter ABC."""

  def test_undervalued_is_filter(self):
    assert isinstance(UndervaluedFilter(), Filter)

  def test_moat_is_filter(self):
    assert isinstance(MoatFilter(), Filter)

  def test_growth_is_filter(self):
    assert isinstance(GrowthFilter(), Filter)


class TestUndervaluedFilter:

  def test_passes_stock_with_low_pe_and_big_drop(self):
    df = _make_row(pe_ratio=5.0, pct_from_52w_high=-30.0)
    result = UndervaluedFilter(min_signals=2).apply(df)
    assert len(result) == 1

  def test_rejects_stock_with_no_signals(self):
    df = _make_row(
        pe_ratio=30.0,
        pct_from_52w_high=-5.0,
        fcf_yield=0.01,
    )
    result = UndervaluedFilter(min_signals=2).apply(df)
    assert len(result) == 0

  def test_counts_high_fcf_yield_as_signal(self):
    df = _make_row(
        pe_ratio=5.0,
        fcf_yield=0.08,
        pct_from_52w_high=-5.0,
    )
    result = UndervaluedFilter(min_signals=2).apply(df)
    assert len(result) == 1


class TestMoatFilter:

  def test_passes_high_roic_and_roe(self):
    df = _make_row(roic=0.15, roe=0.18)
    result = MoatFilter(min_signals=2).apply(df)
    assert len(result) == 1

  def test_rejects_low_quality(self):
    df = _make_row(roic=0.03, roe=0.05, op_margin=0.02)
    result = MoatFilter(min_signals=2).apply(df)
    assert len(result) == 0


class TestGrowthFilter:

  def test_passes_growing_with_low_debt(self):
    df = _make_row(revenue_cagr_3y=0.10, debt_to_equity=0.3)
    result = GrowthFilter(min_signals=1).apply(df)
    assert len(result) == 1

  def test_rejects_shrinking_and_leveraged(self):
    df = _make_row(
        revenue_cagr_3y=-0.05,
        debt_to_equity=2.5,
        fcf_positive_3y=False,
    )
    result = GrowthFilter(min_signals=2).apply(df)
    assert len(result) == 0


class TestFilterChaining:
  """Filters can be applied sequentially to narrow candidates."""

  def test_pipeline_reduces_candidates(self):
    rows = [
        # Good candidate: low PE, big drop, high ROIC/ROE, growing
        {'ticker': 'GOOD', 'pe_ratio': 6.0,
         'pct_from_52w_high': -35.0, 'fcf_yield': 0.08,
         'roic': 0.18, 'roe': 0.20,
         'revenue_cagr_3y': 0.12, 'debt_to_equity': 0.3},
        # Overvalued
        {'ticker': 'EXPENSIVE', 'pe_ratio': 50.0,
         'pct_from_52w_high': -2.0, 'fcf_yield': 0.01,
         'roic': 0.05, 'roe': 0.04,
         'revenue_cagr_3y': -0.05, 'debt_to_equity': 3.0},
        # Cheap but no moat
        {'ticker': 'CHEAP_JUNK', 'pe_ratio': 4.0,
         'pct_from_52w_high': -40.0, 'fcf_yield': 0.10,
         'roic': 0.02, 'roe': 0.03, 'op_margin': 0.03,
         'gp_margin_std_3y': 0.15,
         'revenue_cagr_3y': -0.10, 'debt_to_equity': 4.0},
    ]
    df = _make_df(rows)

    df = UndervaluedFilter(min_signals=2).apply(df)
    df = MoatFilter(min_signals=2).apply(df)
    df = GrowthFilter(min_signals=1).apply(df)

    assert len(df) == 1
    assert df.iloc[0]['ticker'] == 'GOOD'
