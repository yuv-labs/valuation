"""Tests for metric_catalog — market-agnostic metric metadata."""

from data.silver.config.metric_catalog import METRIC_CATALOG
from data.silver.config.metric_specs import METRIC_SPECS

EXPECTED_METRICS = [
    'CFO', 'CAPEX', 'SHARES', 'REVENUE', 'NET_INCOME', 'EBIT',
    'GROSS_PROFIT', 'TOTAL_EQUITY', 'TOTAL_ASSETS',
    'CURRENT_LIABILITIES', 'TOTAL_DEBT', 'CASH',
]


class TestMetricCatalogCompleteness:

  def test_has_all_standard_metrics(self):
    for metric in EXPECTED_METRICS:
      assert metric in METRIC_CATALOG, (
          f'{metric} not found in METRIC_CATALOG')

  def test_no_extra_metrics(self):
    assert set(METRIC_CATALOG.keys()) == set(EXPECTED_METRICS)

  def test_each_entry_has_required_fields(self):
    for name, spec in METRIC_CATALOG.items():
      assert 'is_ytd' in spec, f'{name} missing is_ytd'
      assert 'abs' in spec, f'{name} missing abs'
      assert isinstance(spec['is_ytd'], bool), (
          f'{name} is_ytd must be bool')
      assert isinstance(spec['abs'], bool), (
          f'{name} abs must be bool')


class TestMetricCatalogMatchesUSSpecs:

  def test_is_ytd_matches_metric_specs(self):
    for name, us_spec in METRIC_SPECS.items():
      catalog_spec = METRIC_CATALOG[name]
      assert catalog_spec['is_ytd'] == us_spec['is_ytd'], (
          f'{name} is_ytd mismatch')

  def test_abs_matches_metric_specs(self):
    for name, us_spec in METRIC_SPECS.items():
      catalog_spec = METRIC_CATALOG[name]
      assert catalog_spec['abs'] == us_spec.get('abs', False), (
          f'{name} abs mismatch')
