"""Stooq JP price pipeline — reads JP prices from shared stooq/daily dir."""

from data.silver.core.pipeline import PipelineContext
from data.silver.sources.stooq.pipeline import StooqPipeline


class StooqJPPipeline(StooqPipeline):
  """Stooq pipeline for Japanese prices.

  Reads from the same stooq/daily/ directory as StooqPipeline but
  only processes .JP symbols. Writes to stooq_jp/ with market='jp'.
  """

  def __init__(self, context: PipelineContext):
    super().__init__(context)
    self.out_dir = context.silver_dir / 'stooq_jp'

  def extract(self) -> None:
    super().extract()
    prices = self.datasets.get('prices_daily')
    if prices is not None and not prices.empty:
      jp_mask = prices['symbol'].str.endswith('.JP')
      self.datasets['prices_daily'] = (
          prices[jp_mask].reset_index(drop=True))

  def load(self) -> None:
    self.out_dir.mkdir(parents=True, exist_ok=True)

    prices = self.datasets.get('prices_daily')
    if prices is None or prices.empty:
      return

    prices['market'] = 'jp'
    output_path = self.out_dir / 'prices_daily.parquet'
    metadata = {
        'layer': 'silver',
        'source': 'stooq_jp',
        'dataset': 'prices_daily',
    }
    csv_files = self._get_csv_files()
    self.writer.write(
        prices, output_path, inputs=csv_files, metadata=metadata)
