# Data Pipeline (Bronze → Silver → Gold)

ETL pipeline for financial data processing with medallion architecture.

## Bronze Layer

**Purpose**: Raw data ingestion from external sources

### US Data

**SEC companyfacts** (financial statements):

```bash
python -m data.bronze.update \
  --tickers-file example/tickers/russell1000.txt \
  --sec-user-agent "YourName research (you@email.com)" \
  --refresh-days 7
```

**Stooq prices** (daily OHLCV — via dump file):

Stooq's per-ticker API has daily rate limits. Use the bulk dump instead:

1. Download from <https://stooq.com/db/h/> → Historical Data → U.S. Daily ASCII
2. Ingest:

```bash
python -m data.bronze.ingest_stooq_dump \
  --zip ~/Downloads/d_us_txt.zip \
  --tickers-file example/tickers/russell1000.txt
```

**Output**: `data/bronze/out/sec/`, `data/bronze/out/stooq/`

### KR Data

**DART** (financial statements): collected via DART Open API into
`data/bronze/out/dart/`. Requires `DART_API_KEY` env var.

**KRX prices** (daily OHLCV via pykrx):

```bash
python -m data.bronze.update_krx \
  --tickers-file example/tickers/kr_filtered.txt
```

**Output**: `data/bronze/out/dart/`, `data/bronze/out/krx/`

### Ticker Lists (`example/tickers/`)

| File | Description | Count |
|:--|:--|--:|
| `russell1000.txt` | Russell 1000 (US screening pool) | 1,006 |
| `kr_filtered.txt` | KR >= 3000억 market cap | ~342 |
| `kr_all.txt` | All KR listed (DART CORPCODE) | 3,959 |
| `dow30.txt` | Dow 30 (example) | 30 |
| `bigtech.txt` | Big tech (example) | 4 |

Regenerate `kr_filtered.txt`:

```bash
python scripts/filter_kr_by_mcap.py
```

## Silver Layer

**Purpose**: Normalize raw data into consistent quarterly metrics

**Key Features**:

1. **YTD → Quarterly conversion**: Cumulative to discrete quarters
2. **TTM calculation**: Rolling 4-quarter sum
3. **Fiscal year handling**: Company-specific fiscal year ends
4. **Shares normalization**: Actual count (not millions)
5. **PIT history**: All historical values for backtesting

```bash
python -m data.silver.build --markets us      # US only
python -m data.silver.build --markets kr      # KR only
python -m data.silver.build --markets us kr   # Both
```

**Outputs**:

- `companies.parquet`: Company metadata (ticker, cik, FYE)
- `facts_long.parquet`: Raw facts with all filed versions
- `prices_daily.parquet`: Daily stock prices

**See [silver/README.md](silver/README.md) for details.**

## Gold Layer

**Purpose**: Build analytical panels by joining Silver datasets

```bash
python -m data.gold.build --panel screening --min-date 2019-01-01
python -m data.gold.build --panel valuation --min-date 2010-01-01
```

**Outputs**:

- `screening_panel.parquet`: Screening metrics (PE, ROIC, moat signals)
- `valuation_panel.parquet`: Latest filed version (current valuation)
- `backtest_panel.parquet`: All filed versions (PIT backtesting)

**See [gold/README.md](gold/README.md) for details.**

## Full Refresh Runbook

### US

```bash
# 1. Download Stooq dump: stooq.com/db/h/ → Historical → U.S. Daily ASCII
# 2. Ingest prices
python -m data.bronze.ingest_stooq_dump \
  --zip ~/Downloads/d_us_txt.zip \
  --tickers-file example/tickers/russell1000.txt
# 3. Fetch SEC financials
python -m data.bronze.update \
  --tickers-file example/tickers/russell1000.txt \
  --sec-user-agent "YourName research (you@email.com)"
# 4. Build Silver → Gold → Screen
python -m data.silver.build --markets us
python -m data.gold.build --panel screening --min-date 2019-01-01
python -m screening.run --track moat --top 50
```

### KR

```bash
# 1. Fetch KRX prices
python -m data.bronze.update_krx \
  --tickers-file example/tickers/kr_filtered.txt
# 2. Fetch DART financials (requires DART_API_KEY env var)
#    No standalone CLI yet — use DARTProvider programmatically:
python -c "
from pathlib import Path
import os
from data.bronze.providers.dart import DARTProvider
from data.bronze.update import load_tickers_from_file
tickers = load_tickers_from_file(Path('example/tickers/kr_filtered.txt'))
provider = DARTProvider(api_key=os.environ['DART_API_KEY'])
result = provider.fetch(tickers, Path('data/bronze/out'))
print(f'Fetched: {result.fetched}, Errors: {len(result.errors)}')
"
# 3. Build Silver → Gold → Screen
python -m data.silver.build --markets kr
python -m data.gold.build --panel screening --min-date 2019-01-01
python -m screening.run --track moat --min-mcap-kr 3e11 --top 50
```

## Known Issues

- **Stooq API rate limit**: Per-ticker API has daily hit limits
  (relaxed with an optional API key). Use the bulk dump file for
  initial ingestion.
- **SEC 404**: Some CIKs (ETFs, SPACs, shell companies) have no
  companyfacts. The ingestion script skips these automatically.
- **SEC filed < end**: A small number of SEC filings have `filed` dates
  before `end` dates. Treated as a warning, not a blocking error.
- **pykrx connectivity**: KRX data fetching (via pykrx) may fail in
  some network environments (overseas IP, VPN). Retry from a domestic
  network if requests time out or return empty results.
- **Financial services**: No CAPEX data (different valuation needed).
- **Stock splits**: Shares normalized to latest filed version in
  backtest_panel.

## Data Quality

### Silver Validations

1. Schema compliance (types, nullability)
2. Primary key uniqueness
3. YTD identity (Q1+Q2+Q3+Q4 ≈ Q4_ytd)
4. Fiscal year consistency

### Gold Validations

1. Schema compliance
2. Required fields (no NaN in critical columns)
3. Date alignment (filed ≤ date)
