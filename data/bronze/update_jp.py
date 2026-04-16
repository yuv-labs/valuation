"""Update script for Japanese stock data (EDINET + Stooq prices)."""
import argparse
import os
from pathlib import Path

from data.bronze.providers.edinet import EDINETProvider
from data.bronze.providers.stooq import StooqProvider


def run():
  parser = argparse.ArgumentParser(
      description='Update Japanese stock data')
  parser.add_argument(
      '--tickers', nargs='+', required=True,
      help='List of TSE tickers (e.g. 7203 6758)')
  parser.add_argument(
      '--out', type=Path,
      default=Path('data/bronze/out'),
      help='Output root directory')
  parser.add_argument(
      '--history-years', type=int, default=5,
      help='Years of EDINET history to fetch')
  parser.add_argument(
      '--force', action='store_true',
      help='Force refetch even if fresh')
  parser.add_argument(
      '--skip-prices', action='store_true',
      help='Skip Stooq price fetch')

  args = parser.parse_args()

  api_key = os.environ.get('EDINET_API_KEY', '')
  if not api_key:
    raise SystemExit(
        'EDINET_API_KEY is required. '
        'Get one at https://disclosure.edinet-fsa.go.jp/')

  edinet = EDINETProvider(
      api_key=api_key,
      history_years=args.history_years)
  print(f'Fetching EDINET filings for: {args.tickers}...')
  result = edinet.fetch(
      tickers=args.tickers,
      out_dir=args.out,
      refresh_days=0 if args.force else 7,
      force=args.force)

  print(f'EDINET: fetched={result.fetched}, '
        f'skipped={result.skipped}')
  if result.errors:
    for err in result.errors:
      print(f'  - {err}')

  if not args.skip_prices:
    jp_symbols = [f'{t}.JP' for t in args.tickers]
    stooq = StooqProvider()
    print(f'Fetching Stooq JP prices for: {jp_symbols}...')
    price_result = stooq.fetch(
        tickers=jp_symbols,
        out_dir=args.out,
        refresh_days=0 if args.force else 1,
        force=args.force)
    print(f'Stooq JP: fetched={price_result.fetched}, '
          f'skipped={price_result.skipped}')
    if price_result.errors:
      for err in price_result.errors:
        print(f'  - {err}')


if __name__ == '__main__':
  run()
