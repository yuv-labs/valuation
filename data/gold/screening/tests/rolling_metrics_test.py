"""Unit tests for ScreeningPanelBuilder rolling and price metrics.

No Silver data required — uses synthetic DataFrames.
"""
# pylint: disable=protected-access

import numpy as np
import pandas as pd

from data.gold.screening.panel import ScreeningPanelBuilder


def _make_panel(ticker: str, years: list[int],
                roic: list[float],
                gp_margin: list[float],
                pe_ratio: list[float],
                cfo_ttm: list[float],
                capex_ttm: list[float],
                net_income_ttm: list[float],
                revenue_ttm: list[float]) -> pd.DataFrame:
  """Build a minimal panel DataFrame for one ticker."""
  return pd.DataFrame({
      'ticker': ticker,
      'end': pd.to_datetime([f'{y}-12-31' for y in years]),
      'roic': roic,
      'gp_margin': gp_margin,
      'pe_ratio': pe_ratio,
      'cfo_ttm': cfo_ttm,
      'capex_ttm': capex_ttm,
      'net_income_ttm': net_income_ttm,
      'revenue_ttm': revenue_ttm,
  })


class TestComputeRollingMetrics:

  def test_roic_3y_avg_and_min(self):
    panel = _make_panel(
        'AAPL', [2020, 2021, 2022, 2023],
        roic=[0.12, 0.15, 0.10, 0.18],
        gp_margin=[0.4] * 4,
        pe_ratio=[20.0] * 4,
        cfo_ttm=[100.0] * 4,
        capex_ttm=[20.0] * 4,
        net_income_ttm=[80.0] * 4,
        revenue_ttm=[500.0] * 4,
    )
    result = ScreeningPanelBuilder._compute_rolling_metrics(panel)

    row_2022 = result[result['end'].dt.year == 2022].iloc[0]
    assert abs(row_2022['roic_3y_avg'] - np.mean([0.12, 0.15, 0.10])) < 1e-6
    assert abs(row_2022['roic_3y_min'] - 0.10) < 1e-6

    row_2023 = result[result['end'].dt.year == 2023].iloc[0]
    assert abs(row_2023['roic_3y_avg'] - np.mean([0.15, 0.10, 0.18])) < 1e-6
    assert abs(row_2023['roic_3y_min'] - 0.10) < 1e-6

  def test_roic_3y_nan_with_insufficient_history(self):
    panel = _make_panel(
        'AAPL', [2022, 2023],
        roic=[0.12, 0.15],
        gp_margin=[0.4] * 2,
        pe_ratio=[20.0] * 2,
        cfo_ttm=[100.0] * 2,
        capex_ttm=[20.0] * 2,
        net_income_ttm=[80.0] * 2,
        revenue_ttm=[500.0] * 2,
    )
    result = ScreeningPanelBuilder._compute_rolling_metrics(panel)
    assert result['roic_3y_avg'].isna().all()

  def test_gp_margin_std_3y(self):
    panel = _make_panel(
        'AAPL', [2020, 2021, 2022],
        roic=[0.15] * 3,
        gp_margin=[0.40, 0.42, 0.38],
        pe_ratio=[20.0] * 3,
        cfo_ttm=[100.0] * 3,
        capex_ttm=[20.0] * 3,
        net_income_ttm=[80.0] * 3,
        revenue_ttm=[500.0] * 3,
    )
    result = ScreeningPanelBuilder._compute_rolling_metrics(panel)
    row = result[result['end'].dt.year == 2022].iloc[0]
    expected_std = np.std([0.40, 0.42, 0.38], ddof=1)
    assert abs(row['gp_margin_std_3y'] - expected_std) < 1e-6

  def test_pe_avg_5y_with_3y_history(self):
    """PE avg should work with 3 years (min_periods=3)."""
    panel = _make_panel(
        'AAPL', [2021, 2022, 2023],
        roic=[0.15] * 3,
        gp_margin=[0.4] * 3,
        pe_ratio=[15.0, 20.0, 25.0],
        cfo_ttm=[100.0] * 3,
        capex_ttm=[20.0] * 3,
        net_income_ttm=[80.0] * 3,
        revenue_ttm=[500.0] * 3,
    )
    result = ScreeningPanelBuilder._compute_rolling_metrics(panel)
    row = result[result['end'].dt.year == 2023].iloc[0]
    assert abs(row['pe_avg_5y'] - 20.0) < 1e-6

  def test_pe_avg_5y_nan_with_2y(self):
    """PE avg should be NaN with only 2 years."""
    panel = _make_panel(
        'AAPL', [2022, 2023],
        roic=[0.15] * 2,
        gp_margin=[0.4] * 2,
        pe_ratio=[15.0, 20.0],
        cfo_ttm=[100.0] * 2,
        capex_ttm=[20.0] * 2,
        net_income_ttm=[80.0] * 2,
        revenue_ttm=[500.0] * 2,
    )
    result = ScreeningPanelBuilder._compute_rolling_metrics(panel)
    assert result['pe_avg_5y'].isna().all()

  def test_fcf_positive_3y_all_positive(self):
    panel = _make_panel(
        'AAPL', [2021, 2022, 2023],
        roic=[0.15] * 3,
        gp_margin=[0.4] * 3,
        pe_ratio=[20.0] * 3,
        cfo_ttm=[100.0, 120.0, 110.0],
        capex_ttm=[20.0, 30.0, 25.0],
        net_income_ttm=[80.0] * 3,
        revenue_ttm=[500.0] * 3,
    )
    result = ScreeningPanelBuilder._compute_rolling_metrics(panel)
    row = result[result['end'].dt.year == 2023].iloc[0]
    assert bool(row['fcf_positive_3y']) is True

  def test_fcf_positive_3y_with_negative(self):
    panel = _make_panel(
        'AAPL', [2021, 2022, 2023],
        roic=[0.15] * 3,
        gp_margin=[0.4] * 3,
        pe_ratio=[20.0] * 3,
        cfo_ttm=[100.0, 10.0, 110.0],
        capex_ttm=[20.0, 50.0, 25.0],
        net_income_ttm=[80.0] * 3,
        revenue_ttm=[500.0] * 3,
    )
    result = ScreeningPanelBuilder._compute_rolling_metrics(panel)
    row = result[result['end'].dt.year == 2023].iloc[0]
    assert bool(row['fcf_positive_3y']) is False

  def test_fcf_ni_ratio_excludes_negative_ni(self):
    """When NI <= 0, that year should be excluded from avg."""
    panel = _make_panel(
        'AAPL', [2021, 2022, 2023],
        roic=[0.15] * 3,
        gp_margin=[0.4] * 3,
        pe_ratio=[20.0] * 3,
        cfo_ttm=[100.0, 50.0, 100.0],
        capex_ttm=[20.0, 10.0, 20.0],
        net_income_ttm=[80.0, -10.0, 80.0],
        revenue_ttm=[500.0] * 3,
    )
    result = ScreeningPanelBuilder._compute_rolling_metrics(panel)
    row = result[result['end'].dt.year == 2023].iloc[0]
    # 2021: FCF=80, NI=80, ratio=1.0
    # 2022: NI=-10, excluded
    # 2023: FCF=80, NI=80, ratio=1.0
    # avg of [1.0, 1.0] = 1.0
    assert abs(row['fcf_ni_ratio_3y_avg'] - 1.0) < 1e-6

  def test_fcf_ni_ratio_nan_when_all_ni_negative(self):
    """When all NI <= 0 in window, ratio should be NaN."""
    panel = _make_panel(
        'AAPL', [2021, 2022, 2023],
        roic=[0.15] * 3,
        gp_margin=[0.4] * 3,
        pe_ratio=[20.0] * 3,
        cfo_ttm=[100.0] * 3,
        capex_ttm=[20.0] * 3,
        net_income_ttm=[-10.0, -20.0, -5.0],
        revenue_ttm=[500.0] * 3,
    )
    result = ScreeningPanelBuilder._compute_rolling_metrics(panel)
    row = result[result['end'].dt.year == 2023].iloc[0]
    assert pd.isna(row['fcf_ni_ratio_3y_avg'])

  def test_revenue_cagr_3y(self):
    panel = _make_panel(
        'AAPL', [2020, 2021, 2022, 2023],
        roic=[0.15] * 4,
        gp_margin=[0.4] * 4,
        pe_ratio=[20.0] * 4,
        cfo_ttm=[100.0] * 4,
        capex_ttm=[20.0] * 4,
        net_income_ttm=[80.0] * 4,
        revenue_ttm=[100.0, 110.0, 121.0, 133.1],
    )
    result = ScreeningPanelBuilder._compute_rolling_metrics(panel)
    row = result[result['end'].dt.year == 2023].iloc[0]
    # (133.1 / 100.0)^(1/3) - 1 ≈ 0.10
    expected = (133.1 / 100.0) ** (1 / 3) - 1
    assert abs(row['revenue_cagr_3y'] - expected) < 1e-4

  def test_multiple_tickers_independent(self):
    panel_a = _make_panel(
        'AAPL', [2021, 2022, 2023],
        roic=[0.20, 0.18, 0.22],
        gp_margin=[0.4] * 3,
        pe_ratio=[20.0] * 3,
        cfo_ttm=[100.0] * 3,
        capex_ttm=[20.0] * 3,
        net_income_ttm=[80.0] * 3,
        revenue_ttm=[500.0] * 3,
    )
    panel_b = _make_panel(
        'MSFT', [2021, 2022, 2023],
        roic=[0.10, 0.08, 0.12],
        gp_margin=[0.4] * 3,
        pe_ratio=[20.0] * 3,
        cfo_ttm=[100.0] * 3,
        capex_ttm=[20.0] * 3,
        net_income_ttm=[80.0] * 3,
        revenue_ttm=[500.0] * 3,
    )
    panel = pd.concat([panel_a, panel_b], ignore_index=True)
    result = ScreeningPanelBuilder._compute_rolling_metrics(panel)

    aapl_2023 = result[
        (result['ticker'] == 'AAPL')
        & (result['end'].dt.year == 2023)].iloc[0]
    msft_2023 = result[
        (result['ticker'] == 'MSFT')
        & (result['end'].dt.year == 2023)].iloc[0]

    assert abs(aapl_2023['roic_3y_avg'] - 0.20) < 1e-6
    assert abs(msft_2023['roic_3y_avg'] - 0.10) < 1e-6


class TestComputePriceMetrics:

  def test_drawdown_from_52w_high(self):
    panel = pd.DataFrame({
        'ticker': ['AAPL', 'AAPL'],
        'end': pd.to_datetime(['2022-12-31', '2023-12-31']),
    })
    dates = pd.bdate_range('2023-01-01', periods=260)
    close_vals = [150.0] * 130 + [120.0] * 130
    prices = pd.DataFrame({
        'ticker': 'AAPL',
        'date': dates,
        'close': close_vals,
        'high': close_vals,
    })
    result = ScreeningPanelBuilder._compute_price_metrics(
        panel, prices)

    latest = result[result['end'].dt.year == 2023].iloc[0]
    # 52w high = 150, current = 120, drawdown = -20%
    assert abs(latest['pct_from_52w_high'] - (-0.2)) < 0.01

    # Non-latest period should be NaN.
    older = result[result['end'].dt.year == 2022].iloc[0]
    assert pd.isna(older['pct_from_52w_high'])

  def test_empty_prices(self):
    panel = pd.DataFrame({
        'ticker': ['AAPL'],
        'end': pd.to_datetime(['2023-12-31']),
    })
    result = ScreeningPanelBuilder._compute_price_metrics(
        panel, pd.DataFrame())
    assert 'pct_from_52w_high' in result.columns
    assert result['pct_from_52w_high'].isna().all()

  def test_uses_close_when_no_high_column(self):
    """For KR data without 'high', should use 'close'."""
    panel = pd.DataFrame({
        'ticker': ['005930', '005930'],
        'end': pd.to_datetime(['2022-12-31', '2023-12-31']),
    })
    dates = pd.bdate_range('2023-01-01', periods=260)
    close_vals = [70000.0] * 130 + [60000.0] * 130
    prices = pd.DataFrame({
        'ticker': '005930',
        'date': dates,
        'close': close_vals,
    })
    result = ScreeningPanelBuilder._compute_price_metrics(
        panel, prices)
    latest = result[result['end'].dt.year == 2023].iloc[0]
    expected = (60000.0 / 70000.0) - 1
    assert abs(latest['pct_from_52w_high'] - expected) < 0.01
