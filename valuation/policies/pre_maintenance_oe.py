"""
Pre-Maintenance Owner Earnings estimation policies.

Pre-Maintenance OE represents the cash earnings before deducting maintenance
capital expenditures. CFO (Cash Flow from Operations) is used as an
approximation of this value.

Final Owner Earnings = Pre-Maintenance OE - Maintenance CAPEX
"""

from abc import ABC
from abc import abstractmethod

from valuation.domain.types import FundamentalsSlice
from valuation.domain.types import PolicyOutput


class PreMaintenanceOEPolicy(ABC):
  """
  Base class for Pre-Maintenance Owner Earnings policies.

  Pre-Maintenance OE is the cash earnings before subtracting maintenance
  capital requirements. CFO is the most common approximation.
  """

  @abstractmethod
  def compute(self, data: FundamentalsSlice) -> PolicyOutput[float]:
    """
    Compute Pre-Maintenance Owner Earnings.

    Args:
      data: Point-in-time fundamental data slice

    Returns:
      PolicyOutput with pre-maintenance OE value and diagnostics
    """


class TTMPreMaintenanceOE(PreMaintenanceOEPolicy):
  """
  Standard TTM-based Pre-Maintenance Owner Earnings.

  Uses CFO_TTM (Trailing Twelve Months Cash Flow from Operations).
  """

  def compute(self, data: FundamentalsSlice) -> PolicyOutput[float]:
    """Return TTM CFO as pre-maintenance OE."""
    cfo_ttm = data.latest_cfo_ttm

    return PolicyOutput(value=cfo_ttm,
                        diag={
                            'pre_maint_oe_method': 'ttm',
                            'cfo_ttm': cfo_ttm,
                        })


class AvgCFO(PreMaintenanceOEPolicy):
  """
  Weighted average CFO over 3 years with 3:2:1 weights.

  Buckets quarters by years ago from as_of_date:
    - Year 1: 0 ~ 1.25 years ago (weight 3)
    - Year 2: 1.25 ~ 2.25 years ago (weight 2)
    - Year 3: 2.25 ~ 3.25 years ago (weight 1)

  Falls back to TTM if insufficient data.
  """

  def compute(self, data: FundamentalsSlice) -> PolicyOutput[float]:
    """Return weighted 3-year average of TTM CFO."""
    weighted_avg, diag = data.weighted_yearly_avg('cfo_ttm')

    if weighted_avg is None:
      return PolicyOutput(value=data.latest_cfo_ttm,
                          diag={
                              'pre_maint_oe_method': 'weighted_avg_3y',
                              'fallback': 'ttm',
                              'pre_maint_oe': data.latest_cfo_ttm,
                              **diag,
                          })

    return PolicyOutput(value=weighted_avg,
                        diag={
                            'pre_maint_oe_method': 'weighted_avg_3y',
                            'pre_maint_oe': weighted_avg,
                            **diag,
                        })

class NormalizedMarginOE(PreMaintenanceOEPolicy):
  """
  Normalized Pre-Maintenance OE based on long-term average margin.
  FCF = Revenue * Target Margin * (1 - Reinvestment Rate)
  """

  def __init__(self, target_margin: float, reinvestment_rate: float):
    self.target_margin = target_margin
    self.reinvestment_rate = reinvestment_rate

  def compute(self, data: FundamentalsSlice) -> PolicyOutput[float]:
    revenue = data.latest_revenue
    normalized_nopat = revenue * self.target_margin
    normalized_fcf = normalized_nopat * (1.0 - self.reinvestment_rate)

    return PolicyOutput(
        value=normalized_fcf,
        diag={
            'pre_maint_oe_method': 'normalized_margin',
            'target_margin': self.target_margin,
            'reinvestment_rate': self.reinvestment_rate,
            'normalized_nopat': normalized_nopat,
            'latest_revenue': revenue,
        })


class NormalizedROICOE(PreMaintenanceOEPolicy):
  """
  Normalized Pre-Maintenance OE based on target ROIC and invested capital.
  FCF = Invested Capital * Target ROIC * (1 - Reinvestment Rate)
  """

  def __init__(self, target_roic: float, reinvestment_rate: float):
    self.target_roic = target_roic
    self.reinvestment_rate = reinvestment_rate

  def compute(self, data: FundamentalsSlice) -> PolicyOutput[float]:
    ic = data.latest_invested_capital
    normalized_nopat = ic * self.target_roic
    normalized_fcf = normalized_nopat * (1.0 - self.reinvestment_rate)

    return PolicyOutput(
        value=normalized_fcf,
        diag={
            'pre_maint_oe_method': 'normalized_roic',
            'target_roic': self.target_roic,
            'reinvestment_rate': self.reinvestment_rate,
            'normalized_nopat': normalized_nopat,
            'latest_invested_capital': ic,
        })
