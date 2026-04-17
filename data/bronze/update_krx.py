"""Update script for KRX stock prices."""
import argparse
from pathlib import Path

from data.bronze.cache import BronzeCache
from data.bronze.providers.krx import KRXProvider
from data.bronze.update import load_tickers_from_file


def run():
  parser = argparse.ArgumentParser(
      description='Update KRX daily prices')
  group = parser.add_mutually_exclusive_group(required=True)
  group.add_argument(
      '--tickers', nargs='+',
      help='List of KRX tickers (e.g. 000270 005850)')
  group.add_argument(
      '--tickers-file', type=Path,
      help='File with one ticker per line')
  parser.add_argument(
      '--out', type=Path,
      default=Path('data/bronze/out'),
      help='Output root directory')
  parser.add_argument(
      '--history-days', type=int,
      default=365 * 5,
      help='Days of history to fetch')
  parser.add_argument(
      '--force', action='store_true',
      help='Force refetch even if fresh')
  parser.add_argument(
      '--cache-dir', type=Path, default=None,
      help='Shared cache directory (default: ~/.cache/valuation/bronze/)')
  parser.add_argument(
      '--no-cache', action='store_true',
      help='Disable shared cache')

  args = parser.parse_args()

  cache = None if args.no_cache else BronzeCache(cache_dir=args.cache_dir)
  if cache is not None:
    print(f'[cache] {cache.cache_dir}')

  tickers = args.tickers or load_tickers_from_file(args.tickers_file)
  print(f'Loaded {len(tickers)} tickers')

  provider = KRXProvider(history_days=args.history_days)
  result = provider.fetch(
      tickers=tickers,
      out_dir=args.out,
      refresh_days=0 if args.force else 1,
      force=args.force,
      cache=cache,
  )

  print(f'Done! Fetched: {result.fetched}, Skipped: {result.skipped}')
  if result.errors:
    print('Errors:')
    for err in result.errors:
      print(f'  - {err}')


if __name__ == '__main__':
  run()
