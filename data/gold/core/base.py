"""
Base class for Gold layer panel builders.

Gold panels are purpose-specific views of Silver data.
Each panel builder loads Silver data, aggregates, joins,
and produces a model-ready parquet panel.
"""

from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd

from data.gold.aggregation import build_quarterly_metrics
from data.gold.config.schemas import PanelSchema
from data.gold.transforms import join_metrics_by_cfo_filed
from data.shared.io import ParquetWriter


@dataclass
class MarketSource:
  """Pointer to Silver layer data for a single market."""
  companies_path: Path
  facts_path: Path
  prices_path: Path


def us_source(silver_dir: Path) -> MarketSource:
  """US market source (SEC + Stooq)."""
  return MarketSource(
      companies_path=silver_dir / 'sec' / 'companies.parquet',
      facts_path=silver_dir / 'sec' / 'facts_long.parquet',
      prices_path=silver_dir / 'stooq' / 'prices_daily.parquet',
  )


def kr_source(silver_dir: Path) -> MarketSource:
  """Korean market source (DART + KRX)."""
  return MarketSource(
      companies_path=silver_dir / 'dart' / 'companies.parquet',
      facts_path=silver_dir / 'dart' / 'facts_long.parquet',
      prices_path=silver_dir / 'krx' / 'prices_daily.parquet',
  )


def jp_source(silver_dir: Path) -> MarketSource:
  """Japanese market source (EDINET + Stooq JP)."""
  return MarketSource(
      companies_path=silver_dir / 'edinet' / 'companies.parquet',
      facts_path=silver_dir / 'edinet' / 'facts_long.parquet',
      prices_path=silver_dir / 'stooq_jp' / 'prices_daily.parquet',
  )


MARKET_SOURCES = {
    'us': us_source,
    'kr': kr_source,
    'jp': jp_source,
}


class BasePanelBuilder(ABC):
  """Base class for panel builders."""

  REQUIRED_METRICS: list[str] = []

  def __init__(
      self,
      silver_dir: Path,
      gold_dir: Path,
      schema: PanelSchema,
      min_date: Optional[str] = None,
      markets: Optional[list[str]] = None,
      preloaded_data: Optional[
          tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]] = None,
  ):
    self.silver_dir = Path(silver_dir)
    self.gold_dir = Path(gold_dir)
    self.schema = schema
    self.min_date = min_date
    self.panel: Optional[pd.DataFrame] = None
    self._preloaded_data = preloaded_data

    if markets is None:
      markets = ['us']
    self._sources: list[MarketSource] = []
    for market in markets:
      factory = MARKET_SOURCES.get(market)
      if factory:
        src = factory(self.silver_dir)
        if src.facts_path.exists():
          self._sources.append(src)

  @abstractmethod
  def build(self) -> pd.DataFrame:
    """Build the panel. Subclasses must implement."""

  def load_shared_data(
      self,
  ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load data for sharing across multiple panel builders."""
    return self._load_data_from_sources()

  def _load_data(
      self,
  ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load data from all configured market sources."""
    if self._preloaded_data is not None:
      return self._preloaded_data
    return self._load_data_from_sources()

  def _load_data_from_sources(
      self,
  ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load data from Silver parquet files."""

    companies_parts: list[pd.DataFrame] = []
    facts_parts: list[pd.DataFrame] = []
    prices_parts: list[pd.DataFrame] = []

    for src in self._sources:
      if src.companies_path.exists():
        companies_parts.append(
            pd.read_parquet(src.companies_path))
      if src.facts_path.exists():
        df = pd.read_parquet(src.facts_path)
        # Normalize fy to string for cross-market concat.
        if 'fy' in df.columns:
          df['fy'] = df['fy'].astype(str)
        facts_parts.append(df)
      if src.prices_path.exists():
        prices_parts.append(
            pd.read_parquet(src.prices_path))

    companies = (pd.concat(companies_parts, ignore_index=True)
                 if companies_parts else pd.DataFrame())
    facts = (pd.concat(facts_parts, ignore_index=True)
             if facts_parts else pd.DataFrame())
    prices = (pd.concat(prices_parts, ignore_index=True)
              if prices_parts else pd.DataFrame())

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

    input_paths = []
    for src in self._sources:
      for p in [src.companies_path, src.facts_path,
                src.prices_path]:
        if p.exists():
          input_paths.append(p)

    writer = ParquetWriter()
    writer.write(
        self.panel,
        output_path,
        inputs=input_paths,
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
