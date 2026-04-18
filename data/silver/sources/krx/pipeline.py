"""KRX Silver pipeline — Bronze CSVs to Silver parquet."""

import logging
from pathlib import Path

import pandas as pd

from data.silver.core.pipeline import Pipeline

logger = logging.getLogger(__name__)


def build_krx_prices(
    bronze_dir: Path,
    silver_dir: Path,
) -> Path:
  """Read KRX Bronze CSVs and write Silver prices_daily.parquet.

  Args:
    bronze_dir: Root Bronze directory (contains krx/daily/*.csv)
    silver_dir: Root Silver output directory

  Returns:
    Path to the output parquet file
  """
  krx_csv_dir = bronze_dir / 'krx' / 'daily'
  if not krx_csv_dir.exists():
    raise FileNotFoundError(f'KRX Bronze dir not found: {krx_csv_dir}')

  parts: list[pd.DataFrame] = []

  for csv_path in sorted(krx_csv_dir.glob('*.csv')):
    try:
      df = pd.read_csv(csv_path, encoding='utf-8')
      if df.empty:
        continue

      ticker = csv_path.stem
      date_col = df.columns[0]

      # pykrx uses Korean column names.
      close_col = _find_column(df, ['close', '\uc885\uac00'])
      vol_col = _find_column(df, ['volume', '\uac70\ub798\ub7c9'])

      if close_col is None:
        continue

      out = pd.DataFrame({
          'date': pd.to_datetime(df[date_col]),
          'symbol': ticker,
          'close': pd.to_numeric(df[close_col], errors='coerce'),
      })
      if vol_col is not None:
        out['volume'] = pd.to_numeric(
            df[vol_col], errors='coerce')

      parts.append(out)
    except Exception:  # pylint: disable=broad-except
      logger.warning('Failed to read %s', csv_path.name)

  if not parts:
    raise ValueError('No valid KRX CSV files found')

  prices = pd.concat(parts, ignore_index=True)
  prices = prices.dropna(subset=['date', 'close'])
  prices = prices.sort_values(['symbol', 'date']).reset_index(
      drop=True)

  out_dir = silver_dir / 'krx'
  out_dir.mkdir(parents=True, exist_ok=True)
  out_path = out_dir / 'prices_daily.parquet'
  prices['market'] = 'kr'
  prices.to_parquet(out_path, index=False)

  logger.info(
      'KRX Silver: %d rows, %d symbols -> %s',
      len(prices), prices['symbol'].nunique(), out_path)

  return out_path


class KRXPipeline(Pipeline):
  """KRX daily prices → Silver prices_daily.parquet."""

  def extract(self) -> None:
    krx_csv_dir = self.context.bronze_dir / 'krx' / 'daily'
    if not krx_csv_dir.exists():
      self.datasets['prices_daily'] = pd.DataFrame()
      return

    parts: list[pd.DataFrame] = []
    for csv_path in sorted(krx_csv_dir.glob('*.csv')):
      try:
        df = pd.read_csv(csv_path, encoding='utf-8')
        if df.empty:
          continue

        ticker = csv_path.stem
        date_col = df.columns[0]

        close_col = _find_column(df, ['close', '\uc885\uac00'])
        vol_col = _find_column(df, ['volume', '\uac70\ub798\ub7c9'])
        if close_col is None:
          continue

        out = pd.DataFrame({
            'date': pd.to_datetime(df[date_col]),
            'symbol': ticker,
            'close': pd.to_numeric(df[close_col], errors='coerce'),
        })
        if vol_col is not None:
          out['volume'] = pd.to_numeric(
              df[vol_col], errors='coerce')
        parts.append(out)
      except Exception:  # pylint: disable=broad-except
        logger.warning(
            'Failed to read %s', csv_path.name,
            exc_info=True)

    if not parts:
      self.datasets['prices_daily'] = pd.DataFrame()
      return

    prices = pd.concat(parts, ignore_index=True)
    prices = prices.dropna(subset=['date', 'close'])
    prices = prices.sort_values(
        ['symbol', 'date']).reset_index(drop=True)
    self.datasets['prices_daily'] = prices

  def transform(self) -> None:
    pass

  def validate(self) -> None:
    prices = self.datasets.get('prices_daily', pd.DataFrame())
    if prices.empty:
      return
    required = ['date', 'symbol', 'close']
    missing = [c for c in required if c not in prices.columns]
    if missing:
      self.errors.append(f'Missing columns: {missing}')

  def load(self) -> None:
    prices = self.datasets.get('prices_daily', pd.DataFrame())
    if prices.empty:
      return

    out_dir = self.context.silver_dir / 'krx'
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / 'prices_daily.parquet'
    prices['market'] = 'kr'
    prices.to_parquet(out_path, index=False)

    logger.info(
        'KRX Silver: %d rows, %d symbols -> %s',
        len(prices), prices['symbol'].nunique(), out_path)


def _find_column(
    df: pd.DataFrame,
    candidates: list[str],
) -> str | None:
  """Find first matching column name (case-insensitive)."""
  df_cols_lower: dict[str, str] = {
      c.lower(): c for c in df.columns}
  for cand in candidates:
    if cand.lower() in df_cols_lower:
      return str(df_cols_lower[cand.lower()])
    for col in df.columns:
      if cand in col:
        return str(col)
  return None
