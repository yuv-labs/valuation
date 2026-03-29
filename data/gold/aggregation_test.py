"""Tests for Gold aggregation — public interface only."""

import pandas as pd
import pytest

from data.gold.aggregation import TTMCalculator
from data.gold.aggregation import YTDToQuarterlyConverter


def _make_ytd_facts(cik10: str, metric: str,
                    rows: list[dict]) -> pd.DataFrame:
  """Build a facts DataFrame for testing.

  Each row dict should have: fy, fp, fiscal_quarter, val, filed.
  """
  records = []
  qtr_month = {'Q1': '03-31', 'Q2': '06-30', 'Q3': '09-30', 'FY': '12-31'}
  for r in rows:
    fp = r['fp']
    end = pd.Timestamp(f"{r['fy']}-{qtr_month[fp]}")
    records.append({
        'cik10': cik10,
        'metric': metric,
        'val': r['val'],
        'end': end,
        'filed': pd.Timestamp(r['filed']),
        'fy': str(r['fy']),
        'fp': fp,
        'fiscal_year': r['fy'],
        'fiscal_quarter': r.get('fiscal_quarter', 'Q4' if fp == 'FY' else fp),
        'tag': f'tag_{metric}',
    })
  return pd.DataFrame(records)


class TestYTDToQuarterlyConverter:
  """YTDToQuarterlyConverter.convert() public interface tests."""

  def test_q1_uses_raw_value(self):
    """Q1 has no prior quarter to subtract — q_val == val."""
    facts = _make_ytd_facts('AAPL', 'CFO', [{
        'fy': 2024, 'fp': 'Q1', 'val': 100.0,
        'filed': '2024-05-01',
    }])
    result = YTDToQuarterlyConverter().convert(facts)

    assert len(result) == 1
    assert result.iloc[0]['q_val'] == 100.0

  def test_q2_subtracts_q1_ytd(self):
    """Q2 quarterly = Q2_YTD - Q1_YTD."""
    facts = _make_ytd_facts('AAPL', 'CFO', [
        {'fy': 2024, 'fp': 'Q1', 'val': 100.0, 'filed': '2024-05-01'},
        {'fy': 2024, 'fp': 'Q2', 'val': 250.0, 'filed': '2024-08-01'},
    ])
    result = YTDToQuarterlyConverter().convert(facts)
    q2 = result[result['fiscal_quarter'] == 'Q2']

    assert len(q2) == 1
    assert q2.iloc[0]['q_val'] == 150.0

  def test_fy_subtracts_q3_ytd(self):
    """FY (Q4) quarterly = FY_YTD - Q3_YTD."""
    facts = _make_ytd_facts('AAPL', 'CFO', [
        {'fy': 2024, 'fp': 'Q1', 'val': 100.0, 'filed': '2024-05-01'},
        {'fy': 2024, 'fp': 'Q2', 'val': 250.0, 'filed': '2024-08-01'},
        {'fy': 2024, 'fp': 'Q3', 'val': 400.0, 'filed': '2024-11-01'},
        {'fy': 2024, 'fp': 'FY', 'val': 600.0, 'filed': '2025-02-01',
         'fiscal_quarter': 'Q4'},
    ])
    result = YTDToQuarterlyConverter().convert(facts)
    q4 = result[result['fiscal_quarter'] == 'Q4']

    assert len(q4) == 1
    assert q4.iloc[0]['q_val'] == 200.0

  def test_pit_only_uses_prior_quarter_filed_before(self):
    """PIT: Q2 ignores Q1 filed after Q2's filed date."""
    facts = _make_ytd_facts('AAPL', 'CFO', [
        # Q1 filed AFTER Q2 — should not be used for subtraction
        {'fy': 2024, 'fp': 'Q1', 'val': 100.0, 'filed': '2024-09-01'},
        {'fy': 2024, 'fp': 'Q2', 'val': 250.0, 'filed': '2024-08-01'},
    ])
    result = YTDToQuarterlyConverter().convert(facts)
    q2 = result[result['fiscal_quarter'] == 'Q2']

    # Q1 filed after Q2, so Q2 should use raw value (no subtraction)
    assert len(q2) == 1
    assert q2.iloc[0]['q_val'] == 250.0

  def test_non_ytd_metric_passes_through(self):
    """Non-YTD metrics (e.g., SHARES) pass val as q_val directly."""
    facts = _make_ytd_facts('AAPL', 'SHARES', [{
        'fy': 2024, 'fp': 'Q1', 'val': 1_000_000.0,
        'filed': '2024-05-01',
    }])
    result = YTDToQuarterlyConverter().convert(facts)

    assert len(result) == 1
    assert result.iloc[0]['q_val'] == 1_000_000.0

  def test_negative_q_val_set_to_nan_when_abs(self):
    """For abs=True metrics (CAPEX), negative q_val → NaN."""
    facts = _make_ytd_facts('AAPL', 'CAPEX', [
        {'fy': 2024, 'fp': 'Q1', 'val': 200.0, 'filed': '2024-05-01'},
        # Q2 YTD < Q1 YTD → negative quarterly (restatement)
        {'fy': 2024, 'fp': 'Q2', 'val': 150.0, 'filed': '2024-08-01'},
    ])
    result = YTDToQuarterlyConverter().convert(facts)
    q2 = result[result['fiscal_quarter'] == 'Q2']

    assert len(q2) == 1
    assert pd.isna(q2.iloc[0]['q_val'])

  def test_empty_input(self):
    result = YTDToQuarterlyConverter().convert(pd.DataFrame())
    assert result.empty

  def test_unknown_metric_ignored(self):
    """Metrics not in METRIC_SPECS are silently skipped."""
    facts = _make_ytd_facts('AAPL', 'UNKNOWN_METRIC', [{
        'fy': 2024, 'fp': 'Q1', 'val': 42.0,
        'filed': '2024-05-01',
    }])
    result = YTDToQuarterlyConverter().convert(facts)
    assert result.empty


class TestTTMCalculator:
  """TTMCalculator.calculate() public interface tests."""

  def _make_quarterly(self, cik10: str, metric: str,
                      rows: list[dict]) -> pd.DataFrame:
    records = []
    qtr_month = {
        'Q1': '03-31', 'Q2': '06-30', 'Q3': '09-30', 'Q4': '12-31',
    }
    for r in rows:
      fq = r['fiscal_quarter']
      end = pd.Timestamp(f"{r['fy']}-{qtr_month[fq]}")
      records.append({
          'cik10': cik10,
          'metric': metric,
          'q_val': r['q_val'],
          'end': end,
          'filed': pd.Timestamp(r['filed']),
          'fy': str(r['fy']),
          'fp': r.get('fp', fq),
          'fiscal_year': r['fy'],
          'fiscal_quarter': fq,
          'tag': f'tag_{metric}',
      })
    return pd.DataFrame(records)

  def test_ttm_sums_four_quarters(self):
    """TTM = sum of 4 consecutive quarters."""
    df = self._make_quarterly('AAPL', 'CFO', [
        {'fy': 2023, 'fiscal_quarter': 'Q1',
         'q_val': 100, 'filed': '2023-05-01'},
        {'fy': 2023, 'fiscal_quarter': 'Q2',
         'q_val': 110, 'filed': '2023-08-01'},
        {'fy': 2023, 'fiscal_quarter': 'Q3',
         'q_val': 120, 'filed': '2023-11-01'},
        {'fy': 2023, 'fiscal_quarter': 'Q4',
         'q_val': 130, 'filed': '2024-02-01'},
    ])
    result = TTMCalculator().calculate(df)
    q4 = result[result['fiscal_quarter'] == 'Q4']

    assert len(q4) == 1
    assert q4.iloc[0]['ttm_val'] == pytest.approx(460.0)

  def test_ttm_nan_when_fewer_than_four_quarters(self):
    """TTM is NaN when not all 4 quarters are available."""
    df = self._make_quarterly('AAPL', 'CFO', [
        {'fy': 2023, 'fiscal_quarter': 'Q1',
         'q_val': 100, 'filed': '2023-05-01'},
        {'fy': 2023, 'fiscal_quarter': 'Q2',
         'q_val': 110, 'filed': '2023-08-01'},
    ])
    result = TTMCalculator().calculate(df)

    assert result['ttm_val'].isna().all()

  def test_ttm_crosses_year_boundary(self):
    """TTM at Q2 2024 sums Q3 2023 + Q4 2023 + Q1 2024 + Q2 2024."""
    df = self._make_quarterly('AAPL', 'CFO', [
        {'fy': 2023, 'fiscal_quarter': 'Q1',
         'q_val': 90, 'filed': '2023-05-01'},
        {'fy': 2023, 'fiscal_quarter': 'Q2',
         'q_val': 100, 'filed': '2023-08-01'},
        {'fy': 2023, 'fiscal_quarter': 'Q3',
         'q_val': 110, 'filed': '2023-11-01'},
        {'fy': 2023, 'fiscal_quarter': 'Q4',
         'q_val': 120, 'filed': '2024-02-01'},
        {'fy': 2024, 'fiscal_quarter': 'Q1',
         'q_val': 130, 'filed': '2024-05-01'},
        {'fy': 2024, 'fiscal_quarter': 'Q2',
         'q_val': 140, 'filed': '2024-08-01'},
    ])
    result = TTMCalculator().calculate(df)
    q2_2024 = result[
        (result['fiscal_year'] == 2024) &
        (result['fiscal_quarter'] == 'Q2')]

    # TTM = Q3_2023(110) + Q4_2023(120) + Q1_2024(130) + Q2_2024(140)
    assert q2_2024.iloc[0]['ttm_val'] == pytest.approx(500.0)

  def test_pit_only_uses_filed_before_current(self):
    """TTM only includes quarters filed on or before the current row's filed."""
    df = self._make_quarterly('AAPL', 'CFO', [
        {'fy': 2023, 'fiscal_quarter': 'Q1',
         'q_val': 100, 'filed': '2023-05-01'},
        {'fy': 2023, 'fiscal_quarter': 'Q2',
         'q_val': 110, 'filed': '2023-08-01'},
        {'fy': 2023, 'fiscal_quarter': 'Q3',
         'q_val': 120, 'filed': '2023-11-01'},
        # Q4 filed very late — after Q1 2024
        {'fy': 2023, 'fiscal_quarter': 'Q4',
         'q_val': 130, 'filed': '2024-06-01'},
        {'fy': 2024, 'fiscal_quarter': 'Q1',
         'q_val': 140, 'filed': '2024-05-01'},
    ])
    result = TTMCalculator().calculate(df)
    q1_2024 = result[
        (result['fiscal_year'] == 2024) &
        (result['fiscal_quarter'] == 'Q1')]

    # Q4 2023 filed after Q1 2024 → not available → TTM is NaN
    assert pd.isna(q1_2024.iloc[0]['ttm_val'])

  def test_empty_input(self):
    result = TTMCalculator().calculate(pd.DataFrame())
    assert result.empty
