"""Tests for EDINET Silver pipeline — public interface only."""

import io
import zipfile

import pandas as pd
import pytest

from data.silver.core.pipeline import PipelineContext
from data.silver.sources.edinet.pipeline import EDINETPipeline
from data.silver.sources.edinet.tests.extractor_test import JGAAP_XBRL

EDINET_CODE_CSV = (
    'EDINET code,Type,Listed/Unlisted,Consolidated/Individual,'
    'Capital,Settlement date,Submitter name,'
    'Submitter name (English),Submitter name (Kana),'
    'Address,Industry,Securities code,Corporate number\n'
    'E02529,Corporation,Listed,Consolidated,635400000000,'
    '3月,トヨタ自動車株式会社,TOYOTA MOTOR CORPORATION,'
    'トヨタジドウシャ,愛知県豊田市,Transportation Equipment,72030,'
    '1180301018771\n'
)


@pytest.fixture(name='bronze_dir')
def make_bronze(tmp_path):
  edinet_dir = tmp_path / 'edinet'
  edinet_dir.mkdir()

  (edinet_dir / 'EdinetcodeDlInfo.csv').write_text(
      EDINET_CODE_CSV, encoding='utf-8')

  xbrl_dir = edinet_dir / 'xbrl'
  xbrl_dir.mkdir()

  buf = io.BytesIO()
  with zipfile.ZipFile(buf, 'w') as zf:
    zf.writestr('XBRL/PublicDoc/toyota_2025.xbrl', JGAAP_XBRL)
  (xbrl_dir / 'E02529_2025-03-31_120.zip').write_bytes(
      buf.getvalue())

  return tmp_path


class TestEDINETPipeline:

  def test_run_produces_successful_result(self, bronze_dir, tmp_path):
    ctx = PipelineContext(bronze_dir=bronze_dir, silver_dir=tmp_path)
    result = EDINETPipeline(ctx).run()
    assert result.success
    assert not result.errors

  def test_produces_facts_long_parquet(self, bronze_dir, tmp_path):
    ctx = PipelineContext(bronze_dir=bronze_dir, silver_dir=tmp_path)
    EDINETPipeline(ctx).run()

    path = tmp_path / 'edinet' / 'facts_long.parquet'
    assert path.exists()
    df = pd.read_parquet(path)
    assert not df.empty

  def test_facts_long_has_required_schema(self, bronze_dir, tmp_path):
    ctx = PipelineContext(bronze_dir=bronze_dir, silver_dir=tmp_path)
    EDINETPipeline(ctx).run()

    df = pd.read_parquet(tmp_path / 'edinet' / 'facts_long.parquet')
    required = [
        'cik10', 'metric', 'val', 'end', 'filed',
        'fy', 'fp', 'fiscal_year', 'fiscal_quarter', 'tag',
    ]
    for col in required:
      assert col in df.columns, f'Missing column: {col}'

  def test_facts_long_has_market_column(self, bronze_dir, tmp_path):
    ctx = PipelineContext(bronze_dir=bronze_dir, silver_dir=tmp_path)
    EDINETPipeline(ctx).run()

    df = pd.read_parquet(tmp_path / 'edinet' / 'facts_long.parquet')
    assert 'market' in df.columns
    assert (df['market'] == 'jp').all()

  def test_ticker_is_4_digit_code(self, bronze_dir, tmp_path):
    ctx = PipelineContext(bronze_dir=bronze_dir, silver_dir=tmp_path)
    EDINETPipeline(ctx).run()

    df = pd.read_parquet(tmp_path / 'edinet' / 'facts_long.parquet')
    assert '7203' in df['cik10'].values

  def test_produces_companies_parquet(self, bronze_dir, tmp_path):
    ctx = PipelineContext(bronze_dir=bronze_dir, silver_dir=tmp_path)
    EDINETPipeline(ctx).run()

    path = tmp_path / 'edinet' / 'companies.parquet'
    assert path.exists()
    df = pd.read_parquet(path)
    assert 'ticker' in df.columns
    assert 'market' in df.columns
    assert '7203' in df['ticker'].values

  def test_empty_bronze_produces_empty_result(self, tmp_path):
    bronze = tmp_path / 'bronze'
    bronze.mkdir()
    silver = tmp_path / 'silver'
    silver.mkdir()
    ctx = PipelineContext(bronze_dir=bronze, silver_dir=silver)
    result = EDINETPipeline(ctx).run()
    assert result.success
