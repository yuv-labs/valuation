"""Tests for DART Silver pipeline — public interface only."""

import json

import pandas as pd
import pytest

from data.silver.core.pipeline import PipelineContext
from data.silver.sources.dart.pipeline import DARTPipeline

# Minimal synthetic Bronze data for testing.
CORP_XML = '''<?xml version="1.0" encoding="UTF-8"?>
<result>
  <list>
    <corp_code>00126380</corp_code>
    <corp_name>삼성전자</corp_name>
    <stock_code>005930</stock_code>
    <modify_date>20240101</modify_date>
  </list>
  <list>
    <corp_code>00164779</corp_code>
    <corp_name>SK하이닉스</corp_name>
    <stock_code>000660</stock_code>
    <modify_date>20240101</modify_date>
  </list>
</result>'''

FINSTATE_Q1 = {
    'status': '000',
    'list': [
        {
            'sj_div': 'CF',
            'account_nm': '영업활동현금흐름',
            'thstrm_amount': '10,000,000',
            'bsns_year': '2024',
            'reprt_code': '11013',
            'corp_code': '00126380',
        },
        {
            'sj_div': 'IS',
            'account_nm': '매출액',
            'thstrm_amount': '50,000,000',
            'bsns_year': '2024',
            'reprt_code': '11013',
            'corp_code': '00126380',
        },
        {
            'sj_div': 'BS',
            'account_nm': '자산총계',
            'thstrm_amount': '500,000,000',
            'bsns_year': '2024',
            'reprt_code': '11013',
            'corp_code': '00126380',
        },
    ],
}

FINSTATE_FY = {
    'status': '000',
    'list': [
        {
            'sj_div': 'CF',
            'account_nm': '영업활동현금흐름',
            'thstrm_amount': '40,000,000',
            'bsns_year': '2024',
            'reprt_code': '11011',
            'corp_code': '00126380',
        },
    ],
}

SHARES_DATA = {
    'status': '000',
    'list': [
        {
            'se': '보통주',
            'istc_totqy': '5,969,782,550',
            'corp_code': '00126380',
        },
    ],
}


@pytest.fixture(name='bronze_dir')
def make_bronze(tmp_path):
  """Create synthetic DART Bronze structure."""
  dart_dir = tmp_path / 'dart'

  # CORPCODE.xml
  dart_dir.mkdir(parents=True)
  (dart_dir / 'CORPCODE.xml').write_text(CORP_XML, encoding='utf-8')

  # Finstate JSONs
  finstate_dir = dart_dir / 'finstate'
  finstate_dir.mkdir()
  (finstate_dir / '00126380_2024_Q1.json').write_text(
      json.dumps(FINSTATE_Q1, ensure_ascii=False), encoding='utf-8')
  (finstate_dir / '00126380_2024.json').write_text(
      json.dumps(FINSTATE_FY, ensure_ascii=False), encoding='utf-8')

  # Shares JSONs
  shares_dir = dart_dir / 'shares'
  shares_dir.mkdir()
  (shares_dir / '00126380.json').write_text(
      json.dumps(SHARES_DATA, ensure_ascii=False), encoding='utf-8')

  return tmp_path


class TestDARTPipeline:

  def test_run_produces_successful_result(self, bronze_dir, tmp_path):
    ctx = PipelineContext(bronze_dir=bronze_dir, silver_dir=tmp_path)
    result = DARTPipeline(ctx).run()

    assert result.success
    assert not result.errors

  def test_produces_facts_long_parquet(self, bronze_dir, tmp_path):
    ctx = PipelineContext(bronze_dir=bronze_dir, silver_dir=tmp_path)
    DARTPipeline(ctx).run()

    path = tmp_path / 'dart' / 'facts_long.parquet'
    assert path.exists()

    df = pd.read_parquet(path)
    assert not df.empty

  def test_facts_long_has_required_schema(self, bronze_dir, tmp_path):
    """Output must match SEC facts_long schema for Gold compatibility."""
    ctx = PipelineContext(bronze_dir=bronze_dir, silver_dir=tmp_path)
    DARTPipeline(ctx).run()

    df = pd.read_parquet(tmp_path / 'dart' / 'facts_long.parquet')
    required = [
        'cik10', 'metric', 'val', 'end', 'filed',
        'fy', 'fp', 'fiscal_year', 'fiscal_quarter', 'tag',
    ]
    for col in required:
      assert col in df.columns, f'Missing column: {col}'

  def test_corp_code_mapped_to_stock_code(self, bronze_dir, tmp_path):
    """cik10 should be stock_code (005930), not corp_code (00126380)."""
    ctx = PipelineContext(bronze_dir=bronze_dir, silver_dir=tmp_path)
    DARTPipeline(ctx).run()

    df = pd.read_parquet(tmp_path / 'dart' / 'facts_long.parquet')
    assert '005930' in df['cik10'].values
    assert '00126380' not in df['cik10'].values

  def test_quarter_detection_from_filename(self, bronze_dir, tmp_path):
    """Q1 file → fiscal_quarter='Q1', FY file → fiscal_quarter='Q4'."""
    ctx = PipelineContext(bronze_dir=bronze_dir, silver_dir=tmp_path)
    DARTPipeline(ctx).run()

    df = pd.read_parquet(tmp_path / 'dart' / 'facts_long.parquet')
    quarters = set(df['fiscal_quarter'].unique())
    assert 'Q1' in quarters
    assert 'Q4' in quarters

  def test_end_date_constructed_from_fy_and_quarter(
      self, bronze_dir, tmp_path):
    ctx = PipelineContext(bronze_dir=bronze_dir, silver_dir=tmp_path)
    DARTPipeline(ctx).run()

    df = pd.read_parquet(tmp_path / 'dart' / 'facts_long.parquet')
    q1_rows = df[df['fiscal_quarter'] == 'Q1']
    assert not q1_rows.empty
    # Q1 2024 → end = 2024-03-31
    assert q1_rows.iloc[0]['end'] == pd.Timestamp('2024-03-31')

  def test_filed_date_estimated(self, bronze_dir, tmp_path):
    """Filed = end + 45d (Q1-Q3) or end + 90d (Q4)."""
    ctx = PipelineContext(bronze_dir=bronze_dir, silver_dir=tmp_path)
    DARTPipeline(ctx).run()

    df = pd.read_parquet(tmp_path / 'dart' / 'facts_long.parquet')
    q1 = df[df['fiscal_quarter'] == 'Q1'].iloc[0]
    q4 = df[df['fiscal_quarter'] == 'Q4'].iloc[0]

    assert q1['filed'] == pd.Timestamp('2024-03-31') + pd.Timedelta(days=45)
    assert q4['filed'] == pd.Timestamp('2024-12-31') + pd.Timedelta(days=90)

  def test_shares_integrated_into_facts(self, bronze_dir, tmp_path):
    """SHARES metric rows added from shares API data."""
    ctx = PipelineContext(bronze_dir=bronze_dir, silver_dir=tmp_path)
    DARTPipeline(ctx).run()

    df = pd.read_parquet(tmp_path / 'dart' / 'facts_long.parquet')
    shares = df[df['metric'] == 'SHARES']
    assert not shares.empty
    assert shares.iloc[0]['val'] == pytest.approx(5_969_782_550.0)

  def test_shares_have_valid_end_and_filed(
      self, bronze_dir, tmp_path):
    """SHARES rows must have real end/filed dates, not NaT."""
    ctx = PipelineContext(bronze_dir=bronze_dir, silver_dir=tmp_path)
    DARTPipeline(ctx).run()

    df = pd.read_parquet(tmp_path / 'dart' / 'facts_long.parquet')
    shares = df[df['metric'] == 'SHARES']
    assert not shares.empty
    assert shares['end'].notna().all()
    assert shares['filed'].notna().all()

  def test_produces_companies_parquet(self, bronze_dir, tmp_path):
    ctx = PipelineContext(bronze_dir=bronze_dir, silver_dir=tmp_path)
    DARTPipeline(ctx).run()

    path = tmp_path / 'dart' / 'companies.parquet'
    assert path.exists()

    df = pd.read_parquet(path)
    assert 'cik10' in df.columns
    assert 'ticker' in df.columns
    assert '005930' in df['ticker'].values

  def test_facts_long_has_market_column(self, bronze_dir, tmp_path):
    ctx = PipelineContext(bronze_dir=bronze_dir, silver_dir=tmp_path)
    DARTPipeline(ctx).run()

    df = pd.read_parquet(tmp_path / 'dart' / 'facts_long.parquet')
    assert 'market' in df.columns
    assert (df['market'] == 'kr').all()

  def test_companies_has_market_column(self, bronze_dir, tmp_path):
    ctx = PipelineContext(bronze_dir=bronze_dir, silver_dir=tmp_path)
    DARTPipeline(ctx).run()

    df = pd.read_parquet(tmp_path / 'dart' / 'companies.parquet')
    assert 'market' in df.columns
    assert (df['market'] == 'kr').all()

  def test_empty_bronze_produces_empty_result(self, tmp_path):
    """No DART data → pipeline succeeds with empty datasets."""
    bronze = tmp_path / 'bronze'
    bronze.mkdir()
    silver = tmp_path / 'silver'
    silver.mkdir()
    ctx = PipelineContext(bronze_dir=bronze, silver_dir=silver)
    result = DARTPipeline(ctx).run()

    assert result.success
