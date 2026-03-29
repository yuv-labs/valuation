"""
Pure DCF math engine.

This module contains pure functions for DCF calculations. No pandas, no I/O,
just numeric computations. All inputs must be prepared before calling these.

Key functions:
  compute_intrinsic_value: Main entry point, computes IV per share
  compute_pv_explicit: PV of explicit forecast period
  compute_terminal_value: Gordon growth terminal value
"""

from collections.abc import Sequence
from math import isfinite


def compute_pv_explicit(
    oe0: float,
    sh0: float,
    buyback_rate: float,
    growth_path: Sequence[float],
    discount_rate: float,
) -> tuple[float, float, float]:
  """
  Compute present value of explicit forecast period.

  Args:
    oe0: Initial owner earnings (absolute, not per share)
    sh0: Initial shares outstanding
    buyback_rate: Annual share reduction rate (b)
    growth_path: Sequence of yearly growth rates [g1, g2, ..., gN]
    discount_rate: Required return (r)

  Returns:
    Tuple of (pv_total, final_oeps, final_shares):
    - pv_total: Total PV of explicit period OE per share
    - final_oeps: OE per share in final year
    - final_shares: Shares outstanding in final year
  """
  pv = 0.0
  oe = oe0
  shares = sh0

  for t, g in enumerate(growth_path, start=1):
    oe *= (1.0 + g)
    shares *= (1.0 - buyback_rate)

    if shares <= 0:
      return float('nan'), float('nan'), 0.0

    oeps = oe / shares
    pv += oeps / ((1.0 + discount_rate)**t)

  final_oeps = oe / shares if shares > 0 else 0.0
  return pv, final_oeps, shares

def compute_terminal_value(
    final_oeps: float,
    g_terminal: float,
    discount_rate: float,
    final_year: int,
    tv_method: str = 'gordon',
    tv_param: float | None = None,
) -> float:
  """
  Compute discounted terminal value using Gordon Growth Model.

  Args:
    final_oeps: OE per share in final explicit year
    g_terminal: Terminal (perpetual) growth rate
    discount_rate: Required return (r)
    final_year: Number of years to discount back

  Returns:
    Present value of terminal value

    Returns nan if method is unknown or invalid params
  """
  if tv_param is None:
    tv_param = g_terminal

  if tv_method == 'gordon':
    if discount_rate <= tv_param:
      return float('nan')
    tv = (final_oeps * (1.0 + tv_param)) / (discount_rate - tv_param)
  elif tv_method == 'multiple':
    tv = final_oeps * tv_param
  else:
    return float('nan')

  discounted_tv = tv / ((1.0 + discount_rate)**final_year)
  return discounted_tv

def compute_intrinsic_value(
    oe0: float,
    sh0: float,
    buyback_rate: float,
    growth_path: Sequence[float],
    g_terminal: float,
    discount_rate: float,
    tv_method: str = 'gordon',
    tv_param: float | None = None,
) -> tuple[float, float, float]:
  """
  Compute intrinsic value per share using two-stage DCF model.

  Stage 1: Explicit forecast period with fading growth and share buybacks
  Stage 2: Terminal value using Gordon Growth Model

  Args:
    oe0: Initial owner earnings (CFO - CAPEX)
    sh0: Current shares outstanding
    buyback_rate: Annual share reduction rate (b)
    growth_path: Sequence of yearly growth rates [g1, g2, ..., gN]
    g_terminal: Perpetual terminal growth rate
    discount_rate: Required return (r)

  Returns:
    Tuple of (iv_per_share, pv_explicit, tv_component):
    - iv_per_share: Total intrinsic value per share
    - pv_explicit: PV contribution from explicit period
    - tv_component: PV contribution from terminal value
  """
  n_years = len(growth_path)

  if not isfinite(oe0) or not isfinite(sh0) or not isfinite(buyback_rate):
    return float('nan'), float('nan'), float('nan')

  if not all(isfinite(g) for g in growth_path):
    return float('nan'), float('nan'), float('nan')

  if not isfinite(discount_rate):
    return float('nan'), float('nan'), float('nan')

  if tv_method == 'gordon':
    if not isfinite(g_terminal) or discount_rate <= g_terminal:
      return float('nan'), float('nan'), float('nan')

  if sh0 <= 0 or n_years < 1:
    return float('nan'), float('nan'), float('nan')

  pv_explicit, final_oeps, _ = compute_pv_explicit(oe0, sh0, buyback_rate,
                                                   growth_path, discount_rate)

  if not isfinite(pv_explicit):
    return float('nan'), float('nan'), float('nan')

  tv_component = compute_terminal_value(final_oeps, g_terminal, discount_rate,
                                        n_years, tv_method, tv_param)

  if not isfinite(tv_component):
    return float('nan'), float('nan'), float('nan')

  iv_per_share = pv_explicit + tv_component
  return iv_per_share, pv_explicit, tv_component
