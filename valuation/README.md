# Valuation Framework

Strategy/policy-based DCF valuation system for rapid experimentation.

## Architecture

```text
valuation/
├── domain/         # Typed domain objects (FundamentalsSlice, ValuationResult, etc.)
├── engine/         # Pure DCF math functions (no pandas, no I/O)
├── policies/       # Pluggable estimation policies
│   ├── pre_maintenance_oe.py  # NormalizedMarginOE, NormalizedROICOE
│   ├── oe.py       # TTMOwnerEarnings, AvgQuarterlyOE, MedianQuarterlyOE
│   ├── capex.py    # TTMCapex, WeightedAverageCapex, IntensityClippedCapex
│   ├── growth.py   # CAGRGrowth (with threshold/clipping)
│   ├── fade.py     # LinearFade, StepFade
│   ├── shares.py   # AvgShareChange (buyback rate)
│   ├── terminal.py # GordonTerminal, ExitMultipleTerminal
│   └── discount.py # FixedRate
├── scenarios/      # ScenarioConfig + policy registry
├── analysis/       # AnalysisRunner + metrics
└── run.py          # Single valuation entrypoint
```

## DCF Model

The framework uses a **two-stage DCF model** to calculate intrinsic value:

### Stage 1: Explicit Forecast Period (N years)

**Owner Earnings** grow and get discounted to present value:

```text
For each year t = 1 to N:
  OE(t) = OE(t-1) × (1 + g(t))           # Earnings growth
  Shares(t) = Shares(t-1) × (1 - b)      # Share buybacks
  OEPS(t) = OE(t) / Shares(t)            # Per-share earnings

PV_explicit = Σ [ OEPS(t) / (1+r)^t ]    # Discount to present
```

Where:

- `OE(t)` = Owner Earnings (CFO - CAPEX) in year t
- `g(t)` = Growth rate (typically fades from g0 to g_terminal)
- `b` = Buyback rate (share reduction rate)
- `r` = Discount rate (required return)

### Stage 2: Terminal Value

**Perpetual growth** beyond the explicit period using Gordon Growth:

```text
TV = OEPS(N) × (1 + g_terminal) / (r - g_terminal)
PV_terminal = TV / (1+r)^N
```

Constraint: `r > g_terminal` (required for convergence)

### Total Intrinsic Value

```text
IV per share = PV_explicit + PV_terminal
```

### Key Inputs

All inputs prepared by **policies**:

| Input | Policy | Description |
|-------|--------|-------------|
| Pre-Maint OE | PreMaintOE | Normalized Earnings pre-capex (Margin avg, ROIC avg) |
| OE0 | OE | Owner Earnings (TTM, avg, or median) |
| Shares | Shares | Current diluted shares |
| b | Shares | Buyback rate (5yr CAGR) |
| g0 | Growth | Initial growth (3yr CAGR, clipped) |
| g(t) | Fade | Growth path (linear fade) |
| g_terminal | Terminal | Perpetual growth (Gordon) or Exit Multiple (5x, 7x, etc.) |
| r | Discount | Required return (10%) |

See `valuation/engine/dcf.py` for detailed math implementation.

## Quick Start

### Single Valuation

```python
from valuation.run import run_valuation
from valuation.scenarios.config import ScenarioConfig

result = run_valuation(
    ticker='GOOGL',
    as_of_date='2023-06-30',
    config=ScenarioConfig.default(),
)

print(f"IV: ${result.iv_per_share:.2f}")
print(f"Price/IV: {result.price_to_iv:.2%}")
```

### Backtest

```python
from valuation.backtest.runner import BacktestRunner
from valuation.scenarios.config import ScenarioConfig

runner = BacktestRunner(
    ticker='GOOGL',
    start_date='2022-01-01',
    end_date='2023-12-31',
    scenarios=[
        ScenarioConfig.default(),
        ScenarioConfig.raw_capex(),
        ScenarioConfig.discount_6pct(),
    ],
)

results = runner.run()
results.to_csv('backtest_results.csv')
```

### CLI Usage

```bash
# Single valuation
python -m valuation.run --ticker GOOGL --as-of 2023-06-30 --scenario default

# Backtest
python -m valuation.backtest.runner --ticker GOOGL \
  --start-date 2022-01-01 --end-date 2023-12-31 \
  --scenarios default raw_capex
```

## Adding New Policies

### 1. Create the Policy Class

```python
# valuation/policies/capex.py

class MyCustomCapex(CapexPolicy):
  def __init__(self, my_param: float = 1.0):
    self.my_param = my_param

  def compute(self, data: FundamentalsSlice) -> PolicyOutput[float]:
    capex = ...  # your calculation
    return PolicyOutput(
      value=capex,
      diag={
        'capex_method': 'my_custom',
        'my_param': self.my_param,
        'capex_value': capex,
      }
    )
```

### 2. Register in the Registry

```python
# valuation/scenarios/registry.py

CAPEX_POLICIES['my_custom'] = lambda: MyCustomCapex(my_param=1.5)
```

### 3. Use in Scenario

```python
config = ScenarioConfig(
    name='my_experiment',
    capex='my_custom',  # Use your new policy
    growth='cagr_3y_clip',
    fade='linear',
    shares='avg_5y',
    terminal='gordon',
    discount='fixed_0p10',
)

result = run_valuation(ticker='GOOGL', as_of_date='2023-06-30', config=config)
```

## Available Policies

### Owner Earnings (OE)

- `ttm`: CFO_TTM - CAPEX (standard)
- `avg_4q`: Average of last 4 quarters (annualized)
- `avg_8q`: Average of last 8 quarters (annualized)
- `median`: Median of last 8 quarters (outlier resistant)
- `latest_q`: Latest quarter (annualized)

### CAPEX

- `ttm`: Raw TTM CAPEX
- `weighted_3y_123`: 3-year weighted average (1:2:3)
- `weighted_3y`: 3-year simple weighted average
- `intensity_clipped`: Clip CAPEX/CFO ratio at 90th percentile

### Growth

- `cagr_3y_clip`: 3-year CAGR, threshold 4%, clip 0-18%
- `cagr_3y_clip_25`: 3-year CAGR, threshold 4%, clip 0-25%
- `cagr_3y_no_clip`: 3-year CAGR, no clipping
- `cagr_5y_clip`: 5-year CAGR, clip 0-18%

### Fade

- `linear`: Linear fade from g0 to gT + 1%
- `linear_0p02`: Linear fade from g0 to gT + 2%

### Shares

- `avg_5y`: 5-year average share change
- `avg_3y`: 3-year average share change
- `avg_10y`: 10-year average share change

### Terminal

- `gordon`: Gordon growth at 3%
- `gordon_2pct`: Gordon growth at 2%
- `gordon_4pct`: Gordon growth at 4%

### Discount

- `fixed_0p06`: Fixed 6%
- `fixed_0p08`: Fixed 8%
- `fixed_0p10`: Fixed 10%
- `fixed_0p12`: Fixed 12%

## Design Principles

1. **Separation of Concerns**
   - Engine: Pure math, no pandas
   - Policies: Estimation logic with diagnostics
   - Runner: Orchestration and PIT filtering

2. **Explainable Results**
   - Every policy returns `PolicyOutput[T]` with value and diagnostics
   - Full diagnostic trail in `ValuationResult.diag`

3. **Serializable Configuration**
   - `ScenarioConfig` is JSON/YAML friendly
   - Policy names map to factories in registry

4. **Point-in-Time Safety**
   - `FundamentalsSlice` filters data by filing date
   - Split adjustment applied before PIT filtering
