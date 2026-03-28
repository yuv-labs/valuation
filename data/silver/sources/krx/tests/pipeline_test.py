"""Tests for KRX Silver pipeline — public interface only."""

from pathlib import Path

import pandas as pd
import pytest

BRONZE_DIR = Path('data/bronze/out')
HAS_KRX = (BRONZE_DIR / 'krx' / 'daily').exists()


@pytest.mark.skipif(not HAS_KRX, reason='No KRX Bronze data')
class TestKRXSilverPipeline:

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
