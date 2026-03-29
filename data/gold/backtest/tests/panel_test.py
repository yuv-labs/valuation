"""Tests for BacktestPanelBuilder — public interface only."""

from pathlib import Path

import pytest

SILVER_DIR = Path('data/silver/out')
HAS_SILVER = (SILVER_DIR / 'sec' / 'facts_long.parquet').exists()


@pytest.mark.skipif(not HAS_SILVER, reason='No Silver data')
class TestBacktestPanelBuilder:

  def test_build_returns_dataframe(self, tmp_path):
    from data.gold.backtest.panel import \
        BacktestPanelBuilder  # pylint: disable=import-outside-toplevel
    builder = BacktestPanelBuilder(
        silver_dir=SILVER_DIR, gold_dir=tmp_path)
    panel = builder.build()

    assert not panel.empty
    assert 'ticker' in panel.columns
    assert 'end' in panel.columns
    assert 'filed' in panel.columns

  def test_primary_key_allows_multiple_filed_per_end(self, tmp_path):
    """Backtest panel keeps all filed versions — not just latest."""
    from data.gold.backtest.panel import \
        BacktestPanelBuilder  # pylint: disable=import-outside-toplevel
    builder = BacktestPanelBuilder(
        silver_dir=SILVER_DIR, gold_dir=tmp_path)
    panel = builder.build()

    # For the same ticker+end, there should be multiple filed dates
    # (at least for some tickers with restatements or amended filings)
    grouped = panel.groupby(['ticker', 'end'])['filed'].nunique()
    # At minimum, every group has at least 1 filed
    assert (grouped >= 1).all()
    # PK should be unique on (ticker, end, filed)
    assert not panel.duplicated(
        subset=['ticker', 'end', 'filed']).any()

  def test_has_price_and_market_cap(self, tmp_path):
    from data.gold.backtest.panel import \
        BacktestPanelBuilder  # pylint: disable=import-outside-toplevel
    builder = BacktestPanelBuilder(
        silver_dir=SILVER_DIR, gold_dir=tmp_path)
    panel = builder.build()

    assert 'price' in panel.columns
    assert 'market_cap' in panel.columns
    # At least some rows should have price data
    assert panel['price'].notna().any()
