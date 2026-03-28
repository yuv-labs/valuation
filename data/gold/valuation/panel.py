"""Valuation panel builder — latest version for current DCF.

Supports both US (SEC) and Korean (DART) data.
"""

import logging
from pathlib import Path
from typing import Optional

import pandas as pd

from data.gold.config.schemas import VALUATION_PANEL_SCHEMA
from data.gold.core.base import BasePanelBuilder
from data.gold.transforms import calculate_market_cap
from data.gold.transforms import join_prices_pit

logger = logging.getLogger(__name__)


class ValuationPanelBuilder(BasePanelBuilder):
  """
  Builds valuation panel with latest filed version only.

  Primary key: (ticker, end)
  """

  REQUIRED_METRICS = ['CFO', 'CAPEX', 'SHARES']

  def __init__(
      self,
      silver_dir: Path,
      gold_dir: Path,
      min_date: Optional[str] = None,
      bronze_dir: Optional[Path] = None,
  ):
    super().__init__(
        silver_dir, gold_dir, VALUATION_PANEL_SCHEMA, min_date)
    self._bronze_dir = bronze_dir

  def build(self) -> pd.DataFrame:
    """Build valuation panel with latest version per period."""
    companies, facts, prices = self._load_data()

    # Append Korean data if available.
    if self._bronze_dir is not None:
      kr_facts, kr_prices = self._load_kr_valuation_data(
          self._bronze_dir)
      if not kr_facts.empty:
        facts = pd.concat([facts, kr_facts], ignore_index=True)
        kr_companies = (
            kr_facts[['cik10']].drop_duplicates().copy())
        kr_companies['ticker'] = kr_companies['cik10']
        companies = pd.concat(
            [companies, kr_companies], ignore_index=True)
        logger.info(
            'Added %d Korean facts rows', len(kr_facts))
      if not kr_prices.empty:
        prices = pd.concat(
            [prices, kr_prices], ignore_index=True)

    metrics_q = self._build_quarterly_metrics(facts)
    metrics_wide = self._build_wide_metrics(metrics_q)

    # Keep only latest filed version per (cik10, end)
    metrics_wide = metrics_wide.sort_values('filed')
    metrics_wide = metrics_wide.groupby(
        ['cik10', 'end'], as_index=False).tail(1)

    metrics_wide = metrics_wide.merge(
        companies[['cik10', 'ticker']],
        on='cik10',
        how='left',
    )
    metrics_wide = metrics_wide.dropna(subset=['ticker'])

    panel = join_prices_pit(
        metrics_wide, prices, ticker_col='ticker')
    panel = calculate_market_cap(panel)
    panel = panel.drop(columns=['cik10'], errors='ignore')

    if self.min_date:
      panel = panel[panel['end'] >= self.min_date]

    self.panel = panel.sort_values(
        ['ticker', 'end']).reset_index(drop=True)
    return self.panel

  @staticmethod
  def _load_kr_valuation_data(
      bronze_dir: Path,
  ) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load Korean DART data for valuation (CFO, CAPEX, SHARES).

    DART thstrm_amount is already per-quarter (not YTD), so
    we mark all metrics as is_ytd=False to skip YTD->Q
    conversion in build_quarterly_metrics.
    """
    from data.bronze.providers.dart import \
        _parse_corp_codes  # pylint: disable=import-outside-toplevel
    from data.silver.sources.dart.extractors import \
        DARTExtractor  # pylint: disable=import-outside-toplevel

    # Corp code mapping.
    corp_xml = bronze_dir / 'dart' / 'CORPCODE.xml'
    corp_to_stock: dict[str, str] = {}
    if corp_xml.exists():
      stock_to_corp = _parse_corp_codes(corp_xml)
      corp_to_stock = {v: k for k, v in stock_to_corp.items()}

    # Extract DART facts.
    dart_dir = bronze_dir / 'dart' / 'finstate'
    facts_list: list[pd.DataFrame] = []
    if dart_dir.exists():
      extractor = DARTExtractor()
      for path in sorted(dart_dir.glob('*.json')):
        if path.name.endswith('.meta.json'):
          continue
        df = extractor.extract_facts(path)
        if df.empty:
          continue
        mapped = df[df['metric'].isin(
            ['CFO', 'CAPEX', 'SHARES'])].copy()
        if mapped.empty:
          continue

        mapped['cik10'] = mapped['corp_code'].map(
            corp_to_stock).fillna(mapped['corp_code'])
        mapped = mapped.rename(columns={'bsns_year': 'fy'})
        mapped['fiscal_year'] = pd.to_numeric(
            mapped['fy'], errors='coerce')

        # Quarter handling.
        qtr = mapped['quarter'].iloc[0] if (
            'quarter' in mapped.columns
            and mapped['quarter'].notna().any()
        ) else 'Q4'
        mapped['fiscal_quarter'] = qtr
        mapped['fp'] = 'FY' if qtr == 'Q4' else qtr

        # tag column (required by aggregation.py).
        mapped['tag'] = mapped['account_nm']

        # End date by quarter.
        qtr_month = {
            'Q1': '03-31', 'Q2': '06-30',
            'Q3': '09-30', 'Q4': '12-31',
        }
        mm_dd = qtr_month.get(qtr, '12-31')
        fy_strs = mapped['fy'].astype(str)
        end_str = fy_strs + f'-{mm_dd}'  # type: ignore[operator]
        mapped['end'] = pd.to_datetime(end_str)

        filed_lag = 90 if qtr == 'Q4' else 45
        mapped['filed'] = (
            mapped['end'] + pd.Timedelta(days=filed_lag))

        facts_list.append(mapped)

    facts = (pd.concat(facts_list, ignore_index=True)
             if facts_list else pd.DataFrame())

    # For non-Q4 data, DART gives per-quarter values (not YTD).
    # We must NOT apply YTD->Q conversion. Mark CFO/CAPEX as
    # non-YTD by setting fp to the quarter (not 'FY').
    # For Q4 (annual), fp='FY' triggers YTD->Q but since there's
    # no Q3 YTD to subtract, it uses the value as-is.

    # Load shares from DART shares API and forward-fill
    # across all quarters.
    shares_dir = bronze_dir / 'dart' / 'shares'
    if shares_dir.exists() and not facts.empty:
      from data.gold.screening.panel import \
          _load_kr_shares  # pylint: disable=import-outside-toplevel
      shares_map = _load_kr_shares(shares_dir, corp_to_stock)
      if shares_map:
        shares_rows: list[dict] = []  # type: ignore[type-arg]
        for stock_code, shares_val in shares_map.items():
          # Get all (end, fiscal_quarter) combos for this stock.
          stock_facts = facts[facts['cik10'] == stock_code]
          end_qtrs = stock_facts[
              ['end', 'fiscal_quarter']].drop_duplicates()
          for _, row in end_qtrs.iterrows():
            fq = row['fiscal_quarter']
            end = row['end']
            shares_rows.append({
                'cik10': stock_code,
                'metric': 'SHARES',
                'val': shares_val,
                'end': end,
                'filed': end + pd.Timedelta(days=45),
                'fp': fq,
                'fiscal_year': end.year,
                'fiscal_quarter': fq,
                'fy': str(end.year),
                'tag': 'shares',
            })
        if shares_rows:
          facts = pd.concat(
              [facts, pd.DataFrame(shares_rows)],
              ignore_index=True)

    # KRX prices.
    krx_dir = bronze_dir / 'krx' / 'daily'
    price_list: list[pd.DataFrame] = []
    if krx_dir.exists():
      for csv_path in sorted(krx_dir.glob('*.csv')):
        try:
          pdf = pd.read_csv(csv_path, encoding='utf-8')
          ticker = csv_path.stem
          date_col = pdf.columns[0]
          close_col = [c for c in pdf.columns
                       if 'close' in c.lower()
                       or '\uc885\uac00' in c]
          if not close_col:
            continue
          out = pd.DataFrame({
              'date': pd.to_datetime(pdf[date_col]),
              'symbol': ticker,
              'close': pd.to_numeric(
                  pdf[close_col[0]], errors='coerce'),
          })
          price_list.append(out)
        except Exception:  # pylint: disable=broad-except
          continue

    prices = (pd.concat(price_list, ignore_index=True)
              if price_list else pd.DataFrame())

    return facts, prices
