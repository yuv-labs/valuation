"""Screening report output — table and HTML."""

from datetime import datetime
from html import escape as html_escape
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
    ('track_signal', 'Track', 'track', 'Track 분류: buffett / fisher / mixed'),
    ('fisher_quant_score', 'Fisher', 'score',
     'Fisher 정량 점수 (0-22). 매출 CAGR, R&D, OPM, 마진 추세, CFO/NI'),
    ('buffett_quant_score', 'Buffett', 'score',
     'Buffett 정량 점수 (0-22). FCF yield, FCF 일관, buyback, ROIC, D/A'),
    ('trust_score', 'Trust', 'num',
     '1분 신뢰성 테스트 (0-4). ROE, ROA, CFO/NI, 배당'),
    ('roic', 'ROIC', 'pct', 'ROIC = NOPAT / 투하자본'),
    ('roic_5y_avg', 'ROIC 5Y', 'pct', 'ROIC 5년 평균'),
    ('roic_trend', 'Trend', 'trend', 'ROIC 5년 추세: rising / stable / declining'),
    ('revenue_cagr_5y', 'Rev 5Y', 'pct', '매출 5년 CAGR'),
    ('op_margin', 'OPM', 'pct', '영업이익률'),
    ('fcf_yield', 'FCF Yld', 'pct',
     'FCF 수익률 = (영업CF − Capex) / 시가총액'),
    ('debt_to_assets', 'D/A', 'pct', '부채/자산 비율'),
    ('rd_to_revenue', 'R&D', 'pct', 'R&D / 매출'),
    ('reinvestment_rate', 'Reinvest', 'pct',
     '재투자율 = (Capex + R&D) / CFO'),
    ('pe_ratio', 'PE', 'num', 'PE Ratio = 시가총액 / 순이익(TTM)'),
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
  if fmt == 'score':
    try:
      if val is None or pd.isna(val):
        return '-'
      return f'{int(val)}'
    except (TypeError, ValueError):
      return '-'
  if fmt == 'name':
    return str(val)[:25] if val else '-'
  if fmt in ('track', 'trend'):
    return str(val) if val and not pd.isna(val) else '-'
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
  us_n = len(df[df.get('market', pd.Series()) == 'US'])
  kr_n = len(df[df.get('market', pd.Series()) == 'KR'])

  cols = _visible_cols(df)

  track_counts = {}
  if 'track_signal' in df.columns:
    track_counts = df['track_signal'].value_counts().to_dict()
  n_fisher = track_counts.get('fisher', 0)
  n_buffett = track_counts.get('buffett', 0)
  n_mixed = track_counts.get('mixed', 0)

  css = '''
  :root {
    --bg: #0d1117; --surface: #161b22; --border: #30363d;
    --text: #e6edf3; --dim: #8b949e; --accent: #58a6ff;
    --fisher: #3fb950; --buffett: #d29922; --mixed: #8b949e;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, sans-serif;
         background: var(--bg); color: var(--text); padding: 24px; }
  h1 { font-size: 1.4rem; margin-bottom: 4px; }
  .meta { color: var(--dim); margin-bottom: 20px; font-size: 0.85em; }
  .controls { display: flex; gap: 10px; margin-bottom: 16px;
              flex-wrap: wrap; align-items: center; }
  .btn { padding: 5px 14px; border-radius: 14px; border: 1px solid var(--border);
         background: transparent; color: var(--dim); cursor: pointer;
         font-size: 0.78rem; }
  .btn:hover { border-color: var(--accent); color: var(--text); }
  .btn.on { border-color: var(--accent); color: var(--accent);
            background: rgba(88,166,255,0.1); }
  .btn.on.fisher { border-color: var(--fisher); color: var(--fisher);
                   background: rgba(63,185,80,0.1); }
  .btn.on.buffett { border-color: var(--buffett); color: var(--buffett);
                    background: rgba(210,153,34,0.1); }
  input[type=text] { background: var(--surface); border: 1px solid var(--border);
         color: var(--text); padding: 5px 10px; border-radius: 6px;
         font-size: 0.8rem; width: 160px; }
  .wrap { overflow: auto; max-height: 78vh; border: 1px solid var(--border);
          border-radius: 8px; }
  table { border-collapse: collapse; width: 100%; font-size: 0.8rem; }
  th { position: sticky; top: 0; background: var(--surface);
       border-bottom: 2px solid var(--border); padding: 7px 9px;
       text-align: right; color: var(--dim); font-weight: 600;
       white-space: nowrap; cursor: pointer; user-select: none; }
  th:hover { color: var(--accent); }
  th.asc::after { content: ' ▲'; color: var(--accent); }
  th.desc::after { content: ' ▼'; color: var(--accent); }
  th:nth-child(-n+4) { text-align: left; }
  td { padding: 5px 9px; border-bottom: 1px solid var(--border);
       text-align: right; white-space: nowrap; }
  td:nth-child(-n+4) { text-align: left; }
  tr:hover { background: rgba(88,166,255,0.04); }
  .tag { padding: 2px 7px; border-radius: 10px; font-size: 0.68rem;
         font-weight: 600; text-transform: uppercase; }
  .tag-fisher { background: rgba(63,185,80,0.15); color: var(--fisher); }
  .tag-buffett { background: rgba(210,153,34,0.15); color: var(--buffett); }
  .tag-mixed { background: rgba(139,148,158,0.15); color: var(--mixed); }
  .tag-us { background: rgba(88,166,255,0.12); color: var(--accent); }
  .tag-kr { background: rgba(210,153,34,0.12); color: var(--buffett); }
  .tag-jp { background: rgba(63,185,80,0.12); color: var(--fisher); }
  .trend-rising { color: var(--fisher); }
  .trend-declining { color: #da3633; }
  .trend-stable { color: var(--dim); }
  .bar { display: inline-block; height: 5px; border-radius: 3px;
         vertical-align: middle; margin-right: 4px; }
  .cnt { color: var(--dim); font-size: 0.8rem; margin-bottom: 6px; }
  .pos { color: var(--fisher); }
  .neg { color: #da3633; }
  '''

  html = (
      f'<!DOCTYPE html>\n<html><head><meta charset="utf-8">\n'
      f'<title>Screening {today}</title>\n'
      f'<style>{css}</style>\n'
      f'</head><body>\n'
      f'<h1>Equity Screening</h1>\n'
      f'<p class="meta">{today} | {len(df)} stocks '
      f'(US {us_n}, KR {kr_n})'
      f' | Fisher {n_fisher}'
      f' \u00b7 Buffett {n_buffett}'
      f' \u00b7 Mixed {n_mixed}</p>\n'
      f'<div class="controls">'
      f'<button class="btn on" onclick="filt(\'all\',this)">All</button>'
      f'<button class="btn fisher"'
      f' onclick="filt(\'fisher\',this)">Fisher</button>'
      f'<button class="btn buffett"'
      f' onclick="filt(\'buffett\',this)">Buffett</button>'
      f'<button class="btn"'
      f' onclick="filt(\'mixed\',this)">Mixed</button>'
      f'<input type="text" id="q" placeholder="Search ticker..."'
      f' oninput="search()">'
      f'</div>\n'
      f'<div class="cnt" id="cnt"></div>\n'
      f'<div class="wrap">\n'
      f'<table><thead><tr>')

  for i, (key, label, _, tooltip) in enumerate(cols):
    tt = f' title="{tooltip}"' if tooltip else ''
    html += f'<th data-i="{i}" data-k="{key}"{tt}>{label}</th>'
  html += '</tr></thead><tbody id="tb">'

  for _, r in df.iterrows():
    mkt = str(r.get('market', ''))
    track = str(r.get('track_signal', ''))
    ticker = str(r.get('ticker', ''))
    html += (
        f'<tr data-t="{track}" data-tk="{html_escape(ticker)}">')

    for key, _, fmt, _ in cols:
      val = r.get(key)
      if key == 'market':
        tag_cls = f'tag-{mkt.lower()}'
        html += (
            f'<td><span class="tag {tag_cls}">'
            f'{mkt}</span></td>')
      elif key == 'ticker':
        html += f'<td><b>{html_escape(ticker)}</b></td>'
      elif key == 'name':
        html += (
            f'<td>{html_escape(str(val)[:28])}</td>')
      elif key == 'track_signal':
        tag_cls = f'tag-{track}'
        html += (
            f'<td><span class="tag {tag_cls}">'
            f'{track}</span></td>')
      elif fmt == 'score':
        sv = int(val) if val and not pd.isna(val) else 0
        pct_w = sv / 22 * 100
        color = ('var(--fisher)' if 'fisher' in key
                 else 'var(--buffett)')
        html += (
            f'<td><span class="bar"'
            f' style="width:{pct_w}%;background:{color}">'
            f'</span>{sv}</td>')
      elif key == 'roic_trend':
        trend = str(val) if val and not pd.isna(val) else '-'
        cls = f'trend-{trend}' if trend != '-' else ''
        html += f'<td class="{cls}">{trend}</td>'
      elif fmt == 'pct':
        fv = _format_val(val, fmt)
        try:
          cls = ''
          if val is not None and not pd.isna(val):
            if key in ('debt_to_assets',) and float(val) > 0.5:
              cls = 'neg'
            elif float(val) > 0:
              cls = 'pos'
            elif float(val) < 0:
              cls = 'neg'
          html += f'<td class="{cls}">{fv}</td>'
        except (TypeError, ValueError):
          html += f'<td>{fv}</td>'
      else:
        html += f'<td>{_format_val(val, fmt)}</td>'

    html += '</tr>'

  js = '''
  let curTrack='all';
  function filt(t,el){
    curTrack=t;
    document.querySelectorAll('.btn').forEach(b=>b.classList.remove('on'));
    el.classList.add('on');
    applyFilters();
  }
  function search(){applyFilters();}
  function applyFilters(){
    const q=document.getElementById('q').value.toUpperCase();
    let n=0;
    document.querySelectorAll('#tb tr').forEach(r=>{
      const t=r.dataset.t, tk=r.dataset.tk;
      const show=(curTrack==='all'||t===curTrack)&&(!q||tk.includes(q));
      r.style.display=show?'':'none';
      if(show)n++;
    });
    document.getElementById('cnt').textContent=n+' tickers';
  }
  // Column sort
  let sortK='',sortD='desc';
  document.querySelectorAll('th[data-k]').forEach(th=>{
    th.addEventListener('click',()=>{
      const k=th.dataset.k;
      if(sortK===k){sortD=sortD==='desc'?'asc':'desc';}
      else{sortK=k;sortD='desc';}
      document.querySelectorAll('th').forEach(
        t=>{t.classList.remove('asc','desc');});
      th.classList.add(sortD);
      const tb=document.getElementById('tb');
      const rows=[...tb.querySelectorAll('tr')];
      const i=parseInt(th.dataset.i);
      rows.sort((a,b)=>{
        let va=a.children[i].textContent.replace(/[%$,]/g,'');
        let vb=b.children[i].textContent.replace(/[%$,]/g,'');
        const na=parseFloat(va),nb=parseFloat(vb);
        if(!isNaN(na)&&!isNaN(nb))
          return sortD==='desc'?nb-na:na-nb;
        return sortD==='desc'?
          vb.localeCompare(va):va.localeCompare(vb);
      });
      rows.forEach(r=>tb.appendChild(r));
    });
  });
  applyFilters();
  '''

  html += (
      f'</tbody></table></div>\n'
      f'<script>{js}</script>\n'
      f'</body></html>')
  Path(path).write_text(html, encoding='utf-8')
