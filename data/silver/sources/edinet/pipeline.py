"""EDINET Silver pipeline — Bronze XBRL to Silver parquet."""

import csv
import io
import logging
from pathlib import Path

import pandas as pd

from data.silver.core.pipeline import Pipeline
from data.silver.sources.edinet.extractors import EDINETExtractor

logger = logging.getLogger(__name__)


class EDINETPipeline(Pipeline):
  """EDINET XBRL filings → Silver facts_long + companies."""

  def extract(self) -> None:
    edinet_dir = self.context.bronze_dir / 'edinet'
    if not edinet_dir.exists():
      logger.info('No EDINET Bronze dir, producing empty output')
      self.datasets['facts_long'] = pd.DataFrame()
      self.datasets['companies'] = pd.DataFrame()
      return

    edinet_to_sec = self._load_code_mapping(edinet_dir)
    facts = self._extract_all_xbrl(edinet_dir, edinet_to_sec)

    self.datasets['facts_long'] = facts
    self.datasets['companies'] = self._build_companies(
        facts, edinet_to_sec)

  def transform(self) -> None:
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
      self.errors.append(
          f'Missing columns in facts_long: {missing}')

  def load(self) -> None:
    out_dir = self.context.silver_dir / 'edinet'
    out_dir.mkdir(parents=True, exist_ok=True)

    facts = self.datasets.get('facts_long', pd.DataFrame())
    if not facts.empty:
      facts['market'] = 'jp'
      facts.to_parquet(out_dir / 'facts_long.parquet', index=False)
      logger.info('EDINET facts_long: %d rows', len(facts))

    companies = self.datasets.get('companies', pd.DataFrame())
    if not companies.empty:
      companies['market'] = 'jp'
      companies.to_parquet(
          out_dir / 'companies.parquet', index=False)
      logger.info('EDINET companies: %d rows', len(companies))

  @staticmethod
  def _load_code_mapping(
      edinet_dir: Path,
  ) -> dict[str, dict]:
    """Load EDINET code → {sec_code, name, name_en} mapping."""
    csv_path = edinet_dir / 'EdinetcodeDlInfo.csv'
    if not csv_path.exists():
      return {}

    result: dict[str, dict] = {}
    text = csv_path.read_bytes().decode('utf-8-sig')
    reader = csv.DictReader(io.StringIO(text))

    for row in reader:
      edinet_code = (row.get('EDINET code')
                     or row.get('EDINETコード', '')).strip()
      sec_code = (row.get('Securities code')
                  or row.get('証券コード', '')).strip()
      name = (row.get('Submitter name')
              or row.get('提出者名', '')).strip()
      name_en = (row.get('Submitter name (English)')
                 or row.get('提出者名（英字）', '')).strip()

      settlement = (row.get('Settlement date')
                    or row.get('決算日', '')).strip()
      fye_month = _parse_settlement_month(settlement)

      if edinet_code and sec_code:
        ticker = sec_code[:4] if len(sec_code) == 5 else sec_code
        result[edinet_code] = {
            'sec_code': sec_code,
            'ticker': ticker,
            'name': name,
            'name_en': name_en,
            'fye_month': fye_month,
        }

    return result

  @staticmethod
  def _extract_all_xbrl(
      edinet_dir: Path,
      edinet_to_sec: dict[str, dict],
  ) -> pd.DataFrame:
    """Extract facts from all XBRL zips."""
    xbrl_dir = edinet_dir / 'xbrl'
    if not xbrl_dir.exists():
      return pd.DataFrame()

    extractor = EDINETExtractor()
    parts: list[pd.DataFrame] = []

    for zip_path in sorted(xbrl_dir.glob('*.zip')):
      df = extractor.extract_facts(zip_path)
      if df.empty:
        continue

      edinet_code, period_end, doc_type = _parse_filename(
          zip_path.stem)

      info = edinet_to_sec.get(edinet_code, {})
      ticker = info.get('ticker', edinet_code)

      df['cik10'] = ticker

      if period_end:
        df['end'] = pd.to_datetime(df['end'])
        end_ts = pd.Timestamp(period_end)
        year = end_ts.year
        month = end_ts.month

        fye_month: int = info.get('fye_month', 3)
        fiscal_year = year if month <= fye_month else year + 1

        fq = _infer_fiscal_quarter(month, fye_month)
        df['fiscal_year'] = fiscal_year
        df['fiscal_quarter'] = fq
        df['fy'] = str(fiscal_year)
        df['fp'] = 'FY' if fq == 'Q4' else fq

        filed_lag = 90 if doc_type == '120' else 45
        df['filed'] = end_ts + pd.Timedelta(days=filed_lag)
      else:
        df['fiscal_year'] = None
        df['fiscal_quarter'] = None
        df['fy'] = ''
        df['fp'] = ''
        df['filed'] = pd.NaT

      parts.append(df)

    if not parts:
      return pd.DataFrame()
    return pd.concat(parts, ignore_index=True)

  @staticmethod
  def _build_companies(
      facts: pd.DataFrame,
      edinet_to_sec: dict[str, dict],
  ) -> pd.DataFrame:
    if facts.empty:
      return pd.DataFrame(columns=['cik10', 'ticker', 'title'])

    tickers = facts['cik10'].unique()
    rows: list[dict] = []
    edinet_by_ticker = {
        v['ticker']: v for v in edinet_to_sec.values()
    }
    for t in tickers:
      info = edinet_by_ticker.get(t, {})
      rows.append({
          'cik10': t,
          'ticker': t,
          'title': info.get('name_en') or info.get('name', t),
      })
    return pd.DataFrame(rows)


def _parse_filename(stem: str) -> tuple[str, str, str]:
  """Parse 'E02529_2025-03-31_120' → (edinet_code, period_end, doc_type)."""
  parts = stem.split('_')
  edinet_code = parts[0] if len(parts) >= 1 else ''
  period_end = parts[1] if len(parts) >= 2 else ''
  doc_type = parts[2] if len(parts) >= 3 else ''
  return edinet_code, period_end, doc_type


def _infer_fiscal_quarter(end_month: int, fye_month: int) -> str:
  """Infer fiscal quarter from period end month and FYE month."""
  offset = (end_month - fye_month) % 12
  if offset == 0:
    return 'Q4'
  elif offset <= 3:
    return 'Q1'
  elif offset <= 6:
    return 'Q2'
  return 'Q3'


_JP_MONTH_MAP: dict[str, int] = {
    '1月': 1, '2月': 2, '3月': 3, '4月': 4,
    '5月': 5, '6月': 6, '7月': 7, '8月': 8,
    '9月': 9, '10月': 10, '11月': 11, '12月': 12,
}


def _parse_settlement_month(settlement: str) -> int:
  """Parse EDINET settlement date string to FYE month. Default: 3 (March)."""
  return _JP_MONTH_MAP.get(settlement, 3)
