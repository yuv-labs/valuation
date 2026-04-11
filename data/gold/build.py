"""
Build Gold layer panels.

Usage:
  python -m data.gold.build                     # Build all panels
  python -m data.gold.build --panel valuation   # Build specific panel
  python -m data.gold.build --validate          # Validate after build
"""

import argparse
import logging
from pathlib import Path
from typing import Optional, Protocol

import pandas as pd

from data.gold.backtest.panel import BacktestPanelBuilder
from data.gold.screening.panel import ScreeningPanelBuilder
from data.gold.valuation.panel import ValuationPanelBuilder

logger = logging.getLogger(__name__)


class PanelBuilder(Protocol):
  """Structural type for concrete panel builders."""

  def __init__(
      self,
      silver_dir: Path,
      gold_dir: Path,
      min_date: Optional[str] = None,
      markets: Optional[list[str]] = None,
  ) -> None: ...

  def build(self) -> pd.DataFrame: ...

  def validate(self) -> list[str]: ...

  def save(self) -> Path: ...

  def summary(self) -> str: ...


AVAILABLE_PANELS = ['valuation', 'backtest', 'screening']

PANEL_BUILDERS: dict[str, type[PanelBuilder]] = {
    'valuation': ValuationPanelBuilder,
    'backtest': BacktestPanelBuilder,
    'screening': ScreeningPanelBuilder,
}


def build_panels(
    panels: list[str],
    silver_dir: Path,
    gold_dir: Path,
    markets: list[str],
    min_date: str = '2010-01-01',
    validate: bool = True,
) -> None:
  """
  Build specified Gold layer panels.

  Args:
    panels: List of panel names to build
    silver_dir: Path to Silver layer output
    gold_dir: Path to Gold layer output
    markets: Markets to include (e.g., ['us', 'kr'])
    min_date: Minimum date filter
    validate: Whether to validate after build
  """
  pd.set_option('display.max_columns', None)
  pd.set_option('display.width', None)

  for panel_name in panels:
    logger.info('Building: %s', panel_name)

    builder_cls = PANEL_BUILDERS.get(panel_name)
    if builder_cls is None:
      logger.warning('Unknown panel: %s', panel_name)
      continue

    builder = builder_cls(
        silver_dir=silver_dir,
        gold_dir=gold_dir,
        min_date=min_date,
        markets=markets,
    )

    panel = builder.build()

    if validate:
      errors = builder.validate()
      if errors:
        for err in errors:
          logger.error('Validation error: %s', err)
      else:
        logger.info('Validation passed')

    output_path = builder.save()
    logger.info('Saved: %s', output_path)
    logger.info('%s', builder.summary())
    logger.debug('Sample:\n%s', panel.head(5).to_string(index=False))


def main() -> None:
  """CLI entrypoint."""
  parser = argparse.ArgumentParser(description='Build Gold layer panels')
  parser.add_argument(
      '--panel',
      type=str,
      nargs='+',
      default=AVAILABLE_PANELS,
      choices=AVAILABLE_PANELS,
      help='Panels to build (default: all)',
  )
  parser.add_argument(
      '--silver-dir',
      type=Path,
      default=Path('data/silver/out'),
      help='Silver layer directory',
  )
  parser.add_argument(
      '--gold-dir',
      type=Path,
      default=Path('data/gold/out'),
      help='Gold layer output directory',
  )
  parser.add_argument(
      '--markets',
      nargs='+',
      choices=['us', 'kr'],
      default=['us', 'kr'],
      help='Markets to include (default: us kr)',
  )
  parser.add_argument(
      '--min-date',
      type=str,
      default='2010-01-01',
      help='Minimum date filter',
  )
  parser.add_argument(
      '--no-validate',
      action='store_true',
      help='Skip validation',
  )
  args = parser.parse_args()

  build_panels(
      panels=args.panel,
      silver_dir=args.silver_dir,
      gold_dir=args.gold_dir,
      markets=args.markets,
      min_date=args.min_date,
      validate=not args.no_validate,
  )


if __name__ == '__main__':
  logging.basicConfig(
      level=logging.INFO,
      format='%(asctime)s [%(levelname)s] %(message)s',
      datefmt='%Y-%m-%d %H:%M:%S',
  )
  main()
