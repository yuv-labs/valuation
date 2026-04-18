"""
Silver layer build CLI.

Usage:
    python -m data.silver.build                  # US only (default)
    python -m data.silver.build --markets kr     # Korea only
    python -m data.silver.build --markets us kr  # Both
"""
import argparse
import logging
from pathlib import Path
from typing import Any

from data.silver.core.pipeline import PipelineContext
from data.silver.sources.dart.pipeline import DARTPipeline
from data.silver.sources.edinet.pipeline import EDINETPipeline
from data.silver.sources.krx.pipeline import KRXPipeline
from data.silver.sources.sec.pipeline import SECPipeline
from data.silver.sources.stooq.pipeline import StooqPipeline
from data.silver.sources.stooq_jp.pipeline import StooqJPPipeline

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Market -> pipeline sources mapping.
MARKET_SOURCES: dict[str, dict[str, type]] = {
    'us': {
        'sec': SECPipeline,
        'stooq': StooqPipeline,
    },
    'kr': {
        'dart': DARTPipeline,
        'krx': KRXPipeline,
    },
    'jp': {
        'edinet': EDINETPipeline,
        'stooq_jp': StooqJPPipeline,
    },
}


def main() -> None:
  parser = argparse.ArgumentParser(
      description='Build Silver layer')
  parser.add_argument(
      '--markets',
      nargs='+',
      choices=['us', 'kr', 'jp'],
      default=['us'],
      help='Markets to build (default: us)')
  parser.add_argument(
      '--bronze-dir',
      type=Path,
      default=Path('data/bronze/out'))
  parser.add_argument(
      '--silver-dir',
      type=Path,
      default=Path('data/silver/out'))
  args = parser.parse_args()

  context = PipelineContext(
      bronze_dir=args.bronze_dir,
      silver_dir=args.silver_dir)

  # Resolve which pipelines to run.
  pipeline_classes: dict[str, type] = {}
  for market in args.markets:
    srcs = MARKET_SOURCES.get(market, {})
    for name, cls in srcs.items():
      pipeline_classes[name] = cls

  # Run all pipelines.
  results: dict[str, Any] = {}
  for name, cls in pipeline_classes.items():
    logger.info('Running %s pipeline...', name)
    results[name] = cls(context).run()

  # Summary.
  success_count = sum(
      1 for r in results.values() if r.success)
  print()
  print('=' * 70)
  print(
      f'Build Summary: {success_count}/{len(results)} '
      f'pipelines succeeded')
  print('=' * 70)

  for name, result in results.items():
    if result.success:
      logger.info('\u2713 %s pipeline completed', name)
      if hasattr(result, 'datasets'):
        for dname, df in result.datasets.items():
          if hasattr(df, 'shape'):
            logger.info('  %s: %s', dname, df.shape)
    else:
      logger.error('\u2717 %s pipeline failed', name)
      if hasattr(result, 'errors'):
        for error in result.errors:
          logger.error('  %s', error)

  if success_count < len(results):
    raise SystemExit(1)


if __name__ == '__main__':
  main()
