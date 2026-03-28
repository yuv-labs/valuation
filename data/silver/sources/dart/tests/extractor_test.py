"""Tests for DART extractor — public interface only."""

import json

import pandas as pd
import pytest

from data.silver.sources.dart.extractors import DARTExtractor

# Minimal DART finstate response with key accounts.
SAMSUNG_FINSTATE = {
    'status': '000',
    'message': 'ok',
    'list': [
        {
            'sj_div': 'IS',
            'sj_nm': 'Income Statement',
            'account_nm': 'Revenue',
            'thstrm_amount': '300,870,903,000,000',
            'frmtrm_amount': '258,935,482,000,000',
            'bsns_year': '2024',
            'reprt_code': '11011',
            'corp_code': '00126380',
        },
        {
            'sj_div': 'IS',
            'sj_nm': 'Income Statement',
            'account_nm': 'OperatingProfit',
            'thstrm_amount': '32,725,961,000,000',
            'frmtrm_amount': '6,566,976,000,000',
            'bsns_year': '2024',
            'reprt_code': '11011',
            'corp_code': '00126380',
        },
        {
            'sj_div': 'BS',
            'sj_nm': 'Balance Sheet',
            'account_nm': 'TotalAssets',
            'thstrm_amount': '514,531,948,000,000',
            'frmtrm_amount': '455,905,413,000,000',
            'bsns_year': '2024',
            'reprt_code': '11011',
            'corp_code': '00126380',
        },
    ],
}


@pytest.fixture(name='extractor')
def make_extractor():
  return DARTExtractor()


@pytest.fixture(name='finstate_file')
def make_finstate_file(tmp_path):
  path = tmp_path / '00126380_2024.json'
  path.write_text(
      json.dumps(SAMSUNG_FINSTATE, ensure_ascii=False),
      encoding='utf-8')
  return path


class TestDARTExtractor:

  def test_extract_returns_dataframe(self, extractor, finstate_file):
    df = extractor.extract_facts(finstate_file)
    assert isinstance(df, pd.DataFrame)
    assert not df.empty

  def test_has_required_columns(self, extractor, finstate_file):
    df = extractor.extract_facts(finstate_file)
    required = [
        'corp_code', 'metric', 'sj_div',
        'account_nm', 'val', 'bsns_year',
    ]
    for col in required:
      assert col in df.columns, f'Missing column: {col}'

  def test_parses_amount_with_commas(self, extractor, finstate_file):
    df = extractor.extract_facts(finstate_file)
    # All values should be numeric (commas stripped).
    assert df['val'].dtype in ('float64', 'Float64')
    assert (df['val'] > 0).all()

  def test_maps_account_names_to_metrics(
      self, extractor, finstate_file):
    """Known account names should map to standard metrics."""
    # We override the fixture with Korean account names.
    data = {
        'status': '000',
        'list': [
            {
                'sj_div': 'IS',
                'account_nm': '\ub9e4\ucd9c\uc561',  # 매출액
                'thstrm_amount': '100,000',
                'bsns_year': '2024',
                'reprt_code': '11011',
                'corp_code': '00126380',
            },
            {
                'sj_div': 'BS',
                'account_nm': '\uc790\uc0b0\ucd1d\uacc4',  # 자산총계
                'thstrm_amount': '200,000',
                'bsns_year': '2024',
                'reprt_code': '11011',
                'corp_code': '00126380',
            },
        ],
    }
    path = finstate_file.parent / 'test_kr.json'
    path.write_text(json.dumps(data, ensure_ascii=False),
                    encoding='utf-8')

    df = extractor.extract_facts(path)
    metrics = set(df['metric'].dropna().unique())
    assert 'REVENUE' in metrics
    assert 'TOTAL_ASSETS' in metrics
