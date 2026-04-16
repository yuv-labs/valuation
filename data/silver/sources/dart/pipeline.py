"""DART Silver pipeline — Bronze JSON to Silver parquet."""

import json
import logging
from pathlib import Path
import re
from xml.etree import ElementTree

import pandas as pd

from data.silver.core.pipeline import Pipeline
from data.silver.sources.dart.extractors import DARTExtractor

logger = logging.getLogger(__name__)

_QTR_MONTH = {'Q1': '03-31', 'Q2': '06-30', 'Q3': '09-30', 'Q4': '12-31'}


class DARTPipeline(Pipeline):
  """DART financial statements and shares → Silver facts_long + companies."""

  def extract(self) -> None:
    dart_dir = self.context.bronze_dir / 'dart'
    if not dart_dir.exists():
      logger.info('No DART Bronze dir, producing empty output')
      self.datasets['facts_long'] = pd.DataFrame()
      self.datasets['companies'] = pd.DataFrame()
      return

    corp_to_stock = self._load_corp_mapping(dart_dir)
    facts = self._extract_facts(dart_dir, corp_to_stock)
    shares = self._extract_shares(dart_dir, corp_to_stock)

    if not facts.empty and not shares.empty:
      facts = pd.concat([facts, shares], ignore_index=True)
    elif shares.empty:
      pass  # facts only
    else:
      facts = shares

    # Fill SHARES end/filed from actual fact dates per stock.
    if not facts.empty:
      shares_mask = (
          (facts['metric'] == 'SHARES') & facts['end'].isna())
      if shares_mask.any():
        facts = self._fill_shares_dates(facts, shares_mask)

    self.datasets['facts_long'] = facts
    self.datasets['companies'] = self._build_companies(facts)

  def transform(self) -> None:
    # Extraction already produces the target schema.
    pass

  def validate(self) -> None:
    facts = self.datasets.get('facts_long', pd.DataFrame())
    if facts.empty:
      return
    required = [
        'cik10', 'metric', 'val', 'end', 'filed',
        'fy', 'fp', 'fiscal_year', 'fiscal_quarter', 'tag',
    ]
    missing = [c for c in required if c not in facts.columns]
    if missing:
      self.errors.append(f'Missing columns in facts_long: {missing}')

  def load(self) -> None:
    out_dir = self.context.silver_dir / 'dart'
    out_dir.mkdir(parents=True, exist_ok=True)

    facts = self.datasets.get('facts_long', pd.DataFrame())
    if not facts.empty:
      facts['market'] = 'kr'
      facts.to_parquet(out_dir / 'facts_long.parquet', index=False)
      logger.info('DART facts_long: %d rows', len(facts))

    companies = self.datasets.get('companies', pd.DataFrame())
    if not companies.empty:
      companies['market'] = 'kr'
      companies.to_parquet(out_dir / 'companies.parquet', index=False)
      logger.info('DART companies: %d rows', len(companies))

  # -- Private helpers --

  @staticmethod
  def _load_corp_mapping(dart_dir: Path) -> dict[str, str]:
    """Load corp_code → stock_code mapping from CORPCODE.xml."""
    xml_path = dart_dir / 'CORPCODE.xml'
    if not xml_path.exists():
      return {}

    tree = ElementTree.parse(xml_path)  # noqa: S314
    root = tree.getroot()
    result: dict[str, str] = {}
    for item in root.findall('list'):
      corp_el = item.find('corp_code')
      stock_el = item.find('stock_code')
      if (corp_el is not None and stock_el is not None
          and corp_el.text and stock_el.text
          and stock_el.text.strip()):
        result[corp_el.text.strip()] = stock_el.text.strip()
    return result

  @staticmethod
  def _extract_facts(
      dart_dir: Path,
      corp_to_stock: dict[str, str],
  ) -> pd.DataFrame:
    """Extract DART finstate JSONs into facts DataFrame."""
    finstate_dir = dart_dir / 'finstate'
    if not finstate_dir.exists():
      return pd.DataFrame()

    extractor = DARTExtractor()
    parts: list[pd.DataFrame] = []

    for path in sorted(finstate_dir.glob('*.json')):
      if path.name.endswith('.meta.json'):
        continue

      df = extractor.extract_facts(path)
      if df.empty:
        continue

      mapped = df[df['metric'].notna()].copy()
      if mapped.empty:
        continue

      # Map corp_code → stock_code as cik10.
      mapped['cik10'] = mapped['corp_code'].map(
          corp_to_stock).fillna(mapped['corp_code'])
      mapped = mapped.rename(columns={'bsns_year': 'fy'})
      mapped['fiscal_year'] = pd.to_numeric(
          mapped['fy'], errors='coerce')

      # Quarter detection from filename.
      qtr = mapped['quarter'].iloc[0] if (
          'quarter' in mapped.columns
          and mapped['quarter'].notna().any()
      ) else 'Q4'
      mapped['fiscal_quarter'] = qtr
      mapped['fp'] = 'FY' if qtr == 'Q4' else qtr

      # tag column (required by aggregation.py).
      mapped['tag'] = mapped['account_nm']

      # End date from (fy, quarter).
      mm_dd = _QTR_MONTH.get(qtr, '12-31')
      fy_strs = mapped['fy'].astype(str)
      end_str = fy_strs + f'-{mm_dd}'  # type: ignore[operator]
      mapped['end'] = pd.to_datetime(end_str)

      # Approximate filed date.
      filed_lag = 90 if qtr == 'Q4' else 45
      mapped['filed'] = mapped['end'] + pd.Timedelta(days=filed_lag)

      parts.append(mapped)

    if not parts:
      return pd.DataFrame()
    return pd.concat(parts, ignore_index=True)

  @staticmethod
  def _extract_shares(
      dart_dir: Path,
      corp_to_stock: dict[str, str],
  ) -> pd.DataFrame:
    """Extract shares outstanding from DART shares JSONs."""
    shares_dir = dart_dir / 'shares'
    if not shares_dir.exists():
      return pd.DataFrame()

    shares_map: dict[str, float] = {}
    for path in shares_dir.glob('*.json'):
      if path.name.endswith('.meta.json'):
        continue
      try:
        data = json.loads(path.read_text(encoding='utf-8'))
        if data.get('status') != '000' or not data.get('list'):
          continue
        corp_code = path.stem
        stock_code = corp_to_stock.get(corp_code, corp_code)
        for item in data['list']:
          se = item.get('se', '')
          if se.strip() in ('보통주',):
            raw = item.get('istc_totqy', '')
            cleaned = re.sub(r'[,\s]', '', str(raw))
            if cleaned and cleaned != '-':
              shares_map[stock_code] = float(cleaned)
              break
      except (json.JSONDecodeError, OSError, ValueError):
        continue

    if not shares_map:
      return pd.DataFrame()

    # Build SHARES facts rows — one per stock code.
    # Use a nominal end/filed for now; Gold will fill across quarters.
    rows: list[dict] = []
    for stock_code, val in shares_map.items():
      rows.append({
          'cik10': stock_code,
          'metric': 'SHARES',
          'val': val,
          'end': pd.NaT,
          'filed': pd.NaT,
          'fy': '',
          'fp': 'FY',
          'fiscal_year': None,
          'fiscal_quarter': 'Q4',
          'tag': 'shares',
      })
    return pd.DataFrame(rows)

  @staticmethod
  def _fill_shares_dates(
      facts: pd.DataFrame,
      shares_mask: pd.Series,
  ) -> pd.DataFrame:
    """Fill NaT end/filed on SHARES rows from other facts."""
    non_shares = facts[~shares_mask & facts['end'].notna()]
    result_parts = [facts[~shares_mask].copy()]

    for cik10, share_rows in facts[shares_mask].groupby('cik10'):
      cik_facts = non_shares[non_shares['cik10'] == cik10]
      if cik_facts.empty:
        continue
      ends = cik_facts[['end', 'filed', 'fiscal_year',
                         'fiscal_quarter', 'fy',
                         'fp']].drop_duplicates()
      for _, end_row in ends.iterrows():
        expanded = share_rows.copy()
        expanded['end'] = end_row['end']
        expanded['filed'] = end_row['filed']
        expanded['fiscal_year'] = end_row['fiscal_year']
        expanded['fiscal_quarter'] = end_row['fiscal_quarter']
        expanded['fy'] = end_row['fy']
        expanded['fp'] = end_row['fp']
        result_parts.append(expanded)

    return pd.concat(result_parts, ignore_index=True)

  @staticmethod
  def _build_companies(facts: pd.DataFrame) -> pd.DataFrame:
    """Build companies lookup from facts."""
    if facts.empty:
      return pd.DataFrame(columns=['cik10', 'ticker'])

    companies = facts[['cik10']].drop_duplicates().copy()
    companies['ticker'] = companies['cik10']
    return companies.reset_index(drop=True)
