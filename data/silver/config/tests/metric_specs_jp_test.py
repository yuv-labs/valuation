"""Tests for Japanese metric specs."""

from data.silver.config.metric_catalog import METRIC_CATALOG
from data.silver.config.metric_specs_jp import METRIC_SPECS_JP

EXPECTED_METRICS = list(METRIC_CATALOG.keys())


class TestMetricSpecsJPCompleteness:

  def test_has_all_standard_metrics(self):
    for metric in EXPECTED_METRICS:
      assert metric in METRIC_SPECS_JP, (
          f'{metric} not found in METRIC_SPECS_JP')

  def test_each_entry_has_required_fields(self):
    for name, spec in METRIC_SPECS_JP.items():
      assert 'taxonomies' in spec, f'{name} missing taxonomies'
      assert 'unit' in spec, f'{name} missing unit'
      assert 'is_ytd' in spec, f'{name} missing is_ytd'
      assert isinstance(spec['taxonomies'], dict), (
          f'{name} taxonomies must be dict')

  def test_unit_is_jpy(self):
    for name, spec in METRIC_SPECS_JP.items():
      if name == 'SHARES':
        assert spec['unit'] == 'shares', (
            f'{name} unit should be shares')
      else:
        assert spec['unit'] == 'JPY', (
            f'{name} unit should be JPY')

  def test_is_ytd_matches_catalog(self):
    for name, spec in METRIC_SPECS_JP.items():
      assert spec['is_ytd'] == METRIC_CATALOG[name]['is_ytd'], (
          f'{name} is_ytd mismatch with METRIC_CATALOG')

  def test_has_jgaap_taxonomy(self):
    for name, spec in METRIC_SPECS_JP.items():
      assert 'jppfs_cor' in spec['taxonomies'], (
          f'{name} missing J-GAAP (jppfs_cor) taxonomy')

  def test_has_ifrs_taxonomy(self):
    for name, spec in METRIC_SPECS_JP.items():
      assert 'ifrs-full' in spec['taxonomies'], (
          f'{name} missing IFRS (ifrs-full) taxonomy')

  def test_each_taxonomy_has_at_least_one_tag(self):
    for name, spec in METRIC_SPECS_JP.items():
      for ns, tags in spec['taxonomies'].items():
        assert len(tags) >= 1, (
            f'{name}/{ns} has no tags')
