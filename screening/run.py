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

from screening.filters.growth import GrowthFilter
from screening.filters.moat import MoatFilter
from screening.filters.undervalued import UndervaluedFilter
from screening.report.generator import generate_html
from screening.report.generator import print_table
from screening.scorers.composite import CompositeScorer
from screening.scorers.fear import FearScorer
from screening.scorers.quality import QualityScorer

logger = logging.getLogger(__name__)


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

  # US names from SEC companies
  companies_path = silver_dir / 'sec' / 'companies.parquet'
  if companies_path.exists():
    companies = pd.read_parquet(companies_path)
    name_map.update(
        dict(zip(companies['ticker'], companies['title'])))

  # Check if pykrx available for KR name resolution.
  try:
    import pykrx as _  # pylint: disable=import-outside-toplevel  # noqa: F401
    name_map['_krx_resolver'] = 'pykrx'
  except ImportError:
    pass

  return name_map


def _resolve_kr_name(
    ticker: str,
    name_map: dict[str, str],
) -> str:
  """Resolve Korean ticker name via pykrx (cached)."""
  if ticker in name_map:
    return name_map[ticker]
  if '_krx_resolver' in name_map:
    try:
      from pykrx import stock as krx  # pylint: disable=import-outside-toplevel
      resolved: str = krx.get_market_ticker_name(ticker)
      name_map[ticker] = resolved
      return resolved
    except Exception:  # pylint: disable=broad-except
      pass
  return ticker


def _add_consistency(
    df: pd.DataFrame,
    panel: pd.DataFrame,
    years: int = 3,
) -> pd.DataFrame:
  """Add 3Y avg/min/consistency columns for ROE and ROIC."""
  df = df.copy()
  for metric in ('roe', 'roic'):
    avg_col = f'{metric}_{years}y_avg'
    min_col = f'{metric}_{years}y_min'
    cons_col = f'{metric}_{years}y_consistent'
    df[avg_col] = pd.NA
    df[min_col] = pd.NA
    df[cons_col] = pd.NA

    for idx, row in df.iterrows():
      hist = panel[panel['ticker'] == row['ticker']].copy()
      hist['year'] = hist['end'].dt.year
      yearly = hist.groupby('year')[metric].last().dropna()
      recent = yearly.tail(years)
      if len(recent) >= 2:
        df.loc[idx, avg_col] = recent.mean()
        df.loc[idx, min_col] = recent.min()
        df.loc[idx, cons_col] = bool((recent > 0.10).all())

  return df


def run_screening(  # pylint: disable=unused-argument
    gold_dir: Path,
    bronze_dir: Path | None = None,
    silver_dir: Path | None = None,
    top_n: int = 30,
    min_market_cap_us: float = 2e9,
    min_market_cap_kr: float = 5e11,
    output_dir: Path | None = None,
) -> pd.DataFrame:
  """Run the full screening pipeline. Returns ranked DataFrame."""
  panel = _load_panel(gold_dir)
  latest = panel.sort_values('end').groupby(
      'ticker', as_index=False).tail(1)
  logger.info('Loaded %d tickers', len(latest))

  df = latest.copy()
  df['market'] = df['ticker'].apply(
      lambda t: 'KR' if str(t).isdigit() else 'US')

  # Market cap filter.
  us_mask = (df['market'] == 'US') & (
      df['market_cap'].fillna(0) >= min_market_cap_us)
  kr_mask = (df['market'] == 'KR') & (
      df['market_cap'].fillna(0) >= min_market_cap_kr)
  df = df[us_mask | kr_mask].copy()
  logger.info('After market cap filter: %d', len(df))

  # Fundamental filters.
  df = UndervaluedFilter(min_signals=2).apply(df)
  logger.info('After undervalued filter: %d', len(df))

  df = MoatFilter(min_signals=2).apply(df)
  logger.info('After moat filter: %d', len(df))

  df = GrowthFilter(min_signals=1).apply(df)
  logger.info('After growth filter: %d', len(df))

  if df.empty:
    logger.warning('No stocks passed filters.')
    return df

  # Score.
  fear = FearScorer()
  quality = QualityScorer()
  composite = CompositeScorer()

  df['fear_score'] = df.apply(fear.score, axis=1)
  df['quality_score'] = df.apply(quality.score, axis=1)
  df['opportunity_score'] = df.apply(
      lambda r: composite.score(
          r['fear_score'], r['quality_score']),
      axis=1)

  # 3Y consistency.
  df = _add_consistency(df, panel, years=3)

  # Company names.
  name_map: dict[str, str] = {}
  if silver_dir:
    name_map = _load_names(silver_dir)
  df['name'] = df['ticker'].apply(
      lambda t: _resolve_kr_name(t, name_map))

  df = df.sort_values(
      ['market', 'opportunity_score'],
      ascending=[True, False])

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
      '--bronze-dir', type=Path,
      default=Path('data/bronze/out'))
  parser.add_argument(
      '--output-dir', type=Path,
      default=Path('output'))
  parser.add_argument('--top', type=int, default=50)
  parser.add_argument(
      '--min-mcap-us', type=float, default=2e9)
  parser.add_argument(
      '--min-mcap-kr', type=float, default=5e11)
  args = parser.parse_args()

  run_screening(
      gold_dir=args.gold_dir,
      bronze_dir=args.bronze_dir,
      silver_dir=args.silver_dir,
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
