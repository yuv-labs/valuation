"""Tests for Gold transforms — public interface only."""

import pandas as pd
import pytest

from data.gold.transforms import calculate_market_cap
from data.gold.transforms import join_metrics_by_cfo_filed
from data.gold.transforms import join_prices_pit


def _make_metrics_q(rows: list[dict]) -> pd.DataFrame:
  """Build a long-format metrics DataFrame for testing."""
  return pd.DataFrame(rows)


class TestJoinMetricsByCFOFiled:
  """join_metrics_by_cfo_filed() public interface tests."""

  def test_joins_cfo_capex_shares_by_end_date(self):
    """All three metrics joined on same end date."""
    metrics = _make_metrics_q([
        {'cik10': 'AAPL', 'metric': 'CFO', 'end': '2024-03-31',
         'filed': '2024-05-01', 'q_val': 100.0, 'ttm_val': 400.0,
         'fiscal_year': 2024, 'fiscal_quarter': 'Q1'},
        {'cik10': 'AAPL', 'metric': 'CAPEX', 'end': '2024-03-31',
         'filed': '2024-05-01', 'q_val': 20.0, 'ttm_val': 80.0,
         'fiscal_year': 2024, 'fiscal_quarter': 'Q1'},
        {'cik10': 'AAPL', 'metric': 'SHARES', 'end': '2024-03-31',
         'filed': '2024-05-01', 'q_val': 1_000_000.0, 'ttm_val': None,
         'fiscal_year': 2024, 'fiscal_quarter': 'Q1'},
    ])
    result = join_metrics_by_cfo_filed(metrics)

    assert len(result) == 1
    row = result.iloc[0]
    assert row['cfo_q'] == 100.0
    assert row['cfo_ttm'] == 400.0
    assert row['capex_q'] == 20.0
    assert row['shares_q'] == 1_000_000.0

  def test_missing_capex_does_not_crash(self):
    """When CAPEX is missing, join still succeeds with CFO and SHARES."""
    metrics = _make_metrics_q([
        {'cik10': 'AAPL', 'metric': 'CFO', 'end': '2024-03-31',
         'filed': '2024-05-01', 'q_val': 100.0, 'ttm_val': 400.0,
         'fiscal_year': 2024, 'fiscal_quarter': 'Q1'},
        {'cik10': 'AAPL', 'metric': 'SHARES', 'end': '2024-03-31',
         'filed': '2024-05-01', 'q_val': 1_000_000.0, 'ttm_val': None,
         'fiscal_year': 2024, 'fiscal_quarter': 'Q1'},
    ])
    result = join_metrics_by_cfo_filed(metrics)

    assert len(result) == 1
    assert result.iloc[0]['cfo_q'] == 100.0
    assert result.iloc[0]['shares_q'] == 1_000_000.0

  def test_no_cfo_returns_empty(self):
    """When there is no CFO data, result is empty."""
    metrics = _make_metrics_q([
        {'cik10': 'AAPL', 'metric': 'CAPEX', 'end': '2024-03-31',
         'filed': '2024-05-01', 'q_val': 20.0, 'ttm_val': 80.0,
         'fiscal_year': 2024, 'fiscal_quarter': 'Q1'},
    ])
    result = join_metrics_by_cfo_filed(metrics)
    assert result.empty

  def test_pit_uses_most_recent_capex_before_cfo_filed(self):
    """CAPEX filed before CFO is used; later filings are excluded."""
    metrics = _make_metrics_q([
        {'cik10': 'AAPL', 'metric': 'CFO', 'end': '2024-03-31',
         'filed': '2024-05-15', 'q_val': 100.0, 'ttm_val': 400.0,
         'fiscal_year': 2024, 'fiscal_quarter': 'Q1'},
        # CAPEX filed before CFO
        {'cik10': 'AAPL', 'metric': 'CAPEX', 'end': '2024-03-31',
         'filed': '2024-05-10', 'q_val': 20.0, 'ttm_val': 80.0,
         'fiscal_year': 2024, 'fiscal_quarter': 'Q1'},
    ])
    result = join_metrics_by_cfo_filed(metrics)

    assert len(result) == 1
    assert result.iloc[0]['capex_q'] == 20.0


class TestJoinPricesPIT:
  """join_prices_pit() public interface tests."""

  def test_joins_first_price_after_filed(self):
    """Price from the first trading day after filed date."""
    metrics = pd.DataFrame([{
        'ticker': 'AAPL', 'end': '2024-03-31',
        'filed': '2024-05-01', 'cfo_q': 100.0,
    }])
    prices = pd.DataFrame([
        {'symbol': 'AAPL.US', 'date': '2024-04-30', 'close': 170.0},
        {'symbol': 'AAPL.US', 'date': '2024-05-01', 'close': 172.0},
        {'symbol': 'AAPL.US', 'date': '2024-05-02', 'close': 175.0},
    ])
    result = join_prices_pit(metrics, prices)

    assert len(result) == 1
    assert result.iloc[0]['price'] == 172.0

  def test_no_price_for_ticker_excluded(self):
    """Tickers with no price data are excluded from output."""
    metrics = pd.DataFrame([{
        'ticker': 'AAPL', 'end': '2024-03-31',
        'filed': '2024-05-01', 'cfo_q': 100.0,
    }])
    prices = pd.DataFrame([
        {'symbol': 'MSFT.US', 'date': '2024-05-01', 'close': 400.0},
    ])
    result = join_prices_pit(metrics, prices)
    assert result.empty


class TestCalculateMarketCap:
  """calculate_market_cap() public interface tests."""

  def test_market_cap_is_shares_times_price(self):
    panel = pd.DataFrame([{
        'shares_q': 1_000_000.0,
        'price': 150.0,
    }])
    result = calculate_market_cap(panel)
    assert result.iloc[0]['market_cap'] == pytest.approx(150_000_000.0)

  def test_missing_columns_returns_none(self):
    """Missing shares or price columns → market_cap is None."""
    panel = pd.DataFrame([{'ticker': 'AAPL'}])
    result = calculate_market_cap(panel)
    assert result.iloc[0]['market_cap'] is None

  def test_does_not_mutate_input(self):
    """Original DataFrame is not modified."""
    panel = pd.DataFrame([{'shares_q': 1_000_000.0, 'price': 150.0}])
    original_cols = list(panel.columns)
    calculate_market_cap(panel)
    assert list(panel.columns) == original_cols
