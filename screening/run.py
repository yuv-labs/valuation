"""
Run stock screening pipeline.

Usage:
  python -m screening.run --market us --top 25
"""

import argparse
import logging
from pathlib import Path

import pandas as pd
from tabulate import tabulate  # type: ignore[import-untyped]

from screening.filters.growth import GrowthFilter
from screening.filters.moat import MoatFilter
from screening.filters.undervalued import UndervaluedFilter
from screening.scorers.composite import CompositeScorer
from screening.scorers.fear import FearScorer
from screening.scorers.quality import QualityScorer

logger = logging.getLogger(__name__)

DISPLAY_COLS = [
    ('ticker', 'Ticker'),
    ('pe_ratio', 'PE'),
    ('pb_ratio', 'PB'),
    ('roe', 'ROE'),
    ('roic', 'ROIC'),
    ('fcf_yield', 'FCF Yld'),
    ('op_margin', 'Op Mgn'),
    ('debt_to_equity', 'D/E'),
    ('fear_score', 'Fear'),
    ('quality_score', 'Quality'),
    ('opportunity_score', 'Opp'),
]


def _load_screening_panel(gold_dir: Path) -> pd.DataFrame:
  path = gold_dir / 'screening_panel.parquet'
  if not path.exists():
    raise FileNotFoundError(
        f'Screening panel not found at {path}. '
        'Run: python -m data.gold.screening.build')
  return pd.read_parquet(path)


def _latest_snapshot(panel: pd.DataFrame) -> pd.DataFrame:
  """Keep only the most recent period per ticker."""
  panel = panel.sort_values('end')
  return panel.groupby('ticker', as_index=False).tail(1)


def _fmt(val, decimals=2):
  if pd.isna(val) or val is None:
    return '-'
  if isinstance(val, float):
    return f'{val:.{decimals}f}'
  return str(val)


def run_screening(
    gold_dir: Path,
    top_n: int = 25,
) -> pd.DataFrame:
  """Run the full screening pipeline."""
  panel = _load_screening_panel(gold_dir)
  df = _latest_snapshot(panel)
  logger.info('Loaded %d tickers from screening panel', len(df))

  # Apply filters.
  df = UndervaluedFilter(min_signals=2).apply(df)
  logger.info('After undervalued filter: %d', len(df))

  df = MoatFilter(min_signals=2).apply(df)
  logger.info('After moat filter: %d', len(df))

  df = GrowthFilter(min_signals=1).apply(df)
  logger.info('After growth filter: %d', len(df))

  if df.empty:
    logger.warning('No stocks passed all filters.')
    return df

  # Score.
  fear_scorer = FearScorer()
  quality_scorer = QualityScorer()
  composite_scorer = CompositeScorer()

  df = df.copy()
  df['fear_score'] = df.apply(fear_scorer.score, axis=1)
  df['quality_score'] = df.apply(quality_scorer.score, axis=1)
  df['opportunity_score'] = df.apply(
      lambda r: composite_scorer.score(
          r['fear_score'], r['quality_score']),
      axis=1,
  )

  df = df.sort_values('opportunity_score', ascending=False)

  # Report.
  top = df.head(top_n)
  headers = [label for _, label in DISPLAY_COLS]
  rows = []
  for _, row in top.iterrows():
    rows.append([_fmt(row.get(col)) for col, _ in DISPLAY_COLS])

  sep = '=' * 60
  print(f'\n{sep}')
  print(f'  Top {min(top_n, len(top))} Screening Results')
  print(f'{sep}')
  print(tabulate(rows, headers=headers, tablefmt='simple',
                 stralign='right'))
  print(f'\nTotal candidates: {len(df)}')

  return df


def main() -> None:
  parser = argparse.ArgumentParser(
      description='Run stock screening')
  parser.add_argument(
      '--gold-dir', type=Path,
      default=Path('data/gold/out'))
  parser.add_argument(
      '--top', type=int, default=25)
  args = parser.parse_args()

  run_screening(gold_dir=args.gold_dir, top_n=args.top)


if __name__ == '__main__':
  logging.basicConfig(
      level=logging.INFO,
      format='%(asctime)s [%(levelname)s] %(message)s',
      datefmt='%Y-%m-%d %H:%M:%S',
  )
  main()
