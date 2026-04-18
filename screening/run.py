"""
Run stock screening pipeline.

Usage:
  python -m screening.run
  python -m screening.run --top 30 --min-mcap-kr 1e12
"""

import argparse
import logging
from pathlib import Path

import pandas as pd

from screening.report.generator import generate_html
from screening.report.generator import print_table
from screening.scorers.composite import CompositeScorer
from screening.scorers.fear import FearScorer
from screening.scorers.moat import MoatScorer
from shared.ticker import is_kr_ticker

logger = logging.getLogger(__name__)

_NAVER_STOCK_API = 'https://m.stock.naver.com/api/stock/{ticker}/basic'


def _load_panel(gold_dir: Path) -> pd.DataFrame:
  path = gold_dir / 'screening_panel.parquet'
  if not path.exists():
    raise FileNotFoundError(
        f'Panel not found: {path}. '
        'Build it first via ScreeningPanelBuilder.')
  return pd.read_parquet(path)


def _load_names(
    silver_dir: Path,
) -> dict[str, str]:
  """Load ticker -> company name mapping from all Silver sources."""
  name_map: dict[str, str] = {}

  for companies_path in sorted(silver_dir.glob('*/companies.parquet')):
    companies = pd.read_parquet(companies_path)
    if 'ticker' in companies.columns and 'title' in companies.columns:
      name_map.update(
          dict(zip(companies['ticker'], companies['title'])))

  return name_map


def _resolve_kr_name(
    ticker: str,
    name_map: dict[str, str],
) -> str:
  """Resolve Korean ticker name via pykrx, falling back to Naver API."""
  if ticker in name_map:
    return name_map[ticker]
  if not is_kr_ticker(ticker):
    return ticker

  # Primary: pykrx
  try:
    from pykrx import stock as krx  # pylint: disable=import-outside-toplevel
    resolved: str = krx.get_market_ticker_name(ticker)
    if resolved:
      name_map[ticker] = resolved
      return resolved
  except Exception:  # pylint: disable=broad-except
    pass

  # Fallback: Naver Finance API
  try:
    import requests  # pylint: disable=import-outside-toplevel
    url = _NAVER_STOCK_API.format(ticker=ticker)
    resp = requests.get(url, timeout=5)
    if resp.ok:
      resolved = resp.json().get('stockName', ticker)
      name_map[ticker] = resolved
      return resolved
  except Exception:  # pylint: disable=broad-except
    pass

  return ticker


def _filter_market_cap(
    df: pd.DataFrame,
    min_market_cap_us: float,
    min_market_cap_kr: float,
    min_market_cap_jp: float = 1e11,
) -> pd.DataFrame:
  """Apply market-specific minimum market cap thresholds."""
  if 'market' not in df.columns:
    df['market'] = df['ticker'].apply(
        lambda t: 'KR' if is_kr_ticker(t) else 'US')
  df['market'] = df['market'].str.upper()

  thresholds = {
      'US': min_market_cap_us,
      'KR': min_market_cap_kr,
      'JP': min_market_cap_jp,
  }
  cap = df['market_cap'].fillna(0)
  mask = pd.Series(False, index=df.index)
  for market, threshold in thresholds.items():
    mask = mask | ((df['market'] == market) & (cap >= threshold))
  return df[mask].copy()


def sort_by_track_score(df: pd.DataFrame) -> pd.DataFrame:
  """Sort by track-appropriate quant score.

  Fisher tickers by fisher_quant_score, Buffett by
  buffett_quant_score, mixed by max of both.
  """
  df = df.copy()
  f_score = df.get(
      'fisher_quant_score',
      pd.Series(0, index=df.index)).fillna(0)
  b_score = df.get(
      'buffett_quant_score',
      pd.Series(0, index=df.index)).fillna(0)
  track = df.get(
      'track_signal', pd.Series('', index=df.index)).fillna('')

  df['_sort'] = pd.Series(0.0, index=df.index)
  df.loc[track == 'fisher', '_sort'] = f_score
  df.loc[track == 'buffett', '_sort'] = b_score
  mixed_mask = ~track.isin(['fisher', 'buffett'])
  df.loc[mixed_mask, '_sort'] = pd.concat(
      [f_score[mixed_mask], b_score[mixed_mask]],
      axis=1).max(axis=1)

  sort_cols = ['market', '_sort'] if 'market' in df.columns else [
      '_sort']
  df = df.sort_values(sort_cols, ascending=[True, False]
                      if 'market' in df.columns else [False])
  return df.drop(columns=['_sort'])


def run_screening(
    gold_dir: Path,
    silver_dir: Path | None = None,
    top_n: int = 30,
    min_market_cap_us: float = 2e9,
    min_market_cap_kr: float = 3e11,
    min_market_cap_jp: float = 1e11,
    output_dir: Path | None = None,
) -> pd.DataFrame:
  """Run the screening pipeline. Returns ranked DataFrame."""
  panel = _load_panel(gold_dir)
  latest = panel.sort_values('end').groupby(
      'ticker', as_index=False).tail(1)
  logger.info('Loaded %d tickers', len(latest))

  df = latest.copy()
  df = _filter_market_cap(df, min_market_cap_us, min_market_cap_kr,
                          min_market_cap_jp=min_market_cap_jp)
  logger.info('After market cap filter: %d', len(df))

  # Apply gold-layer gates (trust, leverage, consecutive ROIC).
  if 'gate_pass' not in df.columns:
    raise ValueError(
        'gate_pass column missing — rebuild the screening panel')
  df = df[df['gate_pass']].copy()
  logger.info('After gate filter: %d', len(df))

  # Add moat/fear/opportunity scores as supplemental columns.
  moat = MoatScorer()
  fear = FearScorer()
  composite = CompositeScorer()
  df['moat_score'] = df.apply(moat.score, axis=1)
  df['fear_score'] = df.apply(fear.score, axis=1)
  df['opportunity_score'] = df.apply(
      lambda r: composite.score(
          r['fear_score'], r['moat_score']),
      axis=1)

  if df.empty:
    logger.warning('No stocks passed filters.')
    return df

  # Company names.
  name_map: dict[str, str] = {}
  if silver_dir:
    name_map = _load_names(silver_dir)
  df['name'] = df['ticker'].apply(
      lambda t: _resolve_kr_name(t, name_map))

  df = sort_by_track_score(df)

  # Output.
  top = df.head(top_n)
  print_table(top)

  if output_dir:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    from datetime import datetime  # pylint: disable=import-outside-toplevel
    today = datetime.now().strftime('%Y%m%d')
    csv_path = output_dir / f'screening_{today}.csv'
    df.to_csv(csv_path, index=False)
    logger.info('CSV: %s', csv_path)

    html_path = output_dir / f'screening_{today}.html'
    generate_html(df, html_path)
    logger.info('HTML: %s', html_path)

  return df


def main() -> None:
  parser = argparse.ArgumentParser(
      description='Run stock screening')
  parser.add_argument(
      '--gold-dir', type=Path,
      default=Path('data/gold/out'))
  parser.add_argument(
      '--silver-dir', type=Path,
      default=Path('data/silver/out'))
  parser.add_argument(
      '--output-dir', type=Path,
      default=Path('output'))
  parser.add_argument('--top', type=int, default=50)
  parser.add_argument(
      '--min-mcap-us', type=float, default=2e9)
  parser.add_argument(
      '--min-mcap-kr', type=float, default=3e11)
  parser.add_argument(
      '--min-mcap-jp', type=float, default=1e11)
  args = parser.parse_args()

  run_screening(
      gold_dir=args.gold_dir,
      silver_dir=args.silver_dir,
      top_n=args.top,
      min_market_cap_us=args.min_mcap_us,
      min_market_cap_kr=args.min_mcap_kr,
      min_market_cap_jp=args.min_mcap_jp,
      output_dir=args.output_dir,
  )


if __name__ == '__main__':
  logging.basicConfig(
      level=logging.INFO,
      format='%(asctime)s [%(levelname)s] %(message)s',
      datefmt='%Y-%m-%d %H:%M:%S',
  )
  main()
