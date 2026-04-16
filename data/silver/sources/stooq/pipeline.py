"""
Stooq data processing pipeline.
"""
from pathlib import Path

import pandas as pd

from data.shared.io import ParquetWriter
from data.silver.core.pipeline import Pipeline
from data.silver.core.pipeline import PipelineContext
from data.silver.shared.validators import BasicValidator


class StooqPipeline(Pipeline):
  """Pipeline for Stooq price data processing."""

  def __init__(self, context: PipelineContext):
    super().__init__(context)
    self.stooq_dir = context.bronze_dir / 'stooq' / 'daily'
    self.out_dir = context.silver_dir / 'stooq'

    self.validator = BasicValidator()
    self.writer = ParquetWriter()

  def extract(self) -> None:
    """Extract from Stooq CSV files."""
    csv_files = self._get_csv_files()

    if not csv_files:
      self.errors.append(f'No stooq csv found under: {self.stooq_dir}')
      self.datasets['prices_daily'] = pd.DataFrame()
      return

    parts: list[pd.DataFrame] = []
    for p in csv_files:
      try:
        sym = p.stem.upper()
        df = pd.read_csv(p)

        rename = {c: c.lower() for c in df.columns}
        df = df.rename(columns=rename)

        if 'date' not in df.columns:
          continue

        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.dropna(subset=['date'])
        df['symbol'] = sym

        parts.append(
            df[['symbol', 'date', 'open', 'high', 'low', 'close', 'volume']])

      except Exception as e:  # pylint: disable=broad-except
        self.errors.append(f'Failed to extract {p.name}: {str(e)}')

    if parts:
      prices = pd.concat(parts, ignore_index=True).sort_values(
          ['symbol', 'date']).reset_index(drop=True)
      self.datasets['prices_daily'] = prices
    else:
      self.datasets['prices_daily'] = pd.DataFrame()

  def transform(self) -> None:
    """Apply transformations (none needed for Stooq)."""
    pass

  def validate(self) -> None:
    """Run validation checks."""
    for name, dataset in self.datasets.items():
      validation_result = self.validator.validate(name, dataset)
      if not validation_result.is_valid:
        self.errors.extend(validation_result.errors)

  def load(self) -> None:
    """Write to parquet files."""
    self.out_dir.mkdir(parents=True, exist_ok=True)

    prices = self.datasets.get('prices_daily')
    if prices is None or prices.empty:
      return

    output_path = self.out_dir / 'prices_daily.parquet'

    metadata = {'layer': 'silver', 'source': 'stooq', 'dataset': 'prices_daily'}

    prices['market'] = 'us'
    csv_files = self._get_csv_files()
    self.writer.write(prices, output_path, inputs=csv_files, metadata=metadata)

  def _get_csv_files(self) -> list[Path]:
    """Get CSV files."""
    if not self.stooq_dir.exists():
      return []
    return sorted(self.stooq_dir.glob('*.csv'))
