"""
Base class for Gold layer panel builders.

Gold panels are purpose-specific views of Silver data.
Each panel builder loads Silver data, aggregates, joins,
and produces a model-ready parquet panel.
"""

from abc import ABC
from abc import abstractmethod
from pathlib import Path
from typing import Optional

import pandas as pd

from data.gold.aggregation import build_quarterly_metrics
from data.gold.config.schemas import PanelSchema
from data.gold.transforms import join_metrics_by_cfo_filed
from data.shared.io import ParquetWriter


class BasePanelBuilder(ABC):
  """Base class for panel builders."""

  REQUIRED_METRICS: list[str] = []

  def __init__(
      self,
      silver_dir: Path,
      gold_dir: Path,
      schema: PanelSchema,
      min_date: Optional[str] = None,
  ):
    self.silver_dir = Path(silver_dir)
    self.gold_dir = Path(gold_dir)
    self.schema = schema
    self.min_date = min_date
    self.panel: Optional[pd.DataFrame] = None

  @abstractmethod
  def build(self) -> pd.DataFrame:
    """Build the panel. Subclasses must implement."""

  def _load_data(self) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load required data from Silver layer."""
    companies = pd.read_parquet(
        self.silver_dir / 'sec' / 'companies.parquet')
    facts = pd.read_parquet(
        self.silver_dir / 'sec' / 'facts_long.parquet')
    prices = pd.read_parquet(
        self.silver_dir / 'stooq' / 'prices_daily.parquet')
    return companies, facts, prices

  def _build_quarterly_metrics(
      self, facts: pd.DataFrame) -> pd.DataFrame:
    """Convert facts (YTD) to quarterly values with TTM."""
    return build_quarterly_metrics(facts)

  def _build_wide_metrics(
      self, metrics_q: pd.DataFrame) -> pd.DataFrame:
    """Join metrics using CFO's filed date as the reference."""
    filtered = metrics_q[
        metrics_q['metric'].isin(self.REQUIRED_METRICS)]
    return join_metrics_by_cfo_filed(filtered)

  def validate(self) -> list[str]:
    """Validate the built panel against schema."""
    if self.panel is None:
      return ['Panel not built yet. Call build() first.']
    return self.schema.validate(self.panel)

  def save(self) -> Path:
    """Save the panel to Gold output directory."""
    if self.panel is None:
      raise ValueError('Panel not built. Call build() first.')

    self.gold_dir.mkdir(parents=True, exist_ok=True)
    output_path = self.gold_dir / f'{self.schema.name}.parquet'

    writer = ParquetWriter()
    writer.write(
        self.panel,
        output_path,
        inputs=[
            self.silver_dir / 'sec' / 'companies.parquet',
            self.silver_dir / 'sec' / 'facts_long.parquet',
            self.silver_dir / 'stooq' / 'prices_daily.parquet',
        ],
        metadata={
            'layer': 'gold',
            'dataset': self.schema.name,
            'min_date': self.min_date,
            'schema_version': '1.0',
        },
    )
    return output_path

  def summary(self) -> str:
    """Return summary of the built panel."""
    if self.panel is None:
      return 'Panel not built yet.'

    panel = self.panel
    n_tickers = panel['ticker'].nunique()
    date_min = panel['end'].min()
    date_max = panel['end'].max()
    return '\n'.join([
        f'Panel: {self.schema.name}',
        f'Shape: {panel.shape}',
        f'Tickers: {n_tickers}',
        f'Date range: {date_min} to {date_max}',
        f'Columns: {list(panel.columns)}',
    ])
