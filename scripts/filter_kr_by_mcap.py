"""Filter KR tickers by market cap using existing Gold panel data."""
import pandas as pd

from shared.ticker import is_kr_ticker


def main():
  min_mcap = 3e11
  panel_path = 'data/gold/out/screening_panel.parquet'

  df = pd.read_parquet(panel_path)
  kr = df[df['ticker'].apply(is_kr_ticker)]
  latest = kr.sort_values('end').groupby('ticker').tail(1)
  big = latest[latest['market_cap'] >= min_mcap]
  tickers = sorted(big['ticker'].unique())

  out = 'example/tickers/kr_filtered.txt'
  with open(out, encoding='utf-8', mode='w') as f:
    f.write(
        f'# KR tickers >= 3000억 mcap ({len(tickers)} tickers)\n')
    f.write('# Source: existing Gold screening panel\n')
    for t in tickers:
      f.write(t + '\n')

  print(f'{len(tickers)} tickers saved to {out}')
  total = latest['ticker'].nunique()
  print(f'(from {total} total KR tickers)')


if __name__ == '__main__':
  main()
