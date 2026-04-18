"""
Schema definitions for Gold layer panels.

Each panel has a defined schema with:
- Column names and types
- Nullable constraints
- Primary keys for uniqueness validation
- Description for documentation

Usage:
  from data.gold.config.schemas import VALUATION_PANEL_SCHEMA

  # Validate DataFrame against schema
  errors = VALUATION_PANEL_SCHEMA.validate(df)
"""

from dataclasses import dataclass
from dataclasses import field

import pandas as pd


@dataclass
class ColumnSpec:
  """Specification for a single column."""
  name: str
  dtype: str
  nullable: bool = True
  description: str = ''


@dataclass
class PanelSchema:
  """
  Schema definition for a Gold panel.

  Provides validation and documentation for panel DataFrames.
  """
  name: str
  description: str
  columns: list[ColumnSpec]
  primary_key: list[str] = field(default_factory=list)

  def column_names(self) -> list[str]:
    """Return list of column names."""
    return [c.name for c in self.columns]

  def validate(self, df: pd.DataFrame) -> list[str]:
    """
    Validate DataFrame against schema.

    Returns:
      List of error messages (empty if valid)
    """
    errors = []

    # Check required columns
    expected = set(self.column_names())
    actual = set(df.columns)
    missing = expected - actual
    if missing:
      errors.append(f'Missing columns: {missing}')

    # Check primary key uniqueness
    if self.primary_key:
      pk_cols = [c for c in self.primary_key if c in df.columns]
      if not pk_cols:
        pass
      else:
        duplicates = df.duplicated(subset=pk_cols, keep=False).sum()
        if duplicates > 0:
          pk_str = ', '.join(pk_cols)
          errors.append(f'Primary key [{pk_str}] has {duplicates} duplicates')

    # Check nullable constraints
    for col_spec in self.columns:
      if col_spec.name not in df.columns:
        continue
      if col_spec.nullable:
        continue
      null_count = df[col_spec.name].isna().sum()
      if null_count > 0:
        errors.append(
            f'Column {col_spec.name} has {null_count} nulls (not nullable)')

    return errors

  def get_dtype_dict(self) -> dict:
    """Return dtype mapping for pandas."""
    return {c.name: c.dtype for c in self.columns}

  def summary(self) -> str:
    """Return human-readable schema summary."""
    lines = [
        f'Panel: {self.name}',
        f'Description: {self.description}',
        f'Primary Key: {self.primary_key}',
        '',
        'Columns:',
    ]
    for col in self.columns:
      null_str = 'nullable' if col.nullable else 'NOT NULL'
      lines.append(f'  {col.name}: {col.dtype} ({null_str})')
      if col.description:
        lines.append(f'    {col.description}')
    return '\n'.join(lines)


_COMMON_COLUMNS = [
    # Identity (non-nullable)
    ColumnSpec('ticker',
               'str',
               nullable=False,
               description='Company ticker symbol'),
    ColumnSpec('end',
               'datetime64[ns]',
               nullable=False,
               description='Fiscal period end date'),
    ColumnSpec('filed',
               'datetime64[ns]',
               nullable=False,
               description='SEC filing date'),
    # Fiscal info (non-nullable, for semantic grouping)
    ColumnSpec('fiscal_year',
               'int64',
               nullable=False,
               description='Fiscal year'),
    ColumnSpec('fiscal_quarter',
               'str',
               nullable=False,
               description='Fiscal quarter (Q1, Q2, Q3, Q4)'),
    # Financial metrics (all nullable - depends on data quality)
    ColumnSpec('cfo_q',
               'float64',
               nullable=True,
               description='Quarterly Cash Flow from Operations'),
    ColumnSpec('cfo_ttm',
               'float64',
               nullable=True,
               description='Trailing 12-month CFO'),
    ColumnSpec('capex_q',
               'float64',
               nullable=True,
               description='Quarterly Capital Expenditures'),
    ColumnSpec('capex_ttm',
               'float64',
               nullable=True,
               description='Trailing 12-month CAPEX'),
    ColumnSpec('shares_q',
               'float64',
               nullable=True,
               description='Quarterly share count'),
    # Normalized earnings metrics (nullable - not all tickers have these)
    ColumnSpec('revenue_ttm',
               'float64',
               nullable=True,
               description='Trailing 12-month Revenue'),
    ColumnSpec('ebit_ttm',
               'float64',
               nullable=True,
               description='Trailing 12-month EBIT (Operating Income)'),
    ColumnSpec('net_income_ttm',
               'float64',
               nullable=True,
               description='Trailing 12-month Net Income'),
    ColumnSpec('total_assets_q',
               'float64',
               nullable=True,
               description='Total Assets (point-in-time)'),
    ColumnSpec('total_equity_q',
               'float64',
               nullable=True,
               description='Total Equity (point-in-time)'),
    ColumnSpec('current_liabilities_q',
               'float64',
               nullable=True,
               description='Current Liabilities (point-in-time)'),
    ColumnSpec('cash_q',
               'float64',
               nullable=True,
               description='Cash and Equivalents (point-in-time)'),
    # Price data (nullable - depends on external data)
    ColumnSpec('date',
               'datetime64[ns]',
               nullable=True,
               description='Price date (first trading day after filed)'),
    ColumnSpec('price',
               'float64',
               nullable=True,
               description='Closing price on date'),
    ColumnSpec('market_cap',
               'float64',
               nullable=True,
               description='Market capitalization (shares * price)'),
    ColumnSpec('date_latest',
               'datetime64[ns]',
               nullable=True,
               description='Latest available price date from silver'),
    ColumnSpec('price_latest',
               'float64',
               nullable=True,
               description='Latest available closing price'),
    ColumnSpec('market_cap_latest',
               'float64',
               nullable=True,
               description='Market cap using latest price'),
]

VALUATION_PANEL_SCHEMA = PanelSchema(
    name='valuation_panel',
    description='Latest version only for current valuation',
    columns=_COMMON_COLUMNS,
    primary_key=['ticker', 'end'],
)

BACKTEST_PANEL_SCHEMA = PanelSchema(
    name='backtest_panel',
    description='All filed versions for PIT backtesting',
    columns=_COMMON_COLUMNS,
    primary_key=['ticker', 'end', 'filed'],
)
