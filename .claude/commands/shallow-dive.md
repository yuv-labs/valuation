---
description: Run Shallow Dive analysis for given tickers (--us/--kr/--jp)
allowed-tools: Bash, Read, Write, Glob, Grep, WebSearch, WebFetch, Agent
---

# Shallow Dive

You are running a Shallow Dive analysis. Parse `$ARGUMENTS` and execute the full pipeline.

## 1. Parse arguments

Arguments: `$ARGUMENTS`

Parse `--us`, `--kr`, `--jp` flags. Each flag is followed by one or more tickers for that market. Example:

- `--us AAPL MSFT` → US tickers: AAPL, MSFT
- `--kr 098460` → KR ticker: 098460
- `--jp 7203` → JP ticker: 7203
- `--us AAPL --kr 098460` → US: AAPL, KR: 098460

A flag applies to all tickers until the next flag. At least one flag + ticker is required. If no flags found, ask the user which market.

Count total tickers across all markets. 1 = single mode, 2+ = batch mode.

## 2. Phase 0: Data build

Activate venv and run the data pipeline. All commands use `source venv/bin/activate && ...`.

**For each market that has tickers, run bronze in order:**

US tickers:

```bash
source venv/bin/activate && python3.13 -m data.bronze.update --tickers {TICKERS} --sec-user-agent "yuv valuation research (yuv@yuv.kr)"
```

KR tickers:

```bash
source venv/bin/activate && python3.13 -m data.bronze.update_krx --tickers {TICKERS}
```

JP tickers:

```bash
source venv/bin/activate && python3.13 -m data.bronze.update_jp --tickers {TICKERS}
```

**Then build silver + gold for all involved markets at once:**

```bash
source venv/bin/activate && python3.13 -m data.silver.build --markets {MARKETS}
source venv/bin/activate && python3.13 -m data.gold.build --panel valuation --markets {MARKETS}
```

Where `{MARKETS}` is the space-separated list of markets that had tickers (e.g., `us kr`).

**Verify** gold data exists for each ticker:

```python
import pandas as pd
panel = pd.read_parquet('data/gold/out/valuation_panel.parquet')
for t in ALL_TICKERS:
    data = panel[panel['ticker'] == t]
    assert len(data) > 0, f"No data for {t}"
    assert data['revenue_ttm'].notna().any(), f"No revenue for {t}"
```

If verification fails, report the error and stop.

## 3. Run analysis

### Single mode (1 ticker)

Read `playbook/SHALLOW_DIVE.md` and follow it as the analysis protocol. Also read the knowledge files it references from `knowledge/` directory. Execute Phase 1 through Phase 11 for the ticker. Save the output to `research/shallow-dive/{TICKER}_{company_name}.md`.

### Batch mode (2+ tickers)

**Phase 0 is already done above.** Now spawn one Agent per ticker, all in parallel using `run_in_background: true`:

For each ticker, launch an Agent with this prompt structure:

```text
Read playbook/SHALLOW_DIVE.md and follow it as the analysis protocol.
Read the knowledge files it references from knowledge/ directory.
Execute Phase 1 through Phase 11 for {TICKER} (market: {MARKET}).

Gold data is already built at data/gold/out/valuation_panel.parquet.

Save output to: research/shallow-dive/{TICKER}_{company_name}.md

YAML frontmatter must include: ticker, shallow_date, track_verdict, confidence, deep_eligible,
and the relevant scenario fields (scenario_pv_weighted for Buffett, scenario_cagr_bull for Fisher).

{MARKDOWN_LINT_RULES}
```

After ALL agents complete, read each output file and synthesize a comparison table in the conversation (not a separate file). The comparison table should include:

| Ticker | Company | Track | Confidence | Phase 10 Key Metric | Deep Eligible | Priority |
| --- | --- | --- | --- | --- | --- | --- |

Group by track (Buffett / Fisher / Undecided). For Buffett-assigned tickers show PV/현재가 ratio; for Fisher-assigned show Bull CAGR.

## 4. Markdown lint rules

Apply these rules when writing ALL markdown output files. These prevent markdownlint errors at commit time:

- Table separator rows MUST have spaces: `| --- |` not `|---|`
- Blockquote blank lines MUST keep `>`: never leave a bare blank line inside a blockquote
- Do NOT use bold as heading: use `### Heading` not `**Heading**`
- Lists MUST have blank lines before and after
- Heading levels MUST increment by one: `## → ###` not `## → ####`
- No inline HTML: no `<br>`, `<sub>`, etc.
- Table rows MUST have consistent column count matching the header

## 5. Output format

Each ticker's output file follows `playbook/SHALLOW_DIVE.md` "출력 포맷" section. Key requirements:

- Path: `research/shallow-dive/{TICKER}_{company_name}.md`
- YAML frontmatter with: `ticker`, `shallow_date`, `track_verdict`, `confidence`, `deep_eligible`
- Section structure: Phase 1~11 as specified in the playbook template
