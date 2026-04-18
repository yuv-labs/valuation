"""
SEC data processing pipeline.

Silver layer: Normalization only (no YTD->Q or TTM calculations).
"""
from pathlib import Path

import pandas as pd

from data.shared.io import ParquetWriter
from data.silver.core.pipeline import Pipeline
from data.silver.core.pipeline import PipelineContext
from data.silver.shared.validators import BasicValidator
from data.silver.sources.sec.extractors import SECCompanyFactsExtractor
from data.silver.sources.sec.transforms import SECFactsTransformer


class SECPipeline(Pipeline):
  """Pipeline for SEC data processing."""

  def __init__(self, context: PipelineContext):
    super().__init__(context)
    self.sec_dir = context.bronze_dir / 'sec'
    self.out_dir = context.silver_dir / 'sec'

    self.extractor = SECCompanyFactsExtractor()
    self.transformer = SECFactsTransformer()
    self.validator = BasicValidator()
    self.writer = ParquetWriter()

  def extract(self) -> None:
    """Extract from companyfacts JSON files."""
    cf_files = self._get_companyfact_files()

    companies = self.extractor.extract_companies(
        self.sec_dir / 'company_tickers.json', self.sec_dir / 'submissions')
    self.datasets['companies'] = companies

    facts_list = []
    for cf_file in cf_files:
      try:
        facts = self.extractor.extract_facts(cf_file)
        if not facts.empty:
          facts_list.append(facts)
      except Exception as e:  # pylint: disable=broad-except
        self.errors.append(f'Failed to extract {cf_file.name}: {str(e)}')

    if facts_list:
      self.datasets['facts_raw'] = pd.concat(facts_list, ignore_index=True)
    else:
      self.datasets['facts_raw'] = pd.DataFrame()

  def transform(self) -> None:
    """Apply transformations (normalization only)."""
    facts = self.datasets['facts_raw']
    companies = self.datasets['companies']

    if facts.empty:
      self.datasets['facts_long'] = pd.DataFrame()
      return

    # Infer FYE from data for companies without FYE info
    companies = self._infer_fye(facts, companies)
    self.datasets['companies'] = companies

    # Add fiscal year to all facts
    facts_with_fy = self.transformer.add_fiscal_year(facts, companies)

    # Add fiscal_quarter BEFORE deduplicate (needed for dedup key)
    facts_with_fq = self._add_fiscal_quarter(facts_with_fy, companies)

    # Deduplicate by (fiscal_year, fiscal_quarter, filed) for PIT support
    facts_dedup = self.transformer.deduplicate(facts_with_fq)

    # Normalize values (abs for CAPEX, millions for SHARES)
    facts_normalized = self.transformer.normalize_values(facts_dedup)

    self.datasets['facts_long'] = facts_normalized

  def _infer_fye(self, facts: pd.DataFrame,
                 companies: pd.DataFrame) -> pd.DataFrame:
    """Infer FYE from FY data's end date pattern for companies without FYE."""
    companies = companies.copy()

    # Get FY data end dates
    fy_data = facts[facts['fp'] == 'FY'].copy()
    if fy_data.empty:
      return companies

    fy_data['end_mmdd'] = fy_data['end'].dt.strftime('%m%d')

    # Infer FYE as the most frequent end date pattern per company
    inferred_fye = (fy_data.groupby('cik10')['end_mmdd'].agg(
        lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else None).to_dict())

    # Update companies with inferred FYE where fye_mmdd is None
    def fill_fye(row: pd.Series) -> str:
      if pd.notna(row['fye_mmdd']) and row['fye_mmdd']:
        return str(row['fye_mmdd'])
      return str(inferred_fye.get(row['cik10']) or '1231')

    companies['fye_mmdd'] = companies.apply(  # type: ignore[arg-type]
        fill_fye, axis=1)
    return companies

  def _add_fiscal_quarter(self, df: pd.DataFrame,
                          companies: pd.DataFrame) -> pd.DataFrame:
    """Add fiscal_quarter based on end date and FYE with ±7 day tolerance."""
    from data.silver.shared.transforms import \
        FiscalQuarterCalculator  # pylint: disable=import-outside-toplevel

    df = df.copy()
    fye_series = companies.set_index('cik10')['fye_mmdd']
    fye_map: dict[str, str] = {str(k): str(v) for k, v in fye_series.items()}

    calculator = FiscalQuarterCalculator()
    df['fiscal_quarter'] = calculator.calculate(df, fye_map)
    return df

  def validate(self) -> None:
    """Run validation checks."""
    for name, dataset in self.datasets.items():
      if name == 'facts_raw':
        continue

      validation_result = self.validator.validate(name, dataset)
      if not validation_result.is_valid:
        self.errors.extend(validation_result.errors)

  def load(self) -> None:
    """Write to parquet files."""
    self.out_dir.mkdir(parents=True, exist_ok=True)

    datasets_to_write = {
        'companies': self.datasets.get('companies'),
        'facts_long': self.datasets.get('facts_long'),
    }

    cf_files = self._get_companyfact_files()

    # Calculate target_date as max filed date from facts_long
    target_date = None
    facts_long = self.datasets.get('facts_long')
    has_filed = (facts_long is not None and not facts_long.empty and
                 'filed' in facts_long.columns)
    if has_filed and facts_long is not None:
      target_date = str(facts_long['filed'].max().date())

    for name, dataset in datasets_to_write.items():
      if dataset is None or dataset.empty:
        continue

      output_path = self.out_dir / f'{name}.parquet'

      metadata = {
          'layer': 'silver',
          'source': 'sec',
          'dataset': name,
      }

      inputs = cf_files if name != 'companies' else [
          self.sec_dir / 'company_tickers.json'
      ]

      dataset['market'] = 'us'
      self.writer.write(dataset,
                        output_path,
                        inputs=inputs,
                        metadata=metadata,
                        target_date=target_date)

  def _get_companyfact_files(self) -> list[Path]:
    """Get companyfacts files."""
    cf_dir = self.sec_dir / 'companyfacts'
    if not cf_dir.exists():
      return []
    return sorted(p for p in cf_dir.glob('CIK*.json')
                  if not p.name.endswith('.meta.json'))
