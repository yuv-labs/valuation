"""
Screening panel builder.

Produces a wide panel with fundamental ratios for stock screening:
PE, PB, ROE, ROIC, FCF yield, margins, debt ratios, etc.

Unlike valuation/backtest panels (CFO-anchored, 3 metrics),
this panel uses all available metrics and computes derived ratios.
"""

import json
import logging
from pathlib import Path
import re
from typing import Optional

import pandas as pd

from data.gold.config.schemas import PanelSchema
from data.gold.core.base import BasePanelBuilder
from data.gold.transforms import calculate_market_cap
from data.gold.transforms import join_prices_pit

logger = logging.getLogger(__name__)


def _load_kr_shares(
    shares_dir: Path,
    corp_to_stock: dict[str, str],
) -> dict[str, float]:
  """Load shares outstanding from DART shares JSON files.

  Returns: {stock_code: shares_count}
  """
  result: dict[str, float] = {}
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
        # '보통주' row has common shares outstanding
        se = item.get('se', '')
        if se.strip() in ('\ubcf4\ud1b5\uc8fc', '보통주'):
          raw = item.get('istc_totqy', '')
          cleaned = re.sub(r'[,\s]', '', str(raw))
          if cleaned and cleaned != '-':
            result[stock_code] = float(cleaned)
            break
    except (json.JSONDecodeError, OSError, ValueError):
      continue
  return result

# Metrics we need for screening ratios.
_TTM_METRICS = [
    'REVENUE', 'NET_INCOME', 'EBIT', 'GROSS_PROFIT',
    'CFO', 'CAPEX',
]
_POINT_IN_TIME_METRICS = [
    'TOTAL_EQUITY', 'TOTAL_ASSETS', 'CURRENT_LIABILITIES',
    'TOTAL_DEBT', 'CASH', 'SHARES',
]
_ALL_METRICS = _TTM_METRICS + _POINT_IN_TIME_METRICS

# Schema is not strictly enforced here; we validate in tests.
_SCREENING_SCHEMA_NAME = 'screening_panel'


class ScreeningPanelBuilder(BasePanelBuilder):
  """
  Build screening panel with fundamental ratios.

  Primary key: (ticker, end) — latest filed version only.
  """

  REQUIRED_METRICS = _ALL_METRICS

  def __init__(
      self,
      silver_dir: Path,
      gold_dir: Path,
      min_date: Optional[str] = None,
      bronze_dir: Optional[Path] = None,
  ):
    schema = PanelSchema(
        name=_SCREENING_SCHEMA_NAME,
        description='Screening panel with fundamental ratios',
        columns=[],
        primary_key=['ticker', 'end'],
    )
    super().__init__(silver_dir, gold_dir, schema, min_date)
    self._bronze_dir = bronze_dir

  def build(self) -> pd.DataFrame:
    """Build screening panel (US + optionally KR)."""
    companies, facts, prices = self._load_data()

    # Append Korean data if bronze_dir has DART data.
    if self._bronze_dir is not None:
      kr_facts, kr_prices = self._load_kr_data(self._bronze_dir)
      if not kr_facts.empty:
        facts = pd.concat([facts, kr_facts], ignore_index=True)
        # Add KR companies to the ticker map.
        kr_companies = (
            kr_facts[['cik10']].drop_duplicates().copy())
        kr_companies['ticker'] = kr_companies['cik10']
        companies = pd.concat(
            [companies, kr_companies], ignore_index=True)
        logger.info('Added %d Korean facts rows', len(kr_facts))
      if not kr_prices.empty:
        prices = pd.concat([prices, kr_prices], ignore_index=True)

    # Build quarterly + TTM for all metrics.
    metrics_q = self._build_quarterly_metrics(facts)

    # For Korean annual-only data, TTM is missing because
    # there are no Q1-Q3 filings. Use q_val as ttm_val.
    if 'ttm_val' in metrics_q.columns:
      annual_mask = (
          metrics_q['ttm_val'].isna()
          & metrics_q['fiscal_quarter'].eq('Q4')
          & metrics_q['q_val'].notna())
      metrics_q.loc[annual_mask, 'ttm_val'] = (
          metrics_q.loc[annual_mask, 'q_val'])

    # Pivot to wide: one row per (cik10, end), latest filed.
    wide = self._pivot_to_wide(metrics_q)

    # Join with company tickers.
    wide = wide.merge(
        companies[['cik10', 'ticker']],
        on='cik10', how='left',
    )
    wide = wide.dropna(subset=['ticker'])

    # Adjust shares for stock splits before price join.
    from valuation.data_loader import \
        ValuationDataLoader  # pylint: disable=import-outside-toplevel
    wide = ValuationDataLoader._adjust_for_splits(wide)  # pylint: disable=protected-access

    # Join prices (PIT: first price after filed date).
    panel = join_prices_pit(wide, prices, ticker_col='ticker')
    panel = calculate_market_cap(
        panel, shares_col='shares_q', price_col='price')

    # For the latest period per ticker, override with the most
    # recent price so that screening PE/PB reflects current
    # market conditions (not the PIT price at filing date).
    panel = self._override_latest_price(panel, prices)

    panel = panel.drop(columns=['cik10'], errors='ignore')

    if self.min_date:
      panel = panel[panel['end'] >= self.min_date]

    # Compute derived ratios.
    panel = self._compute_ratios(panel)

    # Keep latest filed per (ticker, end).
    panel = panel.sort_values('filed')
    panel = panel.groupby(
        ['ticker', 'end'], as_index=False).tail(1)

    self.panel = panel.sort_values(
        ['ticker', 'end']).reset_index(drop=True)
    return self.panel

  def _build_wide_metrics(
      self, metrics_q: pd.DataFrame) -> pd.DataFrame:
    """Override: use our own pivot instead of CFO-anchored join."""
    return self._pivot_to_wide(metrics_q)

  @staticmethod
  def _override_latest_price(
      panel: pd.DataFrame,
      prices: pd.DataFrame,
  ) -> pd.DataFrame:
    """Replace price with most recent close for latest period."""
    if panel.empty or prices.empty:
      return panel

    panel = panel.copy()
    prices = prices.copy()
    prices['date'] = pd.to_datetime(prices['date'])

    # Normalize price ticker column.
    if 'symbol' in prices.columns:
      prices = prices.rename(columns={'symbol': 'ticker'})
    if 'ticker' in prices.columns:
      prices['ticker'] = (
          prices['ticker'].str.replace('.US', '', regex=False))

    # Get latest price per ticker.
    latest_prices = (
        prices.sort_values('date')
        .groupby('ticker', as_index=False)
        .tail(1)[['ticker', 'date', 'close']]
        .rename(columns={'close': 'latest_price',
                         'date': 'latest_date'}))

    # Identify latest period per ticker in panel.
    latest_end = (
        panel.groupby('ticker')['end']
        .max().reset_index()
        .rename(columns={'end': 'max_end'}))

    panel = panel.merge(latest_end, on='ticker', how='left')
    panel = panel.merge(latest_prices, on='ticker', how='left')

    is_latest = panel['end'] == panel['max_end']
    has_price = panel['latest_price'].notna()
    mask = is_latest & has_price

    panel.loc[mask, 'price'] = panel.loc[mask, 'latest_price']
    if 'shares_q' in panel.columns:
      panel.loc[mask, 'market_cap'] = (
          panel.loc[mask, 'latest_price']
          * panel.loc[mask, 'shares_q'])

    panel = panel.drop(
        columns=['max_end', 'latest_price', 'latest_date'],
        errors='ignore')
    return panel

  def _pivot_to_wide(
      self, metrics_q: pd.DataFrame) -> pd.DataFrame:
    """
    Pivot metrics_q to wide format.

    For each (cik10, end), take the latest filed version of each
    metric and spread into columns.
    """
    if metrics_q.empty:
      return pd.DataFrame()

    relevant = metrics_q[
        metrics_q['metric'].isin(_ALL_METRICS)].copy()

    if relevant.empty:
      return pd.DataFrame()

    # For each (cik10, metric, end), keep latest filed.
    relevant = relevant.sort_values('filed')
    latest = relevant.groupby(
        ['cik10', 'metric', 'end'], as_index=False).tail(1)

    # Build column mapping: metric -> column names.
    col_map = {}
    for metric in _TTM_METRICS:
      col_map[metric] = {
          'q_val': f'{metric.lower()}_q',
          'ttm_val': f'{metric.lower()}_ttm',
      }
    for metric in _POINT_IN_TIME_METRICS:
      col_map[metric] = {
          'q_val': f'{metric.lower()}_q',
      }
    # Special case: SHARES stays as shares_q.
    col_map['SHARES'] = {'q_val': 'shares_q'}

    # Pivot each metric separately, then merge on (cik10, end).
    # Note: we merge WITHOUT filed to avoid row fragmentation when
    # different metrics have different filed dates for the same end
    # (e.g. amended filings 10-K/A).
    merge_cols = ['cik10', 'end']
    fiscal_cols = ['fiscal_year', 'fiscal_quarter']

    parts: list[pd.DataFrame] = []
    for metric in _ALL_METRICS:
      mdf = latest[latest['metric'] == metric].copy()
      if mdf.empty:
        continue

      rename = col_map.get(metric, {})
      keep_cols = list(merge_cols)
      if not parts:
        keep_cols += fiscal_cols

      for src, dst in rename.items():
        if src in mdf.columns:
          mdf = mdf.rename(columns={src: dst})
          keep_cols.append(dst)

      avail = [c for c in keep_cols if c in mdf.columns]
      parts.append(mdf[avail])

    if not parts:
      return pd.DataFrame()

    result = parts[0]
    for part in parts[1:]:
      on = [c for c in merge_cols if c in part.columns]
      result = result.merge(part, on=on, how='outer')

    # Add filed as max(filed) per (cik10, end) from the latest
    # values we already filtered.
    filed_per_end = (
        latest.groupby(['cik10', 'end'])['filed']
        .max()
        .reset_index())
    result = result.merge(
        filed_per_end, on=['cik10', 'end'], how='left')

    return result

  @staticmethod
  def _compute_ratios(panel: pd.DataFrame) -> pd.DataFrame:
    """Compute derived financial ratios."""
    df = panel.copy()

    mcap = df.get('market_cap')
    ni = df.get('net_income_ttm')
    equity = df.get('total_equity_q')
    assets = df.get('total_assets_q')
    cur_liab = df.get('current_liabilities_q')
    cash = df.get('cash_q')
    ebit = df.get('ebit_ttm')
    revenue = df.get('revenue_ttm')
    gp = df.get('gross_profit_ttm')
    cfo = df.get('cfo_ttm')
    capex = df.get('capex_ttm')
    debt = df.get('total_debt_q')

    # PE ratio = market_cap / net_income_ttm
    if mcap is not None and ni is not None:
      df['pe_ratio'] = mcap / ni.replace(0, pd.NA)
    else:
      df['pe_ratio'] = pd.NA

    # PB ratio = market_cap / total_equity
    if mcap is not None and equity is not None:
      df['pb_ratio'] = mcap / equity.replace(0, pd.NA)
    else:
      df['pb_ratio'] = pd.NA

    # ROE = net_income_ttm / total_equity
    if ni is not None and equity is not None:
      df['roe'] = ni / equity.replace(0, pd.NA)
    else:
      df['roe'] = pd.NA

    # ROIC = EBIT * (1 - tax_rate) / invested_capital
    # Approximate tax_rate = 0.25
    if (ebit is not None and assets is not None
        and cur_liab is not None):
      cash_s = cash if cash is not None else pd.Series(0, index=df.index)
      invested = assets - cur_liab - cash_s
      nopat = ebit * 0.75
      df['roic'] = nopat / invested.replace(0, pd.NA)
    else:
      df['roic'] = pd.NA

    # Debt to equity
    if debt is not None and equity is not None:
      df['debt_to_equity'] = debt / equity.replace(0, pd.NA)
    else:
      df['debt_to_equity'] = pd.NA

    # FCF yield = (CFO - CAPEX) / market_cap
    if cfo is not None and capex is not None and mcap is not None:
      fcf = cfo - capex
      df['fcf_yield'] = fcf / mcap.replace(0, pd.NA)
    else:
      df['fcf_yield'] = pd.NA

    # Operating margin = EBIT / Revenue
    if ebit is not None and revenue is not None:
      df['op_margin'] = ebit / revenue.replace(0, pd.NA)
    else:
      df['op_margin'] = pd.NA

    # Gross profit margin = GP / Revenue
    if gp is not None and revenue is not None:
      df['gp_margin'] = gp / revenue.replace(0, pd.NA)
    else:
      df['gp_margin'] = pd.NA

    return df

  @staticmethod
  def _load_kr_data(
      bronze_dir: Path,
  ) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load Korean DART facts + KRX prices from Bronze."""
    from data.bronze.providers.dart import \
        _parse_corp_codes  # pylint: disable=import-outside-toplevel
    from data.silver.sources.dart.extractors import \
        DARTExtractor  # pylint: disable=import-outside-toplevel

    # Build corp_code -> stock_code mapping.
    corp_xml = bronze_dir / 'dart' / 'CORPCODE.xml'
    stock_to_corp: dict[str, str] = {}
    corp_to_stock: dict[str, str] = {}
    if corp_xml.exists():
      stock_to_corp = _parse_corp_codes(corp_xml)
      corp_to_stock = {v: k for k, v in stock_to_corp.items()}

    # -- DART facts --
    dart_dir = bronze_dir / 'dart' / 'finstate'
    facts_list: list[pd.DataFrame] = []
    if dart_dir.exists():
      extractor = DARTExtractor()
      for path in sorted(dart_dir.glob('*.json')):
        if path.name.endswith('.meta.json'):
          continue
        df = extractor.extract_facts(path)
        if not df.empty:
          mapped = df[df['metric'].notna()].copy()
          if not mapped.empty:
            mapped['cik10'] = mapped['corp_code'].map(
                corp_to_stock).fillna(mapped['corp_code'])
            mapped = mapped.rename(columns={
                'bsns_year': 'fy',
            })
            mapped['fiscal_year'] = pd.to_numeric(
                mapped['fy'], errors='coerce')

            # Quarter-aware end date and fiscal_quarter.
            qtr = mapped['quarter'].iloc[0] if (
                'quarter' in mapped.columns
                and mapped['quarter'].notna().any()
            ) else 'Q4'
            mapped['fiscal_quarter'] = qtr
            # fp must be 'FY' for Q4/annual so
            # YTDToQuarterlyConverter handles it.
            mapped['fp'] = 'FY' if qtr == 'Q4' else qtr

            qtr_month = {
                'Q1': '03-31', 'Q2': '06-30',
                'Q3': '09-30', 'Q4': '12-31',
            }
            mm_dd = qtr_month.get(qtr, '12-31')
            fy_strs = mapped['fy'].astype(str)
            end_str = fy_strs + f'-{mm_dd}'  # type: ignore[operator]
            mapped['end'] = pd.to_datetime(end_str)

            # Approximate filed date: Q-end + 45 days
            # (annual + 90 days).
            filed_lag = 90 if qtr == 'Q4' else 45
            mapped['filed'] = (
                mapped['end']
                + pd.Timedelta(days=filed_lag))

            facts_list.append(mapped)

    facts = (pd.concat(facts_list, ignore_index=True)
             if facts_list else pd.DataFrame())

    # -- DART shares outstanding --
    shares_dir = bronze_dir / 'dart' / 'shares'
    if shares_dir.exists() and not facts.empty:
      shares_map = _load_kr_shares(shares_dir, corp_to_stock)
      if shares_map:
        shares_rows: list[dict] = []  # type: ignore[type-arg]
        for stock_code, shares_val in shares_map.items():
          # Add SHARES as a fact for each end date
          ends = facts[facts['cik10'] == stock_code][
              'end'].unique()
          for end in ends:
            shares_rows.append({
                'cik10': stock_code,
                'metric': 'SHARES',
                'val': shares_val,
                'end': end,
                'filed': end + pd.Timedelta(days=90),
                'fp': 'FY',
                'fiscal_year': end.year,
                'fiscal_quarter': 'Q4',
                'fy': str(end.year),
            })
        if shares_rows:
          shares_df = pd.DataFrame(shares_rows)
          facts = pd.concat(
              [facts, shares_df], ignore_index=True)

    # -- KRX prices --
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
