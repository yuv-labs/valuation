import math

import pytest

from valuation.engine.dcf import compute_intrinsic_value
from valuation.engine.dcf import compute_pv_explicit
from valuation.engine.dcf import compute_terminal_value


class TestComputePVExplicit:
  """Tests for compute_pv_explicit function."""

  def test_normal_case(self):
    """Standard 3-year forecast with positive growth.

    Manual calculation:
    Year 1: OE=105.0, Shares=98.0, OEPS=1.071, PV=0.974
    Year 2: OE=109.2, Shares=96.04, OEPS=1.137, PV=0.940
    Year 3: OE=112.5, Shares=94.12, OEPS=1.195, PV=0.898
    Total PV: 2.812
    """
    pv, _, final_shares = compute_pv_explicit(
        oe0=100.0,
        sh0=100.0,
        buyback_rate=0.02,
        growth_path=[0.05, 0.04, 0.03],
        discount_rate=0.10,
    )

    assert pv == pytest.approx(2.812, abs=0.001)
    assert final_shares == pytest.approx(94.12, abs=0.01)

  def test_zero_growth(self):
    """Forecast with zero growth rates.

    Manual calculation (OE=100, Shares=100 constant):
    Year 1: OEPS=1.0, PV=1.0/1.1=0.909
    Year 2: OEPS=1.0, PV=1.0/1.21=0.826
    Year 3: OEPS=1.0, PV=1.0/1.331=0.751
    Total PV: 2.487
    """
    pv, _, final_shares = compute_pv_explicit(
        oe0=100.0,
        sh0=100.0,
        buyback_rate=0.0,
        growth_path=[0.0, 0.0, 0.0],
        discount_rate=0.10,
    )

    assert pv == pytest.approx(2.487, abs=0.001)
    assert final_shares == pytest.approx(100.0, rel=1e-6)

  def test_negative_growth(self):
    """Declining business scenario.

    Manual calculation (OE declines, Shares constant):
    Year 1: OE=95.0, OEPS=0.95, PV=0.864
    Year 2: OE=92.15, OEPS=0.922, PV=0.761
    Year 3: OE=91.23, OEPS=0.912, PV=0.685
    Total PV: 2.310
    """
    pv, _, _ = compute_pv_explicit(
        oe0=100.0,
        sh0=100.0,
        buyback_rate=0.0,
        growth_path=[-0.05, -0.03, -0.01],
        discount_rate=0.10,
    )

    assert pv == pytest.approx(2.310, abs=0.001)

  def test_high_buyback_rate(self):
    """10% annual buyback rate.

    Manual calculation:
    Year 1: OE=105.0, Sh=90.0, OEPS=1.167, PV=1.061
    Year 2: OE=110.3, Sh=81.0, OEPS=1.361, PV=1.125
    Year 3: OE=115.8, Sh=72.9, OEPS=1.588, PV=1.193
    Total PV: 3.379
    """
    pv, _, final_shares = compute_pv_explicit(
        oe0=100.0,
        sh0=100.0,
        buyback_rate=0.1,
        growth_path=[0.05, 0.05, 0.05],
        discount_rate=0.10,
    )

    assert pv == pytest.approx(3.379, abs=0.001)
    assert final_shares == pytest.approx(72.9, abs=0.1)

  def test_zero_shares_edge_case(self):
    """Extreme buyback rate causing zero shares."""
    pv, _, final_shares = compute_pv_explicit(
        oe0=100.0,
        sh0=100.0,
        buyback_rate=1.0,
        growth_path=[0.05],
        discount_rate=0.10,
    )

    assert math.isnan(pv)
    assert final_shares == 0.0

  def test_single_year_forecast(self):
    """Forecast with just one year.

    Manual calculation:
    Year 1: OE=108.0, Sh=98.0, OEPS=1.102, PV=1.002
    """
    pv, final_oeps, final_shares = compute_pv_explicit(
        oe0=100.0,
        sh0=100.0,
        buyback_rate=0.02,
        growth_path=[0.08],
        discount_rate=0.10,
    )

    assert pv == pytest.approx(1.002, abs=0.001)
    assert final_shares == pytest.approx(98.0, rel=1e-6)
    assert final_oeps == pytest.approx(1.102, abs=0.001)

  def test_long_forecast_period(self):
    """10-year forecast period."""
    growth_path = [0.05] * 10
    pv, _, final_shares = compute_pv_explicit(
        oe0=100.0,
        sh0=100.0,
        buyback_rate=0.02,
        growth_path=growth_path,
        discount_rate=0.10,
    )

    assert pv > 0
    assert final_shares == pytest.approx(100 * 0.98**10, rel=1e-6)


class TestComputeTerminalValue:
  """Tests for compute_terminal_value function."""

  def test_normal_case(self):
    """Standard Gordon growth calculation.

    Manual calculation:
    TV = (10.0 * 1.03) / (0.10 - 0.03) = 10.3 / 0.07 = 147.1429
    PV = 147.1429 / (1.10^5) = 147.1429 / 1.61051 = 91.364
    """
    tv = compute_terminal_value(
        final_oeps=10.0,
        g_terminal=0.03,
        discount_rate=0.10,
        final_year=5,
    )

    assert tv == pytest.approx(91.364, abs=0.001)

  def test_zero_terminal_growth(self):
    """Zero perpetual growth rate.

    Manual calculation:
    TV = (10.0 * 1.0) / (0.10 - 0.0) = 10.0 / 0.10 = 100.0
    PV = 100.0 / (1.10^5) = 100.0 / 1.61051 = 62.092
    """
    tv = compute_terminal_value(
        final_oeps=10.0,
        g_terminal=0.0,
        discount_rate=0.10,
        final_year=5,
    )

    assert tv == pytest.approx(62.092, abs=0.001)

  def test_boundary_condition(self):
    """Terminal growth close to but less than discount rate."""
    tv = compute_terminal_value(
        final_oeps=10.0,
        g_terminal=0.099,
        discount_rate=0.10,
        final_year=5,
    )

    assert tv > 0

  def test_invalid_g_equals_r(self):
    """Terminal growth equals discount rate - invalid."""
    tv = compute_terminal_value(
        final_oeps=10.0,
        g_terminal=0.10,
        discount_rate=0.10,
        final_year=5,
    )

    assert math.isnan(tv)

  def test_invalid_g_greater_than_r(self):
    """Terminal growth exceeds discount rate - invalid."""
    tv = compute_terminal_value(
        final_oeps=10.0,
        g_terminal=0.12,
        discount_rate=0.10,
        final_year=5,
    )

    assert math.isnan(tv)

  def test_different_final_years(self):
    """Terminal value with different forecast periods."""
    tv_3y = compute_terminal_value(10.0, 0.03, 0.10, 3)
    tv_5y = compute_terminal_value(10.0, 0.03, 0.10, 5)
    tv_10y = compute_terminal_value(10.0, 0.03, 0.10, 10)

    assert tv_3y > tv_5y > tv_10y

  def test_exit_multiple_terminal(self):
    """Terminal value using exit multiple method."""
    tv = compute_terminal_value(
        final_oeps=10.0,
        g_terminal=0.03,  # Should be ignored
        discount_rate=0.10,
        final_year=5,
        tv_method='multiple',
        tv_param=7.0,
    )
    # Expected: 10.0 * 7.0 = 70.0
    # PV: 70.0 / (1.10^5) = 43.4645
    assert tv == pytest.approx(43.464, abs=0.001)

  def test_invalid_tv_method(self):
    """Invalid terminal method should return nan."""
    tv = compute_terminal_value(
        final_oeps=10.0,
        g_terminal=0.03,
        discount_rate=0.10,
        final_year=5,
        tv_method='unknown',
    )
    assert math.isnan(tv)



class TestComputeIntrinsicValue:
  """Tests for compute_intrinsic_value function."""

  def test_integrated_normal_case(self):
    """Full IV calculation with realistic inputs.

    Explicit period (5 years):
    Y1: OE=108, Sh=98, OEPS=1.102, PV=1.002
    Y2: OE=114.5, Sh=96.04, OEPS=1.192, PV=0.985
    Y3: OE=120.2, Sh=94.12, OEPS=1.277, PV=0.959
    Y4: OE=125.0, Sh=92.23, OEPS=1.355, PV=0.926
    Y5: OE=128.8, Sh=90.39, OEPS=1.425, PV=0.885
    PV_explicit: 4.757

    Terminal:
    TV = (1.425 * 1.03) / (0.10 - 0.03) = 20.983
    PV_terminal = 20.983 / (1.10^5) = 13.024

    Total IV: 17.781
    """
    iv, pv_explicit, tv_component = compute_intrinsic_value(
        oe0=100.0,
        sh0=100.0,
        buyback_rate=0.02,
        growth_path=[0.08, 0.06, 0.05, 0.04, 0.03],
        g_terminal=0.03,
        discount_rate=0.10,
    )

    assert pv_explicit == pytest.approx(4.757, abs=0.01)
    assert tv_component == pytest.approx(13.024, abs=0.01)
    assert iv == pytest.approx(17.781, abs=0.01)

  def test_intrinsic_value_with_multiple(self):
    """Public interface test for valuation using exit multiple terminal."""
    iv, pv_explicit, tv_component = compute_intrinsic_value(
        oe0=100.0,
        sh0=100.0,
        buyback_rate=0.0,
        growth_path=[0.05, 0.05, 0.05], # 3 years
        g_terminal=0.0, # Not used
        discount_rate=0.10,
        tv_method='multiple',
        tv_param=8.0,
    )
    # OE: Y1=105, Y2=110.25, Y3=115.7625
    # Sh: 100 constant
    # OEPS: Y1=1.05, Y2=1.1025, Y3=1.157625
    # PV explicit: 1.05/1.1 + 1.1025/1.21 + 1.157625/1.331
    # = 0.954 + 0.911 + 0.869 = 2.734
    # TV: 1.157625 * 8.0 = 9.261
    # PV terminal: 9.261 / 1.331 = 6.957
    # Total IV: 2.734 + 6.957 = 9.691
    assert pv_explicit == pytest.approx(2.734, abs=0.01)
    assert tv_component == pytest.approx(6.957, abs=0.01)
    assert iv == pytest.approx(9.691, abs=0.01)


  def test_conservative_scenario(self):
    """Conservative valuation with low growth.

    Explicit period (3 years):
    Y1: OE=103.0, Sh=99.0, OEPS=1.040, PV=0.929
    Y2: OE=106.1, Sh=98.0, OEPS=1.082, PV=0.864
    Y3: OE=109.3, Sh=97.0, OEPS=1.126, PV=0.801
    PV_explicit: 2.594

    Terminal:
    TV = (1.126 * 1.02) / (0.12 - 0.02) = 11.485
    PV_terminal = 11.485 / (1.12^3) = 8.176

    Total IV: 10.770
    """
    iv, pv_explicit, tv_component = compute_intrinsic_value(
        oe0=100.0,
        sh0=100.0,
        buyback_rate=0.01,
        growth_path=[0.03, 0.03, 0.03],
        g_terminal=0.02,
        discount_rate=0.12,
    )

    assert pv_explicit == pytest.approx(2.594, abs=0.01)
    assert tv_component == pytest.approx(8.176, abs=0.01)
    assert iv == pytest.approx(10.770, abs=0.01)

  def test_aggressive_scenario(self):
    """Aggressive valuation with high growth."""
    iv, _, tv_component = compute_intrinsic_value(
        oe0=100.0,
        sh0=100.0,
        buyback_rate=0.05,
        growth_path=[
            0.15, 0.12, 0.10, 0.08, 0.06, 0.05, 0.04, 0.03, 0.03, 0.03
        ],
        g_terminal=0.03,
        discount_rate=0.10,
    )

    assert iv > 0
    assert tv_component > 0

  def test_nan_oe0(self):
    """Invalid OE0 input."""
    iv, _, _ = compute_intrinsic_value(
        oe0=float('nan'),
        sh0=100.0,
        buyback_rate=0.02,
        growth_path=[0.05, 0.04, 0.03],
        g_terminal=0.03,
        discount_rate=0.10,
    )

    assert math.isnan(iv)

  def test_nan_sh0(self):
    """Invalid shares input."""
    iv, _, _ = compute_intrinsic_value(
        oe0=100.0,
        sh0=float('nan'),
        buyback_rate=0.02,
        growth_path=[0.05, 0.04, 0.03],
        g_terminal=0.03,
        discount_rate=0.10,
    )

    assert math.isnan(iv)

  def test_nan_in_growth_path(self):
    """Invalid growth rate in path."""
    iv, _, _ = compute_intrinsic_value(
        oe0=100.0,
        sh0=100.0,
        buyback_rate=0.02,
        growth_path=[0.05, float('nan'), 0.03],
        g_terminal=0.03,
        discount_rate=0.10,
    )

    assert math.isnan(iv)

  def test_invalid_discount_rate(self):
    """Discount rate less than or equal to terminal growth."""
    iv, _, _ = compute_intrinsic_value(
        oe0=100.0,
        sh0=100.0,
        buyback_rate=0.02,
        growth_path=[0.05, 0.04, 0.03],
        g_terminal=0.10,
        discount_rate=0.10,
    )

    assert math.isnan(iv)

  def test_zero_shares(self):
    """Zero shares outstanding."""
    iv, _, _ = compute_intrinsic_value(
        oe0=100.0,
        sh0=0.0,
        buyback_rate=0.02,
        growth_path=[0.05, 0.04, 0.03],
        g_terminal=0.03,
        discount_rate=0.10,
    )

    assert math.isnan(iv)

  def test_negative_shares(self):
    """Negative shares outstanding (invalid)."""
    iv, _, _ = compute_intrinsic_value(
        oe0=100.0,
        sh0=-100.0,
        buyback_rate=0.02,
        growth_path=[0.05, 0.04, 0.03],
        g_terminal=0.03,
        discount_rate=0.10,
    )

    assert math.isnan(iv)

  def test_empty_growth_path(self):
    """Empty growth path."""
    iv, _, _ = compute_intrinsic_value(
        oe0=100.0,
        sh0=100.0,
        buyback_rate=0.02,
        growth_path=[],
        g_terminal=0.03,
        discount_rate=0.10,
    )

    assert math.isnan(iv)

  def test_declining_business_with_terminal(self):
    """Declining business with terminal value."""
    iv, pv_explicit, tv_component = compute_intrinsic_value(
        oe0=100.0,
        sh0=100.0,
        buyback_rate=0.0,
        growth_path=[-0.05, -0.03, -0.01, 0.0, 0.01],
        g_terminal=0.02,
        discount_rate=0.10,
    )

    assert iv > 0
    assert pv_explicit > 0
    assert tv_component > 0
