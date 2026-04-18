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
                revenue_ttm: list[float],
                op_margin: list[float] | None = None,
                reinvestment_rate: list[float] | None = None,
                rd_ttm: list[float] | None = None,
                total_assets_q: list[float] | None = None,
                total_debt_q: list[float] | None = None,
                total_equity_q: list[float] | None = None,
                dividends_paid_ttm: list[float] | None = None,
                shares_q: list[float] | None = None,
                market_cap: list[float] | None = None,
                roe: list[float] | None = None,
                ) -> pd.DataFrame:
  """Build a minimal panel DataFrame for one ticker."""
  data = {
      'ticker': ticker,
      'end': pd.to_datetime([f'{y}-12-31' for y in years]),
      'roic': roic,
      'gp_margin': gp_margin,
      'pe_ratio': pe_ratio,
      'cfo_ttm': cfo_ttm,
      'capex_ttm': capex_ttm,
      'net_income_ttm': net_income_ttm,
      'revenue_ttm': revenue_ttm,
  }
  if op_margin is not None:
    data['op_margin'] = op_margin
  if reinvestment_rate is not None:
    data['reinvestment_rate'] = reinvestment_rate
  if rd_ttm is not None:
    data['rd_ttm'] = rd_ttm
  if total_assets_q is not None:
    data['total_assets_q'] = total_assets_q
  if total_debt_q is not None:
    data['total_debt_q'] = total_debt_q
  if total_equity_q is not None:
    data['total_equity_q'] = total_equity_q
  if dividends_paid_ttm is not None:
    data['dividends_paid_ttm'] = dividends_paid_ttm
  if shares_q is not None:
    data['shares_q'] = shares_q
  if market_cap is not None:
    data['market_cap'] = market_cap
  if roe is not None:
    data['roe'] = roe
  return pd.DataFrame(data)


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


# ── Phase 2: New rolling metrics ──────────────────────────────

class TestNewRollingMetrics:

  def test_revenue_cagr_5y(self):
    # 100 → ~161 over 5 years = 10% CAGR
    revs = [100, 110, 121, 133.1, 146.41, 161.05]
    panel = _make_panel(
        'AAPL', list(range(2018, 2024)),
        roic=[0.15] * 6, gp_margin=[0.4] * 6,
        pe_ratio=[20.0] * 6, cfo_ttm=[100.0] * 6,
        capex_ttm=[20.0] * 6, net_income_ttm=[80.0] * 6,
        revenue_ttm=revs,
        op_margin=[0.2] * 6, reinvestment_rate=[0.3] * 6,
    )
    result = ScreeningPanelBuilder._compute_rolling_metrics(panel)
    row = result[result['end'].dt.year == 2023].iloc[0]
    expected = (161.05 / 100.0) ** (1 / 5) - 1
    assert abs(row['revenue_cagr_5y'] - expected) < 1e-3

  def test_roic_5y_avg_and_min(self):
    panel = _make_panel(
        'AAPL', list(range(2019, 2024)),
        roic=[0.10, 0.12, 0.15, 0.18, 0.20],
        gp_margin=[0.4] * 5, pe_ratio=[20.0] * 5,
        cfo_ttm=[100.0] * 5, capex_ttm=[20.0] * 5,
        net_income_ttm=[80.0] * 5, revenue_ttm=[500.0] * 5,
        op_margin=[0.2] * 5, reinvestment_rate=[0.3] * 5,
    )
    result = ScreeningPanelBuilder._compute_rolling_metrics(panel)
    row = result[result['end'].dt.year == 2023].iloc[0]
    assert abs(row['roic_5y_avg'] - 0.15) < 1e-6
    assert abs(row['roic_5y_min'] - 0.10) < 1e-6

  def test_op_margin_trend_5y(self):
    panel = _make_panel(
        'AAPL', list(range(2018, 2024)),
        roic=[0.15] * 6, gp_margin=[0.4] * 6,
        pe_ratio=[20.0] * 6, cfo_ttm=[100.0] * 6,
        capex_ttm=[20.0] * 6, net_income_ttm=[80.0] * 6,
        revenue_ttm=[500.0] * 6,
        op_margin=[0.10, 0.11, 0.12, 0.14, 0.16, 0.20],
        reinvestment_rate=[0.3] * 6,
    )
    result = ScreeningPanelBuilder._compute_rolling_metrics(panel)
    row = result[result['end'].dt.year == 2023].iloc[0]
    # (0.20 - 0.10) / 5 = 0.02
    assert abs(row['op_margin_trend_5y'] - 0.02) < 1e-6

  def test_roic_trend_rising(self):
    panel = _make_panel(
        'AAPL', list(range(2019, 2024)),
        roic=[0.10, 0.12, 0.14, 0.16, 0.20],
        gp_margin=[0.4] * 5, pe_ratio=[20.0] * 5,
        cfo_ttm=[100.0] * 5, capex_ttm=[20.0] * 5,
        net_income_ttm=[80.0] * 5, revenue_ttm=[500.0] * 5,
        op_margin=[0.2] * 5, reinvestment_rate=[0.3] * 5,
    )
    result = ScreeningPanelBuilder._compute_rolling_metrics(panel)
    row = result[result['end'].dt.year == 2023].iloc[0]
    assert row['roic_trend'] == 'rising'

  def test_roic_trend_stable(self):
    panel = _make_panel(
        'AAPL', list(range(2019, 2024)),
        roic=[0.15, 0.14, 0.16, 0.15, 0.15],
        gp_margin=[0.4] * 5, pe_ratio=[20.0] * 5,
        cfo_ttm=[100.0] * 5, capex_ttm=[20.0] * 5,
        net_income_ttm=[80.0] * 5, revenue_ttm=[500.0] * 5,
        op_margin=[0.2] * 5, reinvestment_rate=[0.3] * 5,
    )
    result = ScreeningPanelBuilder._compute_rolling_metrics(panel)
    row = result[result['end'].dt.year == 2023].iloc[0]
    assert row['roic_trend'] == 'stable'

  def test_roic_trend_declining(self):
    panel = _make_panel(
        'AAPL', list(range(2019, 2024)),
        roic=[0.20, 0.18, 0.16, 0.14, 0.10],
        gp_margin=[0.4] * 5, pe_ratio=[20.0] * 5,
        cfo_ttm=[100.0] * 5, capex_ttm=[20.0] * 5,
        net_income_ttm=[80.0] * 5, revenue_ttm=[500.0] * 5,
        op_margin=[0.2] * 5, reinvestment_rate=[0.3] * 5,
    )
    result = ScreeningPanelBuilder._compute_rolling_metrics(panel)
    row = result[result['end'].dt.year == 2023].iloc[0]
    assert row['roic_trend'] == 'declining'

  def test_reinvestment_rate_5y_avg(self):
    panel = _make_panel(
        'AAPL', list(range(2019, 2024)),
        roic=[0.15] * 5, gp_margin=[0.4] * 5,
        pe_ratio=[20.0] * 5, cfo_ttm=[100.0] * 5,
        capex_ttm=[20.0] * 5, net_income_ttm=[80.0] * 5,
        revenue_ttm=[500.0] * 5, op_margin=[0.2] * 5,
        reinvestment_rate=[0.20, 0.25, 0.30, 0.35, 0.40],
    )
    result = ScreeningPanelBuilder._compute_rolling_metrics(panel)
    row = result[result['end'].dt.year == 2023].iloc[0]
    assert abs(row['reinvestment_rate_5y_avg'] - 0.30) < 1e-6


# ── Phase 3: Track signals ────────────────────────────────────

class TestComputeTrackSignals:

  def test_track_signal_buffett(self):
    panel = pd.DataFrame({
        'roic_trend': ['stable'],
        'reinvestment_rate_5y_avg': [0.20],
        'revenue_cagr_5y': [0.05],
    })
    result = ScreeningPanelBuilder._compute_track_signals(panel)
    assert result['track_signal'].iloc[0] == 'buffett'

  def test_track_signal_fisher(self):
    panel = pd.DataFrame({
        'roic_trend': ['rising'],
        'reinvestment_rate_5y_avg': [0.60],
        'revenue_cagr_5y': [0.20],
    })
    result = ScreeningPanelBuilder._compute_track_signals(panel)
    assert result['track_signal'].iloc[0] == 'fisher'

  def test_track_signal_mixed(self):
    panel = pd.DataFrame({
        'roic_trend': ['rising'],
        'reinvestment_rate_5y_avg': [0.20],
        'revenue_cagr_5y': [0.05],
    })
    result = ScreeningPanelBuilder._compute_track_signals(panel)
    assert result['track_signal'].iloc[0] == 'mixed'

  def test_declining_roic_is_mixed_axis(self):
    """Declining ROIC is negative for both tracks → mixed."""
    panel = pd.DataFrame({
        'roic_trend': ['declining'],
        'reinvestment_rate_5y_avg': [0.20],
        'revenue_cagr_5y': [0.05],
    })
    result = ScreeningPanelBuilder._compute_track_signals(panel)
    assert result['axis_a_roic'].iloc[0] == 'mixed'


class TestComputeTrustSignals:

  def test_trust_score_all_pass(self):
    panel = pd.DataFrame({
        'roe': [0.15],
        'roa': [0.10],
        'cfo_to_ni_ratio': [1.0],
        'has_dividend': [True],
    })
    result = ScreeningPanelBuilder._compute_trust_signals(panel)
    assert result['trust_score'].iloc[0] == 4

  def test_trust_score_partial(self):
    panel = pd.DataFrame({
        'roe': [0.05],
        'roa': [0.10],
        'cfo_to_ni_ratio': [0.5],
        'has_dividend': [True],
    })
    result = ScreeningPanelBuilder._compute_trust_signals(panel)
    assert result['trust_score'].iloc[0] == 2


class TestComputeQuantScores:

  def test_fisher_quant_max_score(self):
    panel = pd.DataFrame({
        'revenue_cagr_5y': [0.20],
        'rd_to_revenue': [0.08],
        'op_margin': [0.20],
        'op_margin_trend_5y': [0.02],
        'cfo_to_ni_ratio': [1.2],
    })
    result = ScreeningPanelBuilder._compute_quant_scores(panel)
    assert result['fisher_quant_score'].iloc[0] == 22

  def test_fisher_quant_rd_nan(self):
    panel = pd.DataFrame({
        'revenue_cagr_5y': [0.20],
        'rd_to_revenue': [np.nan],
        'op_margin': [0.20],
        'op_margin_trend_5y': [0.02],
        'cfo_to_ni_ratio': [1.2],
    })
    result = ScreeningPanelBuilder._compute_quant_scores(panel)
    # R&D NaN → 0 points for that criterion (weight 1x)
    assert result['fisher_quant_score'].iloc[0] == 22 - 2

  def test_buffett_quant_max_score(self):
    panel = pd.DataFrame({
        'fcf_yield': [0.10],
        'fcf_positive_3y': [True],
        'shares_5y_change': [-0.05],
        'roic': [0.30],
        'debt_to_assets': [0.20],
    })
    result = ScreeningPanelBuilder._compute_quant_scores(panel)
    assert result['buffett_quant_score'].iloc[0] == 22

  def test_buffett_quant_mid_tier(self):
    panel = pd.DataFrame({
        'fcf_yield': [0.05],
        'fcf_positive_3y': [True],
        'shares_5y_change': [0.0],
        'roic': [0.15],
        'debt_to_assets': [0.40],
    })
    result = ScreeningPanelBuilder._compute_quant_scores(panel)
    # fcf_yield 3~7%→1*3=3, fcf_pos→2*2=4, shares ±1%→1*2=2,
    # roic 10~25%→1*3=3, d/a 0.3~0.5→1*1=1 = 13
    assert result['buffett_quant_score'].iloc[0] == 13

  def test_mixed_ranking_uses_max(self):
    panel = pd.DataFrame({
        'revenue_cagr_5y': [0.20],
        'rd_to_revenue': [0.08],
        'op_margin': [0.20],
        'op_margin_trend_5y': [0.02],
        'cfo_to_ni_ratio': [1.2],
        'fcf_yield': [0.01],
        'fcf_positive_3y': [False],
        'shares_5y_change': [0.05],
        'roic': [0.05],
        'debt_to_assets': [0.60],
        'track_signal': ['mixed'],
    })
    result = ScreeningPanelBuilder._compute_quant_scores(panel)
    fisher = result['fisher_quant_score'].iloc[0]
    buffett = result['buffett_quant_score'].iloc[0]
    assert fisher > buffett


class TestApplyGates:

  def test_gate_trust_score(self):
    panel = pd.DataFrame({
        'trust_score': [2, 3, 4],
        'roic': [0.10, 0.10, 0.10],
        'debt_to_assets': [0.3, 0.3, 0.3],
        'end': pd.to_datetime(['2023-12-31'] * 3),
        'ticker': ['A', 'B', 'C'],
    })
    result = ScreeningPanelBuilder._apply_gates(panel)
    assert result['gate_pass'].tolist() == [False, True, True]

  def test_gate_debt_to_assets(self):
    panel = pd.DataFrame({
        'trust_score': [4, 4],
        'roic': [0.10, 0.10],
        'debt_to_assets': [0.7, 0.9],
        'end': pd.to_datetime(['2023-12-31'] * 2),
        'ticker': ['A', 'B'],
    })
    result = ScreeningPanelBuilder._apply_gates(panel)
    assert result['gate_pass'].tolist() == [True, False]

  def test_gate_consecutive_roic_negative(self):
    panel = pd.DataFrame({
        'trust_score': [4] * 3,
        'roic': [-0.05, -0.03, 0.10],
        'debt_to_assets': [0.3] * 3,
        'end': pd.to_datetime(
            ['2021-12-31', '2022-12-31', '2023-12-31']),
        'ticker': ['A'] * 3,
    })
    result = ScreeningPanelBuilder._apply_gates(panel)
    # 2021-2022 consecutive negative → latest row should fail
    val = result.loc[
        result['end'].dt.year == 2023, 'gate_pass'].iloc[0]
    assert not val
