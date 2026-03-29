"""
Policy registry for mapping string names to policy factories.

This enables scenarios to be configured with string names (YAML/JSON friendly)
while still instantiating the correct policy classes.
"""

from collections.abc import Callable
from typing import cast, TypedDict

from valuation.policies.discount import DiscountPolicy
from valuation.policies.discount import FixedRate
from valuation.policies.fade import FadePolicy
from valuation.policies.fade import LinearFade
from valuation.policies.growth import AvgOEGrowth
from valuation.policies.growth import FixedGrowth
from valuation.policies.growth import GrowthPolicy
from valuation.policies.maintenance_capex import AvgCapex
from valuation.policies.maintenance_capex import MaintenanceCapexPolicy
from valuation.policies.maintenance_capex import TTMCapex
from valuation.policies.pre_maintenance_oe import AvgCFO
from valuation.policies.pre_maintenance_oe import NormalizedMarginOE
from valuation.policies.pre_maintenance_oe import NormalizedROICOE
from valuation.policies.pre_maintenance_oe import PreMaintenanceOEPolicy
from valuation.policies.pre_maintenance_oe import TTMPreMaintenanceOE
from valuation.policies.shares import AvgShareChange
from valuation.policies.shares import SharePolicy
from valuation.policies.terminal import ExitMultipleTerminal
from valuation.policies.terminal import GordonTerminal
from valuation.policies.terminal import TerminalPolicy
from valuation.scenarios.config import ScenarioConfig


class PolicyBundle(TypedDict):
  """Type-safe bundle of instantiated policies."""
  pre_maint_oe: PreMaintenanceOEPolicy
  maint_capex: MaintenanceCapexPolicy
  growth: GrowthPolicy
  fade: FadePolicy
  shares: SharePolicy
  terminal: TerminalPolicy
  discount: DiscountPolicy


PRE_MAINT_OE_POLICIES: dict[str, Callable[[], PreMaintenanceOEPolicy]] = {
    'ttm': TTMPreMaintenanceOE,
    'avg_3y': AvgCFO,
    'normalized_margin_10p_reinv_20p': lambda: NormalizedMarginOE(
        target_margin=0.10, reinvestment_rate=0.20),
    'normalized_roic_15p_reinv_30p': lambda: NormalizedROICOE(
        target_roic=0.15, reinvestment_rate=0.30),
}

MAINT_CAPEX_POLICIES: dict[str, Callable[[], MaintenanceCapexPolicy]] = {
    'ttm': TTMCapex,
    'avg_3y': AvgCapex,
}

GROWTH_POLICIES: dict[str, Callable[[], GrowthPolicy]] = {
    'fixed_neg0p05': lambda: FixedGrowth(growth_rate=-0.05),
    'fixed_0p00': lambda: FixedGrowth(growth_rate=0.00),
    'fixed_0p02': lambda: FixedGrowth(growth_rate=0.02),
    'fixed_0p03': lambda: FixedGrowth(growth_rate=0.03),
    'fixed_0p05': lambda: FixedGrowth(growth_rate=0.05),
    'fixed_0p06': lambda: FixedGrowth(growth_rate=0.06),
    'fixed_0p07': lambda: FixedGrowth(growth_rate=0.07),
    'fixed_0p08': lambda: FixedGrowth(growth_rate=0.08),
    'fixed_0p10': lambda: FixedGrowth(growth_rate=0.10),
    'fixed_0p12': lambda: FixedGrowth(growth_rate=0.12),
    'fixed_0p15': lambda: FixedGrowth(growth_rate=0.15),
    'avg_oe_3y': lambda: AvgOEGrowth(min_growth=0.0, max_growth=0.20),
    'avg_oe_3y_clip15': lambda: AvgOEGrowth(min_growth=0.0, max_growth=0.15),
}

FADE_POLICIES: dict[str, Callable[[], FadePolicy]] = {
    'linear': lambda: LinearFade(g_end_spread=0.01),
}

SHARE_POLICIES: dict[str, Callable[[], SharePolicy]] = {
    'avg_5y': lambda: AvgShareChange(years=5),
}

TERMINAL_POLICIES: dict[str, Callable[[], TerminalPolicy]] = {
    'gordon_2pct': lambda: GordonTerminal(g_terminal=0.02),
    'gordon': lambda: GordonTerminal(g_terminal=0.03),
    'exit_multiple_5x': lambda: ExitMultipleTerminal(multiple=5.0),
    'exit_multiple_7x': lambda: ExitMultipleTerminal(multiple=7.0),
    'exit_multiple_10x': lambda: ExitMultipleTerminal(multiple=10.0),
}

DISCOUNT_POLICIES: dict[str, Callable[[], DiscountPolicy]] = {
    'fixed_0p10': lambda: FixedRate(rate=0.10),
    'fixed_0p08': lambda: FixedRate(rate=0.08),
    'fixed_0p06': lambda: FixedRate(rate=0.06),
    'fixed_0p12': lambda: FixedRate(rate=0.12),
}

POLICY_REGISTRY = {
    'pre_maint_oe': PRE_MAINT_OE_POLICIES,
    'maint_capex': MAINT_CAPEX_POLICIES,
    'growth': GROWTH_POLICIES,
    'fade': FADE_POLICIES,
    'shares': SHARE_POLICIES,
    'terminal': TERMINAL_POLICIES,
    'discount': DISCOUNT_POLICIES,
}


def create_policies(config: ScenarioConfig) -> PolicyBundle:
  """
  Create policy instances from scenario configuration.

  Args:
    config: ScenarioConfig with policy names

  Returns:
    Dictionary with instantiated policy objects

  Raises:
    KeyError: If a policy name is not found in the registry
  """
  try:
    pre_maint_oe_factory = PRE_MAINT_OE_POLICIES[config.pre_maint_oe]
  except KeyError as e:
    raise KeyError(f"Unknown pre_maint_oe policy: '{config.pre_maint_oe}'. "
                   f'Available: {list(PRE_MAINT_OE_POLICIES.keys())}') from e

  try:
    maint_capex_factory = MAINT_CAPEX_POLICIES[config.maint_capex]
  except KeyError as e:
    raise KeyError(f"Unknown maint_capex policy: '{config.maint_capex}'. "
                   f'Available: {list(MAINT_CAPEX_POLICIES.keys())}') from e

  try:
    growth_factory = GROWTH_POLICIES[config.growth]
  except KeyError as e:
    raise KeyError(f"Unknown growth policy: '{config.growth}'. "
                   f'Available: {list(GROWTH_POLICIES.keys())}') from e

  try:
    fade_factory = FADE_POLICIES[config.fade]
  except KeyError as e:
    raise KeyError(f"Unknown fade policy: '{config.fade}'. "
                   f'Available: {list(FADE_POLICIES.keys())}') from e

  try:
    shares_factory = SHARE_POLICIES[config.shares]
  except KeyError as e:
    raise KeyError(f"Unknown shares policy: '{config.shares}'. "
                   f'Available: {list(SHARE_POLICIES.keys())}') from e

  try:
    terminal_factory = TERMINAL_POLICIES[config.terminal]
  except KeyError as e:
    raise KeyError(f"Unknown terminal policy: '{config.terminal}'. "
                   f'Available: {list(TERMINAL_POLICIES.keys())}') from e

  try:
    discount_factory = DISCOUNT_POLICIES[config.discount]
  except KeyError as e:
    raise KeyError(f"Unknown discount policy: '{config.discount}'. "
                   f'Available: {list(DISCOUNT_POLICIES.keys())}') from e

  return PolicyBundle(
      pre_maint_oe=pre_maint_oe_factory(),
      maint_capex=maint_capex_factory(),
      growth=growth_factory(),
      fade=fade_factory(),
      shares=shares_factory(),
      terminal=terminal_factory(),
      discount=discount_factory(),
  )


def list_policies() -> dict[str, list[str]]:
  """List all available policies by category."""
  result: dict[str, list[str]] = {}
  for category, policies_dict in POLICY_REGISTRY.items():
    policy_dict = cast(dict[str, object], policies_dict)
    result[category] = list(policy_dict.keys())
  return result
