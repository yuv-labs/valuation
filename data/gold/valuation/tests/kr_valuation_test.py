"""Tests for Korean DCF valuation — public interface."""

from pathlib import Path

import pytest

SILVER_DIR = Path('data/silver/out')
HAS_KR_DATA = (SILVER_DIR / 'dart' / 'facts_long.parquet').exists()


@pytest.mark.skipif(not HAS_KR_DATA, reason='No KR Silver data')
class TestKRValuationPanel:

  def test_kia_has_quarterly_cfo_ttm(self):
    """Kia should have multi-quarter CFO TTM after build."""
    from data.gold.valuation.panel import \
        ValuationPanelBuilder  # pylint: disable=import-outside-toplevel
    builder = ValuationPanelBuilder(
        silver_dir=SILVER_DIR,
        gold_dir=Path('/tmp/test_kr_dcf'),
        min_date='2022-01-01',
        markets=['us', 'kr'],
    )
    panel = builder.build()

    kia = panel[panel['ticker'] == '000270']
    assert len(kia) >= 4, (
        f'Kia should have 4+ rows, got {len(kia)}')
    assert kia['cfo_ttm'].notna().sum() >= 2, (
        'Kia should have CFO TTM data')

  def test_kr_tickers_present(self):
    """Panel should include Korean tickers."""
    from data.gold.valuation.panel import \
        ValuationPanelBuilder  # pylint: disable=import-outside-toplevel
    builder = ValuationPanelBuilder(
        silver_dir=SILVER_DIR,
        gold_dir=Path('/tmp/test_kr_dcf2'),
        min_date='2023-01-01',
        markets=['us', 'kr'],
    )
    panel = builder.build()

    from shared.ticker import \
        is_kr_ticker  # pylint: disable=import-outside-toplevel
    kr = panel[panel['ticker'].apply(is_kr_ticker)]
    n_kr = kr['ticker'].nunique()
    assert n_kr >= 3, f'Expected 3+ KR tickers, got {n_kr}'
