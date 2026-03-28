"""
DART financial statement extractor.

Parses DART fnlttSinglAcntAll JSON into a standardized facts
DataFrame, mapping Korean account_nm to metric names using
metric_specs_kr.
"""

import json
from pathlib import Path
import re
from typing import Any, Optional

import pandas as pd

from data.silver.config.metric_specs_kr import METRIC_SPECS_KR


def _build_account_lookup() -> dict[tuple[str, str], str]:
  """Build (sj_div, account_nm) -> metric_name lookup."""
  lookup: dict[tuple[str, str], str] = {}
  for metric, spec in METRIC_SPECS_KR.items():
    sj_list: list[str] = spec['sj_div']  # type: ignore[assignment]
    name_list: list[str] = spec['account_names']  # type: ignore[assignment]
    for sj in sj_list:
      for name in name_list:
        lookup[(sj, name)] = metric
  return lookup


_ACCOUNT_LOOKUP = _build_account_lookup()


def _parse_amount(raw: Any) -> Optional[float]:
  """Parse Korean-format amount string (e.g. '1,234,567')."""
  if raw is None:
    return None
  s = str(raw).strip()
  if not s or s == '-':
    return None
  # Remove commas and spaces.
  s = re.sub(r'[,\s]', '', s)
  try:
    return float(s)
  except ValueError:
    return None


class DARTExtractor:
  """Extract facts from DART finstate JSON files."""

  def extract_facts(self, finstate_path: Path) -> pd.DataFrame:
    """Extract and map a single finstate JSON to facts rows."""
    data = json.loads(
        finstate_path.read_text(encoding='utf-8'))

    if data.get('status') != '000' or not data.get('list'):
      return pd.DataFrame()

    items = data['list']
    corp_code = _extract_corp_code(finstate_path)
    bsns_year = _extract_bsns_year(finstate_path)
    quarter = _extract_quarter(finstate_path)

    rows: list[dict[str, Any]] = []
    for item in items:
      sj_div = item.get('sj_div', '')
      account_nm = item.get('account_nm', '')
      val = _parse_amount(item.get('thstrm_amount'))

      if val is None:
        continue

      metric = _ACCOUNT_LOOKUP.get((sj_div, account_nm))

      rows.append({
          'corp_code': corp_code,
          'metric': metric,
          'sj_div': sj_div,
          'account_nm': account_nm,
          'val': val,
          'bsns_year': bsns_year or item.get('bsns_year'),
          'reprt_code': item.get('reprt_code'),
          'quarter': quarter,
      })

    df = pd.DataFrame(rows)
    if df.empty:
      return df

    df['val'] = pd.to_numeric(df['val'], errors='coerce')
    return df


def _extract_corp_code(path: Path) -> str:
  """Extract corp_code from filename like 00126380_2024_Q1.json."""
  name = path.stem
  parts = name.split('_')
  return parts[0] if parts else name


def _extract_bsns_year(path: Path) -> Optional[str]:
  """Extract bsns_year from filename like 00126380_2024_Q1.json."""
  name = path.stem
  parts = name.split('_')
  if len(parts) >= 2:
    return parts[1]
  return None


def _extract_quarter(path: Path) -> Optional[str]:
  """Extract quarter from filename like 00126380_2024_Q1.json."""
  name = path.stem
  parts = name.split('_')
  if len(parts) >= 3:
    return parts[2]
  return None
