"""Screening report output — table and HTML."""

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from tabulate import tabulate  # type: ignore[import-untyped]

# (column_key, short_label, format, tooltip)
# format: 'pct' = percentage, 'num' = number, 'str' = string
_ALL_COLS = [
    ('market', 'Mkt', 'str', ''),
    ('ticker', 'Ticker', 'str', ''),
    ('name', 'Company', 'name', ''),
    ('pe_ratio', 'PE', 'num',
     'PE Ratio = 시가총액 / 순이익(TTM)'),
    ('roic_3y_avg', 'ROIC 3Y', 'pct',
     'ROIC 3년 평균. Tier 1 기준: > 10%'),
    ('roic_3y_min', 'ROIC Min', 'pct',
     'ROIC 3년 최솟값. Tier 1 기준: > 7%. 나쁜 해에도 자본비용 이상'),
    ('fcf_ni_ratio_3y_avg', 'FCF/NI 3Y', 'pct',
     'FCF/순이익 3년 평균. Tier 1 기준: > 0.8. 이익의 질(오너 어닝)'),
    ('gp_margin', 'GPM', 'pct',
     '매출총이익률. Tier 2 기준: > 30%. 가격결정력 증거'),
    ('gp_margin_std_3y', 'GPM Std', 'pct',
     '매출총이익률 3년 표준편차. Tier 2 기준: < 5%. 마진 안정성'),
    ('debt_to_equity', 'D/E', 'num',
     '부채비율 = 총부채/자기자본. Tier 2 기준: < 1.0'),
    ('fcf_yield', 'FCF Yld', 'pct',
     'FCF 수익률 = (영업CF − Capex) / 시가총액. Track B 기준: > 5%'),
    ('revenue_cagr_3y', 'Rev CAGR', 'pct',
     '매출 3년 CAGR. 참고 지표 (필터/스코어 미반영)'),
    ('moat_score', 'Moat', 'num',
     '해자 점수 (0-100). ROIC, FCF/NI, GPM, D/E 기반'),
    ('fear_score', 'Fear', 'num',
     '공포 점수 (0-100). 52주 고가 대비 하락률, PE vs 5Y 평균, FCF yield'),
    ('opportunity_score', 'Opp', 'num',
     '기회 점수 (0-100). 70% 공포(가격 매력도) + 30% 해자'),
]


def _visible_cols(df: pd.DataFrame) -> list[tuple]:
  """Return only columns that exist in the DataFrame."""
  return [c for c in _ALL_COLS if c[0] in df.columns]


def _format_val(val: Any, fmt: str) -> str:
  if fmt == 'pct':
    try:
      if val is None or pd.isna(val):
        return '-'
      return f'{float(val) * 100:.1f}%'
    except (TypeError, ValueError):
      return '-'
  if fmt == 'num':
    try:
      if val is None or pd.isna(val):
        return '-'
      return f'{float(val):.1f}'
    except (TypeError, ValueError):
      return '-'
  if fmt == 'name':
    return str(val)[:25] if val else '-'
  return str(val) if val else '-'


def print_table(df: pd.DataFrame) -> None:
  """Print screening results as a console table."""
  cols = _visible_cols(df)
  rows = []
  for _, r in df.iterrows():
    rows.append([_format_val(r.get(key), fmt)
                 for key, _, fmt, _ in cols])

  headers = [label for _, label, _, _ in cols]
  sep = '=' * 70
  print(f'\n{sep}')
  print(f'  Screening Results — {len(df)} stocks')
  print(f'{sep}')
  print(tabulate(rows, headers=headers,
                 tablefmt='simple', stralign='right'))


# pylint: disable=too-many-locals
def generate_html(df: pd.DataFrame, path: Path) -> None:
  """Generate interactive HTML screening report."""
  today = datetime.now().strftime('%Y-%m-%d')
  us_n = len(df[df['market'] == 'US'])
  kr_n = len(df[df['market'] == 'KR'])

  cols = _visible_cols(df)

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
  th[title] { cursor: help; text-decoration: underline dotted rgba(255,255,255,0.5);
              text-underline-offset: 3px; }
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
  .section { background: #f5f5f5; }
  .section td { font-weight: 700; padding: 10px; font-size: 0.95em; }
  '''

  html = (
      f'<!DOCTYPE html>\n<html><head><meta charset="utf-8">\n'
      f'<title>Screening {today}</title>\n'
      f'<style>{css}</style>\n'
      f'</head><body>\n'
      f'<h1>Equity Screening</h1>\n'
      f'<p class="meta">{today} | {len(df)} stocks '
      f'(US {us_n}, KR {kr_n})</p>\n'
      f'<table><thead><tr>')

  for _, label, _, tooltip in cols:
    if tooltip:
      html += f'<th title="{tooltip}">{label}</th>'
    else:
      html += f'<th>{label}</th>'
  html += '</tr></thead><tbody>'

  ncols = len(cols)
  prev_mkt = None
  for _, r in df.iterrows():
    mkt = r.get('market', '')
    if mkt != prev_mkt:
      section = ('Korea (KOSPI)' if mkt == 'KR'
                 else 'United States')
      html += (
          f'<tr class="section">'
          f'<td colspan="{ncols}">{section}</td></tr>')
      prev_mkt = mkt

    cls = 'kr' if mkt == 'KR' else ''
    html += f'<tr class="{cls}">'

    for key, _, fmt, _ in cols:
      val = r.get(key)
      if key == 'market':
        tag_cls = f'tag-{mkt.lower()}'
        html += (
            f'<td><span class="tag {tag_cls}">'
            f'{mkt}</span></td>')
      elif key == 'ticker':
        html += f'<td><b>{val}</b></td>'
      elif key == 'name':
        html += f'<td>{str(val)[:30]}</td>'
      else:
        html += f'<td>{_format_val(val, fmt)}</td>'

    html += '</tr>'

  html += '</tbody></table></body></html>'
  Path(path).write_text(html, encoding='utf-8')
