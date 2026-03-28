"""Screening report output — table and HTML."""

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from tabulate import tabulate  # type: ignore[import-untyped]

_TABLE_COLS = [
    ('market', 'Mkt'),
    ('ticker', 'Ticker'),
    ('name', 'Company'),
    ('pe_ratio', 'PE'),
    ('pb_ratio', 'PB'),
    ('roe', 'ROE'),
    ('roe_3y_avg', '3Y Avg'),
    ('roic', 'ROIC'),
    ('roic_3y_avg', '3Y Avg'),
    ('fcf_yield', 'FCF Yld'),
    ('op_margin', 'OpMgn'),
    ('debt_to_equity', 'D/E'),
    ('opportunity_score', 'Opp'),
]


def _fp(val: Any) -> str:
  if val is None or (isinstance(val, float) and pd.isna(val)):
    return '-'
  return f'{float(val) * 100:.1f}%'


def _fn(val: Any) -> str:
  if val is None or (isinstance(val, float) and pd.isna(val)):
    return '-'
  return f'{float(val):.1f}'


def print_table(df: pd.DataFrame) -> None:
  """Print screening results as a console table."""
  rows = []
  for _, r in df.iterrows():
    row = []
    for col, _ in _TABLE_COLS:
      v = r.get(col)
      if col in ('roe', 'roe_3y_avg', 'roic', 'roic_3y_avg',
                  'fcf_yield', 'op_margin'):
        row.append(_fp(v))
      elif col in ('pe_ratio', 'pb_ratio', 'debt_to_equity',
                    'opportunity_score'):
        row.append(_fn(v))
      elif col == 'name':
        row.append(str(v)[:25] if v else '-')
      else:
        row.append(str(v) if v else '-')
    rows.append(row)

  headers = [h for _, h in _TABLE_COLS]
  sep = '=' * 70
  print(f'\n{sep}')
  print(f'  Screening Results — {len(df)} stocks')
  print(f'{sep}')
  print(tabulate(rows, headers=headers,
                 tablefmt='simple', stralign='right'))


def _badge(roe_c: Any, roic_c: Any) -> str:
  rc = bool(roe_c) if roe_c is not None and roe_c is not pd.NA else False
  ic = bool(roic_c) if roic_c is not None and roic_c is not pd.NA else False
  if rc and ic:
    return '<span class="badge both">Both</span>'
  if rc:
    return '<span class="badge partial">ROE</span>'
  if ic:
    return '<span class="badge partial">ROIC</span>'
  return '<span class="badge none">-</span>'


# pylint: disable=too-many-locals
def generate_html(df: pd.DataFrame, path: Path) -> None:
  """Generate interactive HTML screening report."""
  today = datetime.now().strftime('%Y-%m-%d')
  us_n = len(df[df['market'] == 'US'])
  kr_n = len(df[df['market'] == 'KR'])

  css = '''
  * { box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, sans-serif;
         margin: 0; padding: 2rem; background: #f8f9fa; color: #1a1a2e; }
  h1 { margin-bottom: 0.2rem; }
  .meta { color: #666; margin-bottom: 1.5rem; font-size: 0.9em; }
  table { border-collapse: collapse; width: 100%; background: white;
          box-shadow: 0 1px 4px rgba(0,0,0,0.08); border-radius: 8px;
          overflow: hidden; font-size: 0.85em; }
  th { background: #1a1a2e; color: white; padding: 8px 10px;
       text-align: right; white-space: nowrap; position: sticky; top: 0; }
  th:nth-child(-n+3) { text-align: left; }
  td { padding: 6px 10px; border-bottom: 1px solid #f0f0f0;
       text-align: right; white-space: nowrap; }
  td:nth-child(-n+3) { text-align: left; }
  td:nth-child(3) { font-size: 0.85em; color: #555; max-width: 200px;
                     overflow: hidden; text-overflow: ellipsis; }
  tr:hover { background: #f0f4ff; }
  tr.kr { background: #fffbf5; }
  tr.kr:hover { background: #fff0e0; }
  .tag { display: inline-block; padding: 2px 6px; border-radius: 4px;
         font-size: 0.75em; font-weight: 600; }
  .tag-us { background: #e3f2fd; color: #1565c0; }
  .tag-kr { background: #fff3e0; color: #e65100; }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 10px;
           font-size: 0.8em; font-weight: 500; }
  .both { background: #e8f5e9; color: #2e7d32; }
  .partial { background: #fff8e1; color: #f57f17; }
  .none { background: #f5f5f5; color: #999; }
  .section { background: #f5f5f5; }
  .section td { font-weight: 700; padding: 10px; font-size: 0.95em; }
  '''

  header_cols = [
      'Mkt', 'Ticker', 'Company', 'PE', 'PB',
      'ROE', '3Y Avg', '3Y Min',
      'ROIC', '3Y Avg', '3Y Min',
      'FCF Yld', 'OpMgn', 'D/E', 'Opp', 'Consistent?',
  ]

  html = (
      f'<!DOCTYPE html>\n<html><head><meta charset="utf-8">\n'
      f'<title>Screening {today}</title>\n'
      f'<style>{css}</style>\n'
      f'</head><body>\n'
      f'<h1>Equity Screening</h1>\n'
      f'<p class="meta">{today} | {len(df)} stocks '
      f'(US {us_n}, KR {kr_n})</p>\n'
      f'<table><thead><tr>')

  for col in header_cols:
    html += f'<th>{col}</th>'
  html += '</tr></thead><tbody>'

  prev_mkt = None
  ncols = len(header_cols)
  for _, r in df.iterrows():
    mkt = r.get('market', '')
    if mkt != prev_mkt:
      label = ('Korea (KOSPI)' if mkt == 'KR'
               else 'United States')
      html += (
          f'<tr class="section">'
          f'<td colspan="{ncols}">{label}</td></tr>')
      prev_mkt = mkt

    cls = 'kr' if mkt == 'KR' else ''
    tag_cls = f'tag-{mkt.lower()}'
    tag = f'<span class="tag {tag_cls}">{mkt}</span>'
    name = str(r.get('name', ''))[:30]
    ticker = r['ticker']

    roe_c = r.get('roe_3y_consistent')
    roic_c = r.get('roic_3y_consistent')

    html += f'<tr class="{cls}">'
    html += f'<td>{tag}</td>'
    html += f'<td><b>{ticker}</b></td>'
    html += f'<td>{name}</td>'
    vals = [
        _fn(r.get('pe_ratio')), _fn(r.get('pb_ratio')),
        _fp(r.get('roe')), _fp(r.get('roe_3y_avg')),
        _fp(r.get('roe_3y_min')),
        _fp(r.get('roic')), _fp(r.get('roic_3y_avg')),
        _fp(r.get('roic_3y_min')),
        _fp(r.get('fcf_yield')), _fp(r.get('op_margin')),
        _fn(r.get('debt_to_equity')),
        _fn(r.get('opportunity_score')),
        _badge(roe_c, roic_c),
    ]
    for v in vals:
      html += f'<td>{v}</td>'
    html += '</tr>'

  html += '</tbody></table></body></html>'
  Path(path).write_text(html, encoding='utf-8')
