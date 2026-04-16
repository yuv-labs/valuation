"""Ingest Stooq daily dump ZIP into Bronze layer.

Download the US daily dump from https://stooq.com/db/h/ (Historical Data,
U.S. Daily ASCII), then run:
  python -m data.bronze.ingest_stooq_dump \
    --zip ~/Downloads/d_us_txt.zip
  python -m data.bronze.ingest_stooq_dump \
    --zip ~/Downloads/d_us_txt.zip \
    --tickers-file example/tickers/russell1000.txt

This replaces the per-ticker StooqProvider for bulk ingestion.
Output lands in the same directory (stooq/daily/*.csv) and the
Silver StooqPipeline reads both formats identically.

Note: Unlike the raw-only convention of other Bronze scripts, this
script converts the dump's angle-bracket headers and YYYYMMDD dates
into the Silver-compatible CSV format during extraction. This is a
pragmatic trade-off — storing raw dump bytes would require extending
Silver to handle the dump format.
"""
import argparse
import io
from pathlib import Path
import zipfile

import pandas as pd

from data.bronze.update import _atomic_write_bytes
from data.bronze.update import load_tickers_from_file


def _convert_dump_to_csv(raw_bytes: bytes) -> bytes:
  df = pd.read_csv(io.BytesIO(raw_bytes))
  df.columns = pd.Index([c.strip('<>').lower() for c in df.columns])
  df = df.rename(columns={
      'date': 'Date',
      'open': 'Open',
      'high': 'High',
      'low': 'Low',
      'close': 'Close',
      'vol': 'Volume',
  })
  df['Date'] = pd.to_datetime(
      df['Date'].astype(str), format='%Y%m%d',
  ).dt.strftime('%Y-%m-%d')
  df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
  return df.to_csv(index=False).encode('utf-8')


def run(
    zip_path: Path,
    out_dir: Path,
    tickers_file: Path | None,
) -> None:
  stooq_dir = out_dir / 'stooq' / 'daily'
  stooq_dir.mkdir(parents=True, exist_ok=True)

  allowed_tickers: set[str] | None = None
  if tickers_file:
    raw_tickers = load_tickers_from_file(tickers_file)
    allowed_tickers = {t.lower() for t in raw_tickers}
    print(f'Filtering to {len(allowed_tickers)} tickers'
          f' from {tickers_file}')

  extracted = 0
  skipped = 0
  errors = 0

  with zipfile.ZipFile(zip_path) as zf:
    for info in zf.infolist():
      if info.is_dir():
        continue
      name = info.filename.lower()
      if not name.endswith('.txt'):
        continue

      basename = Path(name).name
      symbol = basename.replace('.txt', '')

      if allowed_tickers:
        ticker_bare = symbol.removesuffix('.us')
        if ticker_bare not in allowed_tickers:
          skipped += 1
          continue

      csv_name = basename.replace('.txt', '.csv')
      dest = stooq_dir / csv_name

      try:
        raw = zf.read(info.filename)
        converted = _convert_dump_to_csv(raw)
        _atomic_write_bytes(dest, converted)
        extracted += 1
      except Exception as exc:  # pylint: disable=broad-except
        errors += 1
        if errors <= 5:
          print(f'  Error {symbol}: {exc}')

      if extracted % 200 == 0 and extracted > 0:
        print(f'  extracted {extracted} files...')

  print(f'Done. Extracted: {extracted},'
        f' Skipped: {skipped}, Errors: {errors}')
  print(f'Output: {stooq_dir}')


def main():
  parser = argparse.ArgumentParser(
      description='Ingest Stooq daily dump ZIP into Bronze')
  parser.add_argument(
      '--zip', type=Path, required=True,
      help='Path to Stooq dump ZIP (e.g. d_us_txt.zip)')
  parser.add_argument(
      '--out', type=Path, default=Path('data/bronze/out'),
      help='Bronze output directory')
  parser.add_argument(
      '--tickers-file', type=Path, default=None,
      help='Only extract tickers in this file (optional)')
  args = parser.parse_args()

  if not args.zip.exists():
    raise FileNotFoundError(f'ZIP not found: {args.zip}')

  run(args.zip, args.out, args.tickers_file)


if __name__ == '__main__':
  main()
