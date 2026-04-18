"""Tests for expanded metric specs.

Validates that new metrics extract from real SEC data.
"""

from pathlib import Path

import pytest

from data.silver.config.metric_specs import METRIC_SPECS
from data.silver.sources.sec.extractors import SECCompanyFactsExtractor

# Apple's companyfacts file (must exist in bronze output)
APPLE_CIK10 = '0000320193'
APPLE_COMPANYFACTS = (
    Path('data/bronze/out/sec/companyfacts')
    / f'CIK{APPLE_CIK10}.json')

SCREENING_METRICS = [
    'REVENUE',
    'NET_INCOME',
    'EBIT',
    'GROSS_PROFIT',
    'TOTAL_EQUITY',
    'TOTAL_ASSETS',
    'CURRENT_LIABILITIES',
    'TOTAL_DEBT',
    'CASH',
    'RD',
    'DIVIDENDS_PAID',
]

ORIGINAL_METRICS = ['CFO', 'CAPEX', 'SHARES']


@pytest.fixture(name='extractor')
def make_extractor():
  return SECCompanyFactsExtractor()


class TestMetricSpecsCompleteness:
  """All screening metrics must be defined in METRIC_SPECS."""

  def test_screening_metrics_are_defined(self):
    for metric in SCREENING_METRICS:
      assert metric in METRIC_SPECS, (
          f'{metric} not found in METRIC_SPECS')

  def test_original_metrics_still_defined(self):
    for metric in ORIGINAL_METRICS:
      assert metric in METRIC_SPECS, (
          f'{metric} missing from METRIC_SPECS')

  def test_each_metric_has_required_fields(self):
    for name, spec in METRIC_SPECS.items():
      assert 'namespace' in spec, f'{name} missing namespace'
      assert 'tags' in spec, f'{name} missing tags'
      assert 'unit' in spec, f'{name} missing unit'
      assert 'is_ytd' in spec, f'{name} missing is_ytd'
      assert len(spec['tags']) >= 1, f'{name} has no tags'


@pytest.mark.skipif(
    not APPLE_COMPANYFACTS.exists(),
    reason='Apple companyfacts not available')
class TestMetricExtractionFromRealData:
  """New metrics extract data from real Apple SEC filing."""

  def test_all_screening_metrics_extracted(self, extractor):
    df = extractor.extract_facts(APPLE_COMPANYFACTS)
    extracted = set(df['metric'].unique())
    for metric in SCREENING_METRICS:
      assert metric in extracted, (
          f'{metric} not extracted. '
          f'Available: {sorted(extracted)}')

  def test_revenue_has_reasonable_values(self, extractor):
    df = extractor.extract_facts(APPLE_COMPANYFACTS)
    rev = df[df['metric'] == 'REVENUE']
    assert not rev.empty

    annual = rev[rev['fp'] == 'FY']
    if not annual.empty:
      max_rev = annual['val'].max()
      assert max_rev > 100_000_000_000, (
          f'Apple FY revenue suspiciously low: {max_rev}')

  def test_balance_sheet_metrics_are_not_ytd(self):
    """Balance sheet items should not be YTD."""
    non_ytd = [
        'TOTAL_EQUITY', 'TOTAL_ASSETS',
        'CURRENT_LIABILITIES', 'TOTAL_DEBT', 'CASH',
    ]
    for metric in non_ytd:
      assert METRIC_SPECS[metric]['is_ytd'] is False, (
          f'{metric} should not be is_ytd')

  def test_income_statement_metrics_are_ytd(self):
    """Income statement items should be YTD."""
    ytd = ['REVENUE', 'NET_INCOME', 'EBIT', 'GROSS_PROFIT']
    for metric in ytd:
      assert METRIC_SPECS[metric]['is_ytd'] is True, (
          f'{metric} should be is_ytd')

  def test_rd_extracted(self, extractor):
    df = extractor.extract_facts(APPLE_COMPANYFACTS)
    rd = df[df['metric'] == 'RD']
    assert not rd.empty, 'RD not extracted from Apple'
    annual = rd[rd['fp'] == 'FY']
    if not annual.empty:
      max_rd = annual['val'].max()
      assert max_rd > 10_000_000_000, (
          f'Apple FY R&D suspiciously low: {max_rd}')

  def test_dividends_paid_extracted(self, extractor):
    df = extractor.extract_facts(APPLE_COMPANYFACTS)
    div = df[df['metric'] == 'DIVIDENDS_PAID']
    assert not div.empty, 'DIVIDENDS_PAID not extracted from Apple'
    annual = div[div['fp'] == 'FY']
    if not annual.empty:
      max_div = annual['val'].max()
      assert max_div > 1_000_000_000, (
          f'Apple FY dividends suspiciously low: {max_div}')
