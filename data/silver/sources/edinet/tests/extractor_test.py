"""Tests for EDINET extractor — public interface only."""

import io
import zipfile

import pandas as pd
import pytest

from data.silver.config.metric_catalog import METRIC_CATALOG
from data.silver.sources.edinet.extractors import EDINETExtractor

JGAAP_XBRL = '''<?xml version="1.0" encoding="UTF-8"?>
<xbrli:xbrl
  xmlns:xbrli="http://www.xbrl.org/2003/instance"
  xmlns:jppfs_cor="http://disclosure.edinet-fsa.go.jp/taxonomy/jppfs/2024-02-01/jppfs_cor"
  xmlns:iso4217="http://www.xbrl.org/2003/iso4217"
  xmlns:xbrli_pure="http://www.xbrl.org/2003/instance">

  <jppfs_cor:NetSales
    contextRef="CurrentYearDuration"
    unitRef="JPY"
    decimals="-6">45095325000000</jppfs_cor:NetSales>

  <jppfs_cor:OperatingIncome
    contextRef="CurrentYearDuration"
    unitRef="JPY"
    decimals="-6">5352929000000</jppfs_cor:OperatingIncome>

  <jppfs_cor:TotalAssets
    contextRef="CurrentYearInstant"
    unitRef="JPY"
    decimals="-6">80692493000000</jppfs_cor:TotalAssets>

  <jppfs_cor:CashAndDeposits
    contextRef="CurrentYearInstant"
    unitRef="JPY"
    decimals="-6">9020000000000</jppfs_cor:CashAndDeposits>

  <jppfs_cor:CashAndCashEquivalentsIncreaseDecreaseFromOperatingActivities
    contextRef="CurrentYearDuration"
    unitRef="JPY"
    decimals="-6">4200000000000</jppfs_cor:CashAndCashEquivalentsIncreaseDecreaseFromOperatingActivities>

  <jppfs_cor:PurchaseOfPropertyPlantAndEquipmentAndIntangibleAssetsInvCF
    contextRef="CurrentYearDuration"
    unitRef="JPY"
    decimals="-6">1700000000000</jppfs_cor:PurchaseOfPropertyPlantAndEquipmentAndIntangibleAssetsInvCF>

  <jppfs_cor:ProfitLossAttributableToOwnersOfParent
    contextRef="CurrentYearDuration"
    unitRef="JPY"
    decimals="-6">4944933000000</jppfs_cor:ProfitLossAttributableToOwnersOfParent>

  <jppfs_cor:GrossProfit
    contextRef="CurrentYearDuration"
    unitRef="JPY"
    decimals="-6">9000000000000</jppfs_cor:GrossProfit>

  <jppfs_cor:NetAssets
    contextRef="CurrentYearInstant"
    unitRef="JPY"
    decimals="-6">32000000000000</jppfs_cor:NetAssets>

  <jppfs_cor:CurrentLiabilities
    contextRef="CurrentYearInstant"
    unitRef="JPY"
    decimals="-6">25000000000000</jppfs_cor:CurrentLiabilities>

  <jppfs_cor:LongTermLoansPayable
    contextRef="CurrentYearInstant"
    unitRef="JPY"
    decimals="-6">12000000000000</jppfs_cor:LongTermLoansPayable>

  <jppfs_cor:IssuedSharesTotalNumberOfSharesIssuedPerShareInformation
    contextRef="CurrentYearInstant"
    unitRef="shares"
    decimals="0">14520000000</jppfs_cor:IssuedSharesTotalNumberOfSharesIssuedPerShareInformation>

  <xbrli:context id="CurrentYearDuration">
    <xbrli:entity><xbrli:identifier scheme="http://disclosure.edinet-fsa.go.jp">E02529</xbrli:identifier></xbrli:entity>
    <xbrli:period><xbrli:startDate>2024-04-01</xbrli:startDate><xbrli:endDate>2025-03-31</xbrli:endDate></xbrli:period>
  </xbrli:context>
  <xbrli:context id="CurrentYearInstant">
    <xbrli:entity><xbrli:identifier scheme="http://disclosure.edinet-fsa.go.jp">E02529</xbrli:identifier></xbrli:entity>
    <xbrli:period><xbrli:instant>2025-03-31</xbrli:instant></xbrli:period>
  </xbrli:context>
  <xbrli:unit id="JPY"><xbrli:measure>iso4217:JPY</xbrli:measure></xbrli:unit>
  <xbrli:unit id="shares"><xbrli:measure>xbrli:shares</xbrli:measure></xbrli:unit>
</xbrli:xbrl>
'''


@pytest.fixture(name='extractor')
def make_extractor():
  return EDINETExtractor()


@pytest.fixture(name='xbrl_zip')
def make_xbrl_zip(tmp_path):
  zip_path = tmp_path / 'E02529_2025-03-31_120.zip'
  buf = io.BytesIO()
  with zipfile.ZipFile(buf, 'w') as zf:
    zf.writestr('XBRL/PublicDoc/toyota_2025.xbrl', JGAAP_XBRL)
  zip_path.write_bytes(buf.getvalue())
  return zip_path


class TestEDINETExtractor:

  def test_extract_returns_dataframe(self, extractor, xbrl_zip):
    df = extractor.extract_facts(xbrl_zip)
    assert isinstance(df, pd.DataFrame)
    assert not df.empty

  def test_has_required_columns(self, extractor, xbrl_zip):
    df = extractor.extract_facts(xbrl_zip)
    required = [
        'edinet_code', 'metric', 'val', 'end', 'tag',
    ]
    for col in required:
      assert col in df.columns, f'Missing column: {col}'

  def test_maps_jgaap_tags_to_metrics(self, extractor, xbrl_zip):
    df = extractor.extract_facts(xbrl_zip)
    metrics = set(df['metric'].dropna().unique())
    assert 'REVENUE' in metrics
    assert 'EBIT' in metrics
    assert 'TOTAL_ASSETS' in metrics
    assert 'CFO' in metrics
    assert 'CAPEX' in metrics
    assert 'SHARES' in metrics

  def test_all_12_metrics_extracted(self, extractor, xbrl_zip):
    df = extractor.extract_facts(xbrl_zip)
    extracted = set(df['metric'].dropna().unique())
    for metric in METRIC_CATALOG:
      assert metric in extracted, (
          f'{metric} not extracted. Available: {sorted(extracted)}')

  def test_values_are_numeric(self, extractor, xbrl_zip):
    df = extractor.extract_facts(xbrl_zip)
    assert df['val'].dtype in ('float64', 'Float64', 'int64')

  def test_revenue_has_reasonable_value(self, extractor, xbrl_zip):
    df = extractor.extract_facts(xbrl_zip)
    rev = df[df['metric'] == 'REVENUE']
    assert not rev.empty
    assert rev.iloc[0]['val'] > 1e12
