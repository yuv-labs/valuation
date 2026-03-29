"""
Domain types for the valuation framework.

These dataclasses provide typed interfaces between components, ensuring
policies don't directly depend on raw DataFrame columns.
"""

from dataclasses import dataclass
from dataclasses import field
from typing import Any, Generic, Optional, TypeVar

import pandas as pd

_T = TypeVar('_T')


@dataclass
class PolicyOutput(Generic[_T]):
  """
  Standard output from any policy.

  Every policy returns both a computed value and diagnostic information
  explaining how the value was computed.

  Attributes:
    value: The computed value (type depends on policy)
    diag: Dictionary of diagnostic information
  """
  value: _T
  diag: dict[str, Any] = field(default_factory=dict)


@dataclass
class QuarterData:
  """
  Financial data for a single fiscal quarter.

  All metrics are synchronized - same quarter, same filing version.
  Missing values are explicitly None.

  Attributes:
    fiscal_year: Fiscal year (e.g., 2024)
    fiscal_quarter: Quarter identifier (Q1, Q2, Q3, Q4)
    end: Quarter end date
    filed: SEC filing date
    cfo_ttm: Trailing 12-month Cash Flow from Operations
    capex_ttm: Trailing 12-month Capital Expenditures
    shares: Shares outstanding
    cfo_q: Quarterly CFO (optional)
    capex_q: Quarterly CAPEX (optional)
  """
  fiscal_year: int
  fiscal_quarter: str
  end: pd.Timestamp
  filed: pd.Timestamp
  cfo_ttm: Optional[float] = None
  capex_ttm: Optional[float] = None
  shares: Optional[float] = None
  cfo_q: Optional[float] = None
  capex_q: Optional[float] = None
  # Normalized earnings support (nullable).
  revenue_ttm: Optional[float] = None
  ebit_ttm: Optional[float] = None
  total_assets: Optional[float] = None
  total_equity: Optional[float] = None
  current_liabilities: Optional[float] = None
  cash: Optional[float] = None

  @property
  def period(self) -> str:
    """Return period string (e.g., '2024Q1')."""
    return f'{self.fiscal_year}{self.fiscal_quarter}'


@dataclass
class FundamentalsSlice:
  """
  Point-in-time slice of fundamental data for a single company.

  This is the primary input to policies. All data should reflect only
  what was available as of the cutoff date (PIT-safe).

  Attributes:
    ticker: Company ticker symbol
    as_of_date: PIT cutoff date (only data filed before this is used)
    quarters: List of QuarterData, sorted by fiscal period (oldest first)
  """
  ticker: str
  as_of_date: pd.Timestamp
  quarters: list[QuarterData]

  @property
  def latest(self) -> QuarterData:
    """Return the most recent quarter."""
    return self.quarters[-1]

  @property
  def latest_cfo_ttm(self) -> float:
    """Most recent TTM CFO value."""
    val = self.latest.cfo_ttm
    if val is None:
      raise ValueError(f'{self.ticker}: Missing cfo_ttm in latest quarter')
    return val

  @property
  def latest_capex_ttm(self) -> float:
    """Most recent TTM CAPEX value."""
    val = self.latest.capex_ttm
    if val is None:
      raise ValueError(f'{self.ticker}: Missing capex_ttm in latest quarter')
    return val

  @property
  def latest_shares(self) -> float:
    """Most recent shares count."""
    val = self.latest.shares
    if val is None:
      raise ValueError(f'{self.ticker}: Missing shares in latest quarter')
    return val

  @property
  def latest_filed(self) -> pd.Timestamp:
    """Filing date of the most recent data."""
    return self.latest.filed

  @property
  def as_of_end(self) -> pd.Timestamp:
    """Quarter end date of the most recent data (alias for latest.end)."""
    return self.latest.end

  @property
  def cfo_ttm_history(self) -> list[Optional[float]]:
    """List of TTM CFO values (oldest first)."""
    return [q.cfo_ttm for q in self.quarters]

  @property
  def capex_ttm_history(self) -> list[Optional[float]]:
    """List of TTM CAPEX values (oldest first)."""
    return [q.capex_ttm for q in self.quarters]

  @property
  def shares_history(self) -> list[Optional[float]]:
    """List of shares values (oldest first)."""
    return [q.shares for q in self.quarters]

  @property
  def latest_revenue(self) -> float:
    """Most recent TTM Revenue."""
    val = self.latest.revenue_ttm
    if val is None:
      raise ValueError(f'{self.ticker}: Missing revenue_ttm in latest quarter')
    return val

  @property
  def latest_ebit(self) -> float:
    """Most recent TTM EBIT (Operating Income)."""
    val = self.latest.ebit_ttm
    if val is None:
      raise ValueError(f'{self.ticker}: Missing ebit_ttm in latest quarter')
    return val

  @property
  def latest_invested_capital(self) -> float:
    """Most recent Invested Capital (Total Assets - Current Liab - Cash)."""
    assets = self.latest.total_assets
    cur_liab = self.latest.current_liabilities
    cash = self.latest.cash
    if assets is None or cur_liab is None:
      raise ValueError(
          f'{self.ticker}: Missing balance sheet data for invested capital')
    cash_val = cash if cash is not None else 0.0
    return assets - cur_liab - cash_val

  @property
  def revenue_ttm_history(self) -> list[Optional[float]]:
    """List of TTM Revenue values (oldest first)."""
    return [q.revenue_ttm for q in self.quarters]

  @property
  def ebit_ttm_history(self) -> list[Optional[float]]:
    """List of TTM EBIT values (oldest first)."""
    return [q.ebit_ttm for q in self.quarters]

  def weighted_yearly_avg(
      self,
      metric: str,
      weights: tuple[float, ...] = (3.0, 2.0, 1.0),
  ) -> tuple[Optional[float], dict[str, Any]]:
    """
    Calculate weighted average of a metric over N years.

    Buckets quarters by years ago from as_of_date:
      - Year 1: 0 ~ 1.25 years ago
      - Year 2: 1.25 ~ 2.25 years ago
      - Year N: (N-1)+0.25 ~ N+0.25 years ago

    For each year, calculates average of available quarters.
    Then applies weighted average across years with data.

    Args:
      metric: Attribute name on QuarterData (e.g., 'cfo_ttm', 'capex_ttm')
      weights: Weights for each year (default: 3:2:1 for 3 years)
               Length determines how many years to consider.

    Returns:
      Tuple of (weighted_avg, diagnostics_dict)
      Returns (None, diag) if no data available
    """
    num_years = len(weights)
    year_buckets: dict[int, list[float]] = {
        i: [] for i in range(1, num_years + 1)
    }

    for q in self.quarters:
      val = getattr(q, metric, None)
      if val is None:
        continue

      years_ago = (self.as_of_date - q.end).days / 365.25

      if years_ago < 0:
        continue

      for year_idx in range(1, num_years + 1):
        lower = 0 if year_idx == 1 else (year_idx - 1) + 0.25
        upper = year_idx + 0.25
        if lower <= years_ago < upper:
          year_buckets[year_idx].append(val)
          break

    yearly_avgs: list[tuple[float, float, int]] = []
    diag_yearly: dict[str, Any] = {}

    for year_idx, weight in enumerate(weights, 1):
      bucket = year_buckets[year_idx]
      if bucket:
        avg = sum(bucket) / len(bucket)
        yearly_avgs.append((avg, weight, year_idx))
        diag_yearly[f'year{year_idx}_avg'] = avg
        diag_yearly[f'year{year_idx}_n'] = len(bucket)

    if not yearly_avgs:
      return None, {'error': 'no_data', 'metric': metric}

    total_weight = sum(w for _, w, _ in yearly_avgs)
    weighted_avg = sum(avg * w for avg, w, _ in yearly_avgs) / total_weight

    years_used = [y for _, _, y in yearly_avgs]
    weights_used = [w for _, w, _ in yearly_avgs]

    diag = {
        'method': 'weighted_yearly_avg',
        'metric': metric,
        'years_used': years_used,
        'weights_used': weights_used,
        'weighted_avg': weighted_avg,
        **diag_yearly,
    }

    return weighted_avg, diag

  @classmethod
  def from_panel(cls, panel: pd.DataFrame, ticker: str,
                 as_of_date: pd.Timestamp) -> 'FundamentalsSlice':
    """
    Construct FundamentalsSlice from Gold panel with PIT filtering.

    Args:
      panel: Gold valuation panel DataFrame
      ticker: Company ticker symbol
      as_of_date: Point-in-time date (only data filed <= this date)

    Returns:
      FundamentalsSlice with PIT-filtered data
    """
    ticker_data = panel[panel['ticker'] == ticker].copy()
    if ticker_data.empty:
      raise ValueError(f'No data for ticker {ticker}')

    pit_data = ticker_data[ticker_data['filed'] <= as_of_date].copy()
    if pit_data.empty:
      raise ValueError(f'No data for {ticker} as of {as_of_date.date()}')

    pit_data = pit_data.sort_values('filed')
    pit_data = pit_data.groupby(['fiscal_year', 'fiscal_quarter'],
                                as_index=False).tail(1)

    pit_data = pit_data.sort_values(['fiscal_year', 'fiscal_quarter'])

    quarters: list[QuarterData] = []
    for _, row in pit_data.iterrows():
      qd = QuarterData(
          fiscal_year=int(row['fiscal_year']),
          fiscal_quarter=str(row['fiscal_quarter']),
          end=row['end'],
          filed=row['filed'],
          cfo_ttm=_safe_float(row.get('cfo_ttm')),
          capex_ttm=_safe_float(row.get('capex_ttm')),
          shares=_safe_float(row.get('shares_q')),
          cfo_q=_safe_float(row.get('cfo_q')),
          capex_q=_safe_float(row.get('capex_q')),
          revenue_ttm=_safe_float(row.get('revenue_ttm')),
          ebit_ttm=_safe_float(row.get('ebit_ttm')),
          total_assets=_safe_float(row.get('total_assets_q')),
          total_equity=_safe_float(row.get('total_equity_q')),
          current_liabilities=_safe_float(row.get('current_liabilities_q')),
          cash=_safe_float(row.get('cash_q')),
      )
      quarters.append(qd)

    if not quarters:
      raise ValueError(f'No valid quarters for {ticker} as of {as_of_date}')

    latest = quarters[-1]
    missing = []
    if latest.cfo_ttm is None:
      missing.append('cfo_ttm')
    if latest.capex_ttm is None:
      missing.append('capex_ttm')
    if latest.shares is None:
      missing.append('shares')
    if missing:
      raise ValueError(
          f'{ticker}: Missing required data as of {as_of_date.date()}: '
          f'{', '.join(missing)}')

    return cls(ticker=ticker, as_of_date=as_of_date, quarters=quarters)

  @classmethod
  def from_ticker_panel(cls, ticker_panel: pd.DataFrame,
                        as_of_date: pd.Timestamp) -> 'FundamentalsSlice':
    """
    Construct FundamentalsSlice from pre-filtered ticker panel.

    Args:
      ticker_panel: Panel already filtered for a single ticker
      as_of_date: Point-in-time date (only data filed <= this date)

    Returns:
      FundamentalsSlice with PIT-filtered data
    """
    if ticker_panel.empty:
      raise ValueError('Empty ticker panel')

    ticker = str(ticker_panel['ticker'].iloc[0])

    pit_data = ticker_panel[ticker_panel['filed'] <= as_of_date].copy()
    if pit_data.empty:
      raise ValueError(f'No data for {ticker} as of {as_of_date.date()}')

    pit_data = pit_data.sort_values('filed')
    pit_data = pit_data.groupby(['fiscal_year', 'fiscal_quarter'],
                                as_index=False).tail(1)

    pit_data = pit_data.sort_values(['fiscal_year', 'fiscal_quarter'])

    quarters: list[QuarterData] = []
    for _, row in pit_data.iterrows():
      qd = QuarterData(
          fiscal_year=int(row['fiscal_year']),
          fiscal_quarter=str(row['fiscal_quarter']),
          end=row['end'],
          filed=row['filed'],
          cfo_ttm=_safe_float(row.get('cfo_ttm')),
          capex_ttm=_safe_float(row.get('capex_ttm')),
          shares=_safe_float(row.get('shares_q')),
          cfo_q=_safe_float(row.get('cfo_q')),
          capex_q=_safe_float(row.get('capex_q')),
          revenue_ttm=_safe_float(row.get('revenue_ttm')),
          ebit_ttm=_safe_float(row.get('ebit_ttm')),
          total_assets=_safe_float(row.get('total_assets_q')),
          total_equity=_safe_float(row.get('total_equity_q')),
          current_liabilities=_safe_float(row.get('current_liabilities_q')),
          cash=_safe_float(row.get('cash_q')),
      )
      quarters.append(qd)

    if not quarters:
      raise ValueError(f'No valid quarters for {ticker} as of {as_of_date}')

    latest = quarters[-1]
    missing = []
    if latest.cfo_ttm is None:
      missing.append('cfo_ttm')
    if latest.capex_ttm is None:
      missing.append('capex_ttm')
    if latest.shares is None:
      missing.append('shares')
    if missing:
      raise ValueError(
          f'{ticker}: Missing required data as of {as_of_date.date()}: '
          f'{', '.join(missing)}')

    return cls(ticker=ticker, as_of_date=as_of_date, quarters=quarters)


def _safe_float(val: Any) -> Optional[float]:
  """Convert value to float, returning None if NA or invalid."""
  if val is None or pd.isna(val):
    return None
  try:
    return float(val)
  except (ValueError, TypeError):
    return None


@dataclass
class MarketSlice:
  """
  Market price data for comparison.

  Attributes:
    price: Market price per share
    price_date: Date of the price observation
  """
  price: float
  price_date: pd.Timestamp


@dataclass
class PreparedInputs:
  """
  Fully prepared inputs for the DCF engine.

  All policy outputs are aggregated here before passing to the pure math engine.

  Attributes:
    oe0: Initial owner earnings (CFO - CAPEX)
    sh0: Current shares outstanding
    buyback_rate: Annual share reduction rate
    g0: Initial growth rate (first year in growth_path)
    g_terminal: Terminal growth rate (for Gordon Growth)
    growth_path: Yearly growth rates [g1, g2, ..., gN] from fade policy
    n_years: Number of explicit forecast years
    discount_rate: Required return / discount rate
  """
  oe0: float
  sh0: float
  buyback_rate: float
  g0: float
  g_terminal: float
  growth_path: list[float]
  n_years: int
  discount_rate: float

  @property
  def g_end(self) -> float:
    """Growth rate at end of explicit period (last in growth_path)."""
    if not self.growth_path:
      return self.g_terminal
    return self.growth_path[-1]


@dataclass
class ValuationResult:
  """
  Complete valuation result with diagnostics.

  Attributes:
    iv_per_share: Intrinsic value per share
    pv_explicit: Present value of explicit forecast period
    tv_component: Terminal value component (discounted)
    market_price: Market price (if provided)
    price_to_iv: Market price / IV ratio (if market price provided)
    margin_of_safety: (IV - Price) / IV (if market price provided)
    inputs: The PreparedInputs used for calculation
    diag: Merged diagnostics from all policies
  """
  iv_per_share: float
  pv_explicit: float
  tv_component: float
  market_price: Optional[float] = None
  price_to_iv: Optional[float] = None
  margin_of_safety: Optional[float] = None
  inputs: Optional[PreparedInputs] = None
  diag: dict[str, Any] = field(default_factory=dict)

  def to_dict(self) -> dict[str, Any]:
    """Convert to dictionary for DataFrame creation."""
    result = {
        'iv_per_share': self.iv_per_share,
        'pv_explicit': self.pv_explicit,
        'tv_component': self.tv_component,
        'market_price': self.market_price,
        'price_to_iv': self.price_to_iv,
        'margin_of_safety': self.margin_of_safety,
    }
    if self.inputs:
      result.update({
          'oe0': self.inputs.oe0,
          'sh0': self.inputs.sh0,
          'buyback_rate': self.inputs.buyback_rate,
          'g0': self.inputs.g0,
          'g_terminal': self.inputs.g_terminal,
          'discount_rate': self.inputs.discount_rate,
      })
    result.update(self.diag)
    return result


@dataclass
class ExclusionReason:
  """
  Reason why a valuation was excluded/skipped.

  Attributes:
    reason: Human-readable explanation
    code: Machine-readable code (e.g., 'insufficient_data', 'low_growth')
    details: Additional context
  """
  reason: str
  code: str
  details: dict[str, Any] = field(default_factory=dict)
