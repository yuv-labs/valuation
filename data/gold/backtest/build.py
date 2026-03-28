"""
Build backtest panel.

Usage:
  python -m data.gold.backtest.build
  python -m data.gold.backtest.build --no-validate
"""

import argparse
import logging
from pathlib import Path

from data.gold.backtest.panel import BacktestPanelBuilder

logger = logging.getLogger(__name__)


def main() -> None:
  """CLI entrypoint."""
  parser = argparse.ArgumentParser(
      description='Build Gold backtest panel')
  parser.add_argument(
      '--silver-dir', type=Path,
      default=Path('data/silver/out'))
  parser.add_argument(
      '--gold-dir', type=Path,
      default=Path('data/gold/out'))
  parser.add_argument(
      '--min-date', type=str, default='2010-01-01')
  parser.add_argument(
      '--no-validate', action='store_true')
  args = parser.parse_args()

  builder = BacktestPanelBuilder(
      silver_dir=args.silver_dir,
      gold_dir=args.gold_dir,
      min_date=args.min_date,
  )
  builder.build()

  if not args.no_validate:
    errors = builder.validate()
    if errors:
      for err in errors:
        logger.error('Validation error: %s', err)
    else:
      logger.info('Validation passed')

  output_path = builder.save()
  logger.info('Saved: %s', output_path)
  logger.info('%s', builder.summary())


if __name__ == '__main__':
  logging.basicConfig(
      level=logging.INFO,
      format='%(asctime)s [%(levelname)s] %(message)s',
      datefmt='%Y-%m-%d %H:%M:%S',
  )
  main()
