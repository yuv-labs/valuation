"""Tests for KRX Silver pipeline — public interface only."""

from pathlib import Path

import pandas as pd
import pytest

from data.silver.core.pipeline import PipelineContext

BRONZE_DIR = Path('data/bronze/out')
HAS_KRX = (BRONZE_DIR / 'krx' / 'daily').exists()


@pytest.mark.skipif(not HAS_KRX, reason='No KRX Bronze data')
class TestKRXSilverPipeline:
  """Tests for standalone build_krx_prices (legacy)."""

  def test_produces_prices_parquet(self, tmp_path):
    from data.silver.sources.krx.pipeline import \
        build_krx_prices  # pylint: disable=import-outside-toplevel
    build_krx_prices(
        bronze_dir=BRONZE_DIR,
        silver_dir=tmp_path)

    path = tmp_path / 'krx' / 'prices_daily.parquet'
    assert path.exists()

    df = pd.read_parquet(path)
    assert 'date' in df.columns
    assert 'symbol' in df.columns
    assert 'close' in df.columns

  def test_contains_known_ticker(self, tmp_path):
    from data.silver.sources.krx.pipeline import \
        build_krx_prices  # pylint: disable=import-outside-toplevel
    build_krx_prices(
        bronze_dir=BRONZE_DIR,
        silver_dir=tmp_path)

    df = pd.read_parquet(tmp_path / 'krx' / 'prices_daily.parquet')
    assert '005930' in df['symbol'].values

  def test_date_is_datetime(self, tmp_path):
    from data.silver.sources.krx.pipeline import \
        build_krx_prices  # pylint: disable=import-outside-toplevel
    build_krx_prices(
        bronze_dir=BRONZE_DIR,
        silver_dir=tmp_path)

    df = pd.read_parquet(tmp_path / 'krx' / 'prices_daily.parquet')
    assert pd.api.types.is_datetime64_any_dtype(df['date'])


@pytest.mark.skipif(not HAS_KRX, reason='No KRX Bronze data')
class TestKRXPipeline:
  """Tests for KRXPipeline(Pipeline) ABC implementation."""

  def test_run_returns_successful_result(self, tmp_path):
    from data.silver.sources.krx.pipeline import \
        KRXPipeline  # pylint: disable=import-outside-toplevel
    ctx = PipelineContext(bronze_dir=BRONZE_DIR, silver_dir=tmp_path)
    result = KRXPipeline(ctx).run()

    assert result.success
    assert not result.errors

  def test_produces_prices_daily_dataset(self, tmp_path):
    from data.silver.sources.krx.pipeline import \
        KRXPipeline  # pylint: disable=import-outside-toplevel
    ctx = PipelineContext(bronze_dir=BRONZE_DIR, silver_dir=tmp_path)
    result = KRXPipeline(ctx).run()

    assert 'prices_daily' in result.datasets
    df = result.datasets['prices_daily']
    assert not df.empty
    assert 'date' in df.columns
    assert 'symbol' in df.columns
    assert 'close' in df.columns

  def test_writes_parquet_file(self, tmp_path):
    from data.silver.sources.krx.pipeline import \
        KRXPipeline  # pylint: disable=import-outside-toplevel
    ctx = PipelineContext(bronze_dir=BRONZE_DIR, silver_dir=tmp_path)
    KRXPipeline(ctx).run()

    path = tmp_path / 'krx' / 'prices_daily.parquet'
    assert path.exists()
