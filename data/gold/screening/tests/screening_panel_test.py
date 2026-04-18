"""Tests for ScreeningPanelBuilder — public interface only.

Uses real Silver data to validate the screening panel output.
"""

from pathlib import Path

import pytest

SILVER_DIR = Path('data/silver/out')
HAS_SILVER_DATA = (
    (SILVER_DIR / 'sec' / 'facts_long.parquet').exists()
    and (SILVER_DIR / 'stooq' / 'prices_daily.parquet').exists()
)

# Derived ratio columns the screening panel must produce.
DERIVED_RATIOS = [
    'pe_ratio',
    'pb_ratio',
    'roe',
    'roic',
    'debt_to_equity',
    'fcf_yield',
    'op_margin',
    'gp_margin',
    'roa',
    'rd_to_revenue',
    'cfo_to_ni_ratio',
    'reinvestment_rate',
    'has_dividend',
    'debt_to_assets',
]

# Rolling multi-year metrics.
ROLLING_METRICS = [
    'roic_3y_avg',
    'roic_3y_min',
    'gp_margin_std_3y',
    'pe_avg_5y',
    'fcf_positive_3y',
    'fcf_ni_ratio_3y_avg',
    'revenue_cagr_3y',
    'revenue_cagr_5y',
    'roic_5y_avg',
    'roic_5y_min',
    'op_margin_trend_5y',
    'reinvestment_rate_5y_avg',
    'roic_trend',
]

# Track classification columns.
TRACK_COLS = [
    'axis_a_roic',
    'axis_b_reinvest',
    'axis_c_growth',
    'track_signal',
]

# Trust test columns.
TRUST_COLS = [
    'trust_roe_pass',
    'trust_roa_pass',
    'trust_cfo_ni_pass',
    'trust_dividend_exists',
    'trust_score',
]

# Quant score columns.
SCORE_COLS = [
    'fisher_quant_score',
    'buffett_quant_score',
    'gate_pass',
]

# Price-derived metrics.
PRICE_METRICS = [
    'pct_from_52w_high',
]

# Base metric TTM/point-in-time columns.
BASE_METRICS = [
    'revenue_ttm',
    'net_income_ttm',
    'ebit_ttm',
    'gross_profit_ttm',
    'cfo_ttm',
    'capex_ttm',
    'total_equity_q',
    'total_assets_q',
    'current_liabilities_q',
    'total_debt_q',
    'cash_q',
    'shares_q',
    'price',
    'market_cap',
]

IDENTITY_COLS = ['ticker', 'end', 'filed']


@pytest.mark.skipif(
    not HAS_SILVER_DATA,
    reason='Silver data not available')
class TestScreeningPanelBuilder:
  """ScreeningPanelBuilder.build() produces expected columns."""

  @pytest.fixture(autouse=True, scope='class')
  def _build_panel(self, tmp_path_factory):
    from data.gold.screening.panel import \
        ScreeningPanelBuilder  # pylint: disable=import-outside-toplevel
    tmp = tmp_path_factory.mktemp('screening')
    builder = ScreeningPanelBuilder(
        silver_dir=SILVER_DIR,
        gold_dir=tmp,
        min_date='2015-01-01',
    )
    TestScreeningPanelBuilder._panel = builder.build()

  @property
  def panel(self):
    return TestScreeningPanelBuilder._panel

  def test_panel_is_not_empty(self):
    assert len(self.panel) > 0

  def test_has_identity_columns(self):
    for col in IDENTITY_COLS:
      assert col in self.panel.columns, (
          f'Missing identity column: {col}')

  def test_has_base_metric_columns(self):
    for col in BASE_METRICS:
      assert col in self.panel.columns, (
          f'Missing base metric column: {col}')

  def test_has_derived_ratio_columns(self):
    for col in DERIVED_RATIOS:
      assert col in self.panel.columns, (
          f'Missing derived ratio column: {col}')

  def test_pe_ratio_is_reasonable(self):
    """Non-null PE ratios should be > 0 for profitable companies."""
    pe = self.panel['pe_ratio'].dropna()
    assert len(pe) > 0
    # At least some should be positive
    assert (pe > 0).sum() > len(pe) * 0.5

  def test_roe_is_percentage_scale(self):
    """ROE should be in decimal form (e.g. 0.15 = 15%)."""
    roe = self.panel['roe'].dropna()
    assert len(roe) > 0
    # Most ROE should be between -2 and +2 (i.e. -200% to +200%)
    reasonable = ((roe > -2) & (roe < 2)).sum()
    assert reasonable > len(roe) * 0.8

  def test_multiple_tickers(self):
    """Panel should cover multiple companies."""
    n_tickers = self.panel['ticker'].nunique()
    assert n_tickers >= 10

  def test_no_duplicate_primary_key(self):
    """(ticker, end) should be unique (latest filed only)."""
    dupes = self.panel.duplicated(
        subset=['ticker', 'end'], keep=False).sum()
    assert dupes == 0, (
        f'{dupes} duplicate (ticker, end) rows')

  def test_has_rolling_metric_columns(self):
    for col in ROLLING_METRICS:
      assert col in self.panel.columns, (
          f'Missing rolling metric column: {col}')

  def test_has_price_metric_columns(self):
    for col in PRICE_METRICS:
      assert col in self.panel.columns, (
          f'Missing price metric column: {col}')

  def test_roic_3y_avg_is_reasonable(self):
    """Non-null ROIC 3Y avg should be between -1 and +1."""
    vals = self.panel['roic_3y_avg'].dropna()
    if len(vals) == 0:
      pytest.skip('No ROIC 3Y avg data')
    reasonable = ((vals > -1) & (vals < 1)).sum()
    assert reasonable > len(vals) * 0.8

  def test_pct_from_52w_high_is_negative_or_zero(self):
    """Drawdown from 52w high should be <= 0."""
    vals = self.panel['pct_from_52w_high'].dropna()
    if len(vals) == 0:
      pytest.skip('No 52w high data')
    assert (vals <= 0.001).all(), (
        'pct_from_52w_high should be <= 0')

  def test_has_track_columns(self):
    for col in TRACK_COLS:
      assert col in self.panel.columns, (
          f'Missing track column: {col}')

  def test_has_trust_columns(self):
    for col in TRUST_COLS:
      assert col in self.panel.columns, (
          f'Missing trust column: {col}')

  def test_has_score_columns(self):
    for col in SCORE_COLS:
      assert col in self.panel.columns, (
          f'Missing score column: {col}')

  def test_track_signal_values_valid(self):
    vals = self.panel['track_signal'].dropna().unique()
    valid = {'buffett', 'fisher', 'mixed'}
    for v in vals:
      assert v in valid, f'Invalid track_signal: {v}'

  def test_trust_score_range(self):
    vals = self.panel['trust_score'].dropna()
    if len(vals) == 0:
      pytest.skip('No trust_score data')
    assert (vals >= 0).all() and (vals <= 4).all()

  def test_fisher_quant_score_range(self):
    vals = self.panel['fisher_quant_score'].dropna()
    if len(vals) == 0:
      pytest.skip('No fisher_quant_score data')
    assert (vals >= 0).all() and (vals <= 22).all()

  def test_buffett_quant_score_range(self):
    vals = self.panel['buffett_quant_score'].dropna()
    if len(vals) == 0:
      pytest.skip('No buffett_quant_score data')
    assert (vals >= 0).all() and (vals <= 22).all()
