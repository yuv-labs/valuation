"""
Run stock screening pipeline.

Usage:
  python -m screening.run                          # Track A → B (default)
  python -m screening.run --track moat             # Track A only
  python -m screening.run --top 30 --min-mcap-kr 1e12
"""

import argparse
import logging
from pathlib import Path

import pandas as pd

from screening.domain import Track
from screening.filters.moat_existence import MoatExistenceFilter
from screening.filters.moat_health import MoatHealthFilter
from screening.filters.opportunity import OpportunityFilter
from screening.report.generator import generate_html
from screening.report.generator import print_table
from screening.scorers.composite import CompositeScorer
from screening.scorers.fear import FearScorer
from screening.scorers.moat import MoatScorer

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
  """Load ticker -> company name mapping."""
  name_map: dict[str, str] = {}

  companies_path = silver_dir / 'sec' / 'companies.parquet'
  if companies_path.exists():
    companies = pd.read_parquet(companies_path)
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
  if not str(ticker).isdigit():
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
) -> pd.DataFrame:
  """Apply market-specific minimum market cap thresholds."""
  df['market'] = df['ticker'].apply(
      lambda t: 'KR' if str(t).isdigit() else 'US')
  us_mask = (df['market'] == 'US') & (
      df['market_cap'].fillna(0) >= min_market_cap_us)
  kr_mask = (df['market'] == 'KR') & (
      df['market_cap'].fillna(0) >= min_market_cap_kr)
  return df[us_mask | kr_mask].copy()


def _run_track_a(df: pd.DataFrame) -> pd.DataFrame:
  """Track A: moat universe — identify durable moat companies."""
  df = MoatExistenceFilter().apply(df)
  logger.info('After moat existence filter: %d', len(df))

  df = MoatHealthFilter(min_signals=2).apply(df)
  logger.info('After moat health filter: %d', len(df))

  if df.empty:
    return df

  moat = MoatScorer()
  df['moat_score'] = df.apply(moat.score, axis=1)
  return df


def _run_track_b(df: pd.DataFrame) -> pd.DataFrame:
  """Track B: opportunity scanner — find moat companies at fair prices."""
  df = OpportunityFilter(min_signals=2).apply(df)
  logger.info('After opportunity filter: %d', len(df))

  if df.empty:
    return df

  fear = FearScorer()
  composite = CompositeScorer()

  df['fear_score'] = df.apply(fear.score, axis=1)
  assert 'moat_score' in df.columns, (
      'Track B requires moat_score from Track A')
  df['opportunity_score'] = df.apply(
      lambda r: composite.score(
          r['fear_score'], r['moat_score']),
      axis=1)

  return df


def run_screening(
    gold_dir: Path,
    silver_dir: Path | None = None,
    track: Track = Track.FULL,
    top_n: int = 30,
    min_market_cap_us: float = 2e9,
    min_market_cap_kr: float = 5e11,
    output_dir: Path | None = None,
) -> pd.DataFrame:
  """Run the screening pipeline. Returns ranked DataFrame."""
  panel = _load_panel(gold_dir)
  latest = panel.sort_values('end').groupby(
      'ticker', as_index=False).tail(1)
  logger.info('Loaded %d tickers', len(latest))

  df = latest.copy()
  df = _filter_market_cap(df, min_market_cap_us, min_market_cap_kr)
  logger.info('After market cap filter: %d', len(df))

  if track == Track.MOAT:
    df = _run_track_a(df)
    sort_col = 'moat_score'
  else:  # Track.FULL: Track A → Track B
    df = _run_track_a(df)
    df = _run_track_b(df)
    sort_col = 'opportunity_score'

  if df.empty:
    logger.warning('No stocks passed filters.')
    return df

  # Company names.
  name_map: dict[str, str] = {}
  if silver_dir:
    name_map = _load_names(silver_dir)
  df['name'] = df['ticker'].apply(
      lambda t: _resolve_kr_name(t, name_map))

  df = df.sort_values(
      ['market', sort_col],
      ascending=[True, False])

  # Output.
  top = df.head(top_n)
  print_table(top)

  if output_dir:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    from datetime import datetime  # pylint: disable=import-outside-toplevel
    today = datetime.now().strftime('%Y%m%d')
    suffix = f'_{track.value}' if track != Track.FULL else ''

    csv_path = output_dir / f'screening_{today}{suffix}.csv'
    df.to_csv(csv_path, index=False)
    logger.info('CSV: %s', csv_path)

    html_path = output_dir / f'screening_{today}{suffix}.html'
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
  parser.add_argument(
      '--track', type=str, default='full',
      choices=[t.value for t in Track])
  parser.add_argument('--top', type=int, default=50)
  parser.add_argument(
      '--min-mcap-us', type=float, default=2e9)
  parser.add_argument(
      '--min-mcap-kr', type=float, default=5e11)
  args = parser.parse_args()

  run_screening(
      gold_dir=args.gold_dir,
      silver_dir=args.silver_dir,
      track=Track(args.track),
      top_n=args.top,
      min_market_cap_us=args.min_mcap_us,
      min_market_cap_kr=args.min_mcap_kr,
      output_dir=args.output_dir,
  )


if __name__ == '__main__':
  logging.basicConfig(
      level=logging.INFO,
      format='%(asctime)s [%(levelname)s] %(message)s',
      datefmt='%Y-%m-%d %H:%M:%S',
  )
  main()
