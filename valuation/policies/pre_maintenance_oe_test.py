import pandas as pd
import pytest

from valuation.domain.types import FundamentalsSlice
from valuation.domain.types import PolicyOutput
from valuation.domain.types import QuarterData
from valuation.policies.pre_maintenance_oe import AvgCFO
from valuation.policies.pre_maintenance_oe import NormalizedMarginOE
from valuation.policies.pre_maintenance_oe import NormalizedROICOE
from valuation.policies.pre_maintenance_oe import TTMPreMaintenanceOE


def _make_quarters(
    start_year: int,
    num_quarters: int,
    cfo_ttm_values: list[float],
    capex_ttm_values: list[float],
    shares_values: list[float],
) -> list[QuarterData]:
  """Helper to create QuarterData list."""
  quarters: list[QuarterData] = []
  quarter_map = ['Q1', 'Q2', 'Q3', 'Q4']
  end_months = [3, 6, 9, 12]

  for i in range(num_quarters):
    year = start_year + i // 4
    q_idx = i % 4
    qd = QuarterData(
        fiscal_year=year,
        fiscal_quarter=quarter_map[q_idx],
        end=pd.Timestamp(year=year, month=end_months[q_idx], day=28),
        filed=pd.Timestamp(year=year, month=end_months[q_idx], day=28) +
        pd.DateOffset(days=45),
        cfo_ttm=cfo_ttm_values[i],
        capex_ttm=capex_ttm_values[i],
        shares=shares_values[i],
    )
    quarters.append(qd)
  return quarters


class TestTTMPreMaintenanceOE:
  """Tests for TTMPreMaintenanceOE policy."""

  def test_returns_cfo_ttm(self):
    """Returns latest CFO TTM value."""
    quarters = _make_quarters(
        start_year=2022,
        num_quarters=4,
        cfo_ttm_values=[100.0, 110.0, 120.0, 130.0],
        capex_ttm_values=[20.0, 22.0, 24.0, 26.0],
        shares_values=[100.0, 100.0, 100.0, 100.0],
    )
    data = FundamentalsSlice(
        ticker='TEST',
        as_of_date=pd.Timestamp('2023-01-15'),
        quarters=quarters,
    )

    policy = TTMPreMaintenanceOE()
    result = policy.compute(data)

    assert isinstance(result, PolicyOutput)
    assert result.value == 130.0
    assert result.diag['pre_maint_oe_method'] == 'ttm'
    assert result.diag['cfo_ttm'] == 130.0


class TestAvgCFO:
  """Tests for AvgCFO policy (weighted yearly average)."""

  def test_weighted_avg_3y(self):
    """Weighted average with 3:2:1 weights over 3 years."""
    quarters = _make_quarters(
        start_year=2022,
        num_quarters=16,
        cfo_ttm_values=[100.0] * 4 + [150.0] * 4 + [200.0] * 4 + [250.0] * 4,
        capex_ttm_values=[20.0] * 16,
        shares_values=[100.0] * 16,
    )
    data = FundamentalsSlice(
        ticker='TEST',
        as_of_date=pd.Timestamp('2026-01-15'),
        quarters=quarters,
    )

    policy = AvgCFO()
    result = policy.compute(data)

    assert result.diag['pre_maint_oe_method'] == 'weighted_avg_3y'
    assert result.diag['years_used'] == [1, 2, 3]
    assert result.diag['weights_used'] == [3.0, 2.0, 1.0]
    assert result.value > 0

  def test_fallback_to_ttm_with_no_data(self):
    """Falls back to TTM when no quarters in any year bucket."""
    quarters = _make_quarters(
        start_year=2025,
        num_quarters=4,
        cfo_ttm_values=[100.0, 110.0, 120.0, 130.0],
        capex_ttm_values=[20.0, 22.0, 24.0, 26.0],
        shares_values=[100.0] * 4,
    )
    data = FundamentalsSlice(
        ticker='TEST',
        as_of_date=pd.Timestamp('2020-01-15'),
        quarters=quarters,
    )

    policy = AvgCFO()
    result = policy.compute(data)

    assert result.value == 130.0
    assert result.diag['fallback'] == 'ttm'

  def test_partial_years_uses_available(self):
    """Uses available year buckets when some are missing."""
    quarters = _make_quarters(
        start_year=2024,
        num_quarters=4,
        cfo_ttm_values=[100.0, 110.0, 120.0, 130.0],
        capex_ttm_values=[20.0, 22.0, 24.0, 26.0],
        shares_values=[100.0] * 4,
    )
    data = FundamentalsSlice(
        ticker='TEST',
        as_of_date=pd.Timestamp('2025-01-15'),
        quarters=quarters,
    )

    policy = AvgCFO()
    result = policy.compute(data)

    assert result.value == 115.0


class TestNormalizedMarginOE:
  """Tests for NormalizedMarginOE policy."""

  def test_normalized_fcf(self):
    """Calculates FCF based on revenue, target margin, and reinvestment rate."""
    quarters = _make_quarters(
        start_year=2024,
        num_quarters=1,
        cfo_ttm_values=[100.0],
        capex_ttm_values=[20.0],
        shares_values=[100.0],
    )
    data = FundamentalsSlice(
        ticker='TEST',
        as_of_date=pd.Timestamp('2024-03-31'),
        quarters=quarters,
    )
    # Mocking latest_revenue
    data.latest_revenue = 1000.0

    # 1000 * 0.10 * (1 - 0.20) = 100 * 0.8 = 80
    policy = NormalizedMarginOE(target_margin=0.10, reinvestment_rate=0.20)
    result = policy.compute(data)

    assert result.value == pytest.approx(80.0)
    assert result.diag['pre_maint_oe_method'] == 'normalized_margin'
    assert result.diag['normalized_nopat'] == 100.0


class TestNormalizedROICOE:
  """Tests for NormalizedROICOE policy."""

  def test_normalized_fcf(self):
    """Calculates FCF based on IC, target ROIC, and reinvestment rate."""
    quarters = _make_quarters(
        start_year=2024,
        num_quarters=1,
        cfo_ttm_values=[100.0],
        capex_ttm_values=[20.0],
        shares_values=[100.0],
    )
    data = FundamentalsSlice(
        ticker='TEST',
        as_of_date=pd.Timestamp('2024-03-31'),
        quarters=quarters,
    )
    # Mocking latest_invested_capital
    data.latest_invested_capital = 500.0

    # 500 * 0.20 * (1 - 0.30) = 100 * 0.7 = 70
    policy = NormalizedROICOE(target_roic=0.20, reinvestment_rate=0.30)
    result = policy.compute(data)

    assert result.value == pytest.approx(70.0)
    assert result.diag['pre_maint_oe_method'] == 'normalized_roic'
    assert result.diag['normalized_nopat'] == 100.0
