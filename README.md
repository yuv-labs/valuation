# Equity Analysis

Equity analysis framework: DCF valuation + multi-factor stock screening
for US and Korean markets.

> **Disclaimer**: This is an analysis tool for research purposes.
> Investment decisions are the sole responsibility of the investor.
> This tool does not constitute financial advice.

## Requirements

- Python 3.13
- Dependencies managed via `pyproject.toml`
- DART API key for Korean data (free at opendart.fss.or.kr)

### Installation

```bash
# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate

# Production (runtime dependencies only)
pip install -e .

# Development (includes pytest, linting tools, etc.)
pip install -e ".[dev]"
```

## Quick Start

### Stock Screening (US + Korea)

```bash
# 1. Ingest US data (SEC + Stooq prices)
python -m data.bronze.update --tickers-file data/snp500.txt \
  --sec-user-agent "your_name research (your@email.com)"

# 2. Build Silver + Gold screening panel
python -m data.silver.build
python -c "
from pathlib import Path
from data.gold.screening.panel import ScreeningPanelBuilder
builder = ScreeningPanelBuilder(
    silver_dir=Path('data/silver/out'),
    gold_dir=Path('data/gold/out'),
    bronze_dir=Path('data/bronze/out'),  # includes KR data
)
builder.build()
builder.save()
"

# 3. Run screening
python -m screening.run --top 25
```

### DCF Valuation (US)

```bash
# 1. Data ingestion
python -m data.bronze.update --tickers-file example/tickers/bigtech.txt \
  --sec-user-agent "your_name research (your@email.com)"

# 2. Build pipeline
python -m data.silver.build
python -m data.gold.valuation.build

# 3. Run valuation
python -m valuation.run --ticker AAPL --as-of 2024-09-30

# 4. IV band chart
python -m valuation.analysis.plot_prices \
  --tickers AAPL --market us \
  --config-dir scenarios/base --output-dir output/charts
```

### DCF Valuation (Korea)

```bash
# 1. Build Silver (DART + KRX)
python -m data.silver.build --markets kr

# 2. Run valuation
python -m valuation.run --ticker 000270 --market kr --as-of 2025-03-31 \
  --gold-path data/gold/out/valuation_panel.parquet

# 3. IV band chart
python -m valuation.analysis.plot_prices \
  --tickers 000270 192080 005850 --market kr \
  --config-dir scenarios/base --output-dir output/charts \
  --gold-path data/gold/out/valuation_panel.parquet
```

### Scenario Experimentation + Visualization

Compare multiple valuation scenarios systematically:

```bash
# 1. Generate scenario configs (Grid Search)
python -m valuation.analysis.generate_grid_configs \
  --discount fixed_0p07 fixed_0p09 \
  --terminal gordon gordon_2pct \
  --n-years 3 5 10 \
  --output-dir scenarios/my_experiment

# 2. Run backtest with all scenarios
python -m valuation.analysis.backtest_from_configs \
  --ticker AAPL \
  --start-date 2020-01-01 \
  --end-date 2025-12-31 \
  --config-dir example/scenarios \
  --output output/valuation/bigtech.csv

# 3. Visualize comparison (with parallel processing)
python -m valuation.analysis.plot_prices \
  --tickers-file example/tickers/bigtech.txt \
  --start-date 2020-01-01 \
  --end-date 2025-12-31 \
  --config-dir example/scenarios \
  --output-dir output/analysis/price_charts \
  --concurrency 4
```

### Stock Screening

Screen stocks based on valuation band criteria:

```bash
# Find undervalued stocks within reliable valuation bands
python -m valuation.analysis.band_screening \
  --tickers-file data/snp500.txt \
  --lower-config scenarios/grid_search/conservative.json \
  --upper-config scenarios/grid_search/aggressive.json \
  --start-date 2016-01-01 \
  --end-date 2025-12-31 \
  --tolerance-day 90 \
  --min-hit-rate 0.6 \
  --min-inband-ratio 0.5 \
  --dev-threshold 0.3 \
  --concurrency 8 \
  --output output/screened_tickers.txt
```

**Screening Criteria:**

- `min-hit-rate`: Minimum ratio of quarters with valid IV data
- `min-inband-ratio`: Market price within lower/upper IV bounds
- `dev-threshold`: Current undervaluation level (L(T)-P(T))/W(T)

**Example Output:**

![MSFT Scenario Comparison](example/charts/MSFT__comparison__12scenarios_e64025ed.png)

*Figure: MSFT intrinsic value across 12 scenarios (2×2×3 grid:
discount × terminal × n_years). Common policies shown in subtitle,
differences in legend.*

## DCF Model

This framework implements a **two-stage discounted cash flow (DCF) model**
based on Owner Earnings to estimate intrinsic value per share.

### Methodology

#### Stage 1: Explicit Forecast Period (N years)

- Projects Owner Earnings (OE = CFO - CAPEX) with declining growth rates
- Accounts for share buybacks/dilution
- Discounts each year's OE per share to present value

#### Stage 2: Terminal Value

- Applies Gordon Growth Model for perpetual growth beyond forecast period
- Assumes stable, low terminal growth rate (typically 2-3%)

### Key Formula

```text
IV = Σ(OEPS_t / (1+r)^t) + TV / (1+r)^N

Where:
  OEPS_t = Owner Earnings per Share in year t
  r = Discount rate (required return)
  TV = Terminal Value using Gordon Growth
  N = Forecast period length
```

### Key Assumptions

- **Cash flow proxy**: Owner Earnings (CFO - CAPEX) instead of Free Cash Flow
- **Growth path**: Initial growth rate that fades linearly to terminal rate
- **Share dynamics**: Incorporates historical buyback/dilution rates
- **Multiple scenarios**: Policy-based architecture allows testing different
  assumptions

For theoretical background, see
[Discounted Cash Flow (Wikipedia)](https://en.wikipedia.org/wiki/Discounted_cash_flow).
The DCF method has been used since the 1800s and was formally established by
Irving Fisher (1930) and John Burr Williams (1938).

## Architecture

### Data Pipeline (Bronze → Silver → Gold)

```text
Bronze (Raw)              Silver (Normalized)     Gold (Views)
├─ SEC filings         →  ├─ facts_long        →  ├─ valuation/  (DCF)
├─ Stooq prices           └─ companies            ├─ backtest/   (PIT)
├─ DART filings (KR)                               └─ screening/  (ratios)
└─ KRX prices (KR)
```

Bronze providers are pluggable (`BronzeProvider` ABC):

- `SECProvider` / `StooqProvider` for US
- `DARTProvider` / `KRXProvider` for Korea

Gold panels are independent modules, each with own `build.py`:

- `python -m data.gold.valuation.build`
- `python -m data.gold.backtest.build`
- `python -m data.gold.screening.build` (via Python API)

### Screening Framework

```text
Gold screening_panel (PE, PB, ROE, ROIC, margins, ...)
       ↓
Filters (Undervalued → Moat → Growth)
       ↓
Scorers (Fear + Quality → Opportunity)
       ↓
Ranked results
```

### Valuation Framework

```text
Domain Types (FundamentalsSlice, MarketSlice)
       ↓
Policies (CAPEX, Growth, Fade, Shares, Terminal, Discount)
       ↓
DCF Engine (pure math)
       ↓
ValuationResult (IV, diagnostics)
```

## Project Structure

```text
equity-analysis/
├── data/                  # ETL pipeline
│   ├── bronze/
│   │   ├── providers/     # Pluggable data sources
│   │   │   ├── base.py    # BronzeProvider ABC
│   │   │   ├── sec.py     # SEC EDGAR (US financials)
│   │   │   ├── stooq.py   # Stooq (US prices)
│   │   │   ├── dart.py    # DART (KR financials + shares)
│   │   │   └── krx.py     # KRX (KR prices)
│   │   └── update.py      # CLI orchestrator
│   ├── silver/
│   │   ├── config/
│   │   │   ├── metric_specs.py     # US SEC XBRL tags (12 metrics)
│   │   │   └── metric_specs_kr.py  # KR DART account names
│   │   └── sources/
│   │       ├── sec/       # SEC extraction pipeline
│   │       └── dart/      # DART extraction pipeline
│   └── gold/
│       ├── core/          # BasePanelBuilder
│       ├── valuation/     # DCF panel (latest version)
│       ├── backtest/      # PIT panel (all versions)
│       └── screening/     # Screening panel (ratios)
│
├── valuation/             # DCF valuation engine
│   ├── domain/            # Typed domain objects
│   ├── engine/            # Pure DCF math
│   ├── policies/          # Estimation policies
│   └── analysis/          # Batch valuation, backtesting
│
├── screening/             # Stock screening
│   ├── run.py             # CLI: python -m screening.run
│   ├── filters/           # Undervalued, Moat, Growth
│   ├── scorers/           # Fear, Quality, Composite
│   └── report/            # Output formatting
│
├── tools/                 # Utility scripts
├── scenarios/             # JSON scenario configs
└── output/                # Screening results (CSV)
```

## Key Features

### Screening

- **Multi-factor screening**: PE, PB, ROE, ROIC, FCF yield,
  margins, debt ratios
- **Signal-based filters**: Undervalued, Moat, Growth
- **Composite scoring**: Fear + Quality = Opportunity
- **US + Korea**: SEC + DART official financial data

### Valuation

- **Policy-based architecture**: Easy experimentation
- **PIT (Point-in-Time)**: No look-ahead bias
- **JSON config scenarios**: Reproducible experiments
- **Grid search**: Scenario combinations
- **Batch processing**: Entire stock lists

## Data Coverage

### US Market

- **Source**: SEC EDGAR (10,500+ companies) + Stooq (prices)
- **Metrics**: 12 fundamentals (CFO, CAPEX, Revenue, etc.)
- **Coverage**: 83-100% across S&P 500

### Korean Market

- **Source**: DART Open API + KRX via pykrx (prices)
- **Metrics**: 11 fundamentals from K-IFRS
- **Limitation**: Financial companies not available via DART
- **Requires**: DART API key (free at opendart.fss.or.kr)

### Ticker Filtering

```bash
# Filter out financial/utility/REIT sectors from S&P 500
python tools/filter_tickers.py data/snp500.txt -o data/snp500_filtered.txt
```

## Configuration

```python
from valuation.scenarios.config import ScenarioConfig

config = ScenarioConfig(
    name='custom',
    pre_maint_oe='avg_3y',    # or 'ttm' - CFO calculation method
    maint_capex='avg_3y',     # or 'ttm' - CAPEX calculation method
    growth='avg_oe_3y',       # or 'fixed_0p10', 'fixed_0p12', etc.
    fade='linear',            # Linear fade to terminal
    shares='avg_5y',          # 5yr average share change
    terminal='gordon',        # Gordon growth at 3% (or 'gordon_2pct')
    discount='fixed_0p10',    # 10% discount rate
    n_years=10,               # 10-year explicit forecast
)
```

## Documentation

- **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)**: Complete project
  structure and entry points
- **[data/README.md](data/README.md)**: ETL pipeline details
  (Bronze/Silver/Gold)
- **[valuation/README.md](valuation/README.md)**: Valuation framework
  and policies
- **[valuation/analysis/README.md](valuation/analysis/README.md)**:
  Analysis tools usage
- **[scenarios/README.md](scenarios/README.md)**: Scenario configuration
  and grid search

## Development

### Pre-commit

Install pre-commit after installing dependencies.

```bash
pre-commit install
```

### Adding New Policies

1. Create policy in `valuation/policies/`
2. Register in `valuation/scenarios/registry.py`
3. Use in `ScenarioConfig`

See [valuation/README.md](valuation/README.md) for details.
