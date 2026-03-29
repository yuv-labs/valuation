"""
Single-company valuation entrypoint.

This module provides the main entry point for running valuations. It:
1. Loads data and constructs domain slices (PIT-safe)
2. Applies policies from the scenario configuration
3. Runs the DCF engine
4. Returns ValuationResult with full diagnostics

Usage:
  from valuation.run import run_valuation
  from valuation.scenarios.config import ScenarioConfig

  result = run_valuation(
    ticker='GOOGL',
    as_of_date='2024-12-31',
    config=ScenarioConfig.default(),
  )
  print(f"IV: ${result.iv_per_share:.2f}")
"""

import argparse
import logging
from pathlib import Path
from typing import Any, Optional

import pandas as pd

from valuation.data_loader import ValuationDataLoader
from valuation.domain.types import FundamentalsSlice
from valuation.domain.types import MarketSlice
from valuation.domain.types import PreparedInputs
from valuation.domain.types import ValuationResult
from valuation.engine.dcf import compute_intrinsic_value
from valuation.scenarios.config import ScenarioConfig
from valuation.scenarios.registry import create_policies

logger = logging.getLogger(__name__)


def get_price_after_filing(
    ticker: str,
    filed_date: pd.Timestamp,
    loader: ValuationDataLoader,
    market: str = 'us',
) -> MarketSlice:
  """
  Get market price on first trading day after filing date.

  Args:
    ticker: Company ticker symbol
    filed_date: SEC filing date
    loader: Data loader for accessing price data
    market: Market identifier ('us' or 'kr')

  Returns:
    MarketSlice with price and date
  """
  prices = loader.load_prices()

  symbol = ticker if market == 'kr' else f'{ticker}.US'
  ticker_prices = prices[prices['symbol'] == symbol].copy()

  if ticker_prices.empty:
    raise ValueError(f'No price data for {ticker}')

  ticker_prices = ticker_prices.sort_values('date')

  window_end = filed_date + pd.Timedelta(days=7)
  after_filing = ticker_prices[(ticker_prices['date'] > filed_date) &
                               (ticker_prices['date'] <= window_end)]

  if after_filing.empty:
    on_filing = ticker_prices[ticker_prices['date'] == filed_date]
    if not on_filing.empty:
      row = on_filing.iloc[0]
      return MarketSlice(price=float(row['close']), price_date=row['date'])
    raise ValueError(f'No price data for {ticker} around {filed_date.date()}')

  row = after_filing.iloc[0]
  return MarketSlice(price=float(row['close']), price_date=row['date'])


def run_valuation(
    ticker: str,
    as_of_date: str,
    loader: ValuationDataLoader,
    config: Optional[ScenarioConfig] = None,
    include_market_price: bool = True,
    market: str = 'us',
) -> ValuationResult:
  """
  Run valuation for a single ticker at a specific date.

  Args:
    ticker: Company ticker symbol (e.g., 'GOOGL', 'AAPL')
    as_of_date: Point-in-time date for valuation (YYYY-MM-DD)
    loader: Data loader for accessing panel and price data
    config: ScenarioConfig (default: ScenarioConfig.default())
    include_market_price: Whether to fetch and include market price

  Returns:
    ValuationResult with IV, diagnostics, and optional market comparison
  """
  if config is None:
    config = ScenarioConfig.default()

  as_of = pd.Timestamp(as_of_date)

  panel = loader.load_panel()

  data = FundamentalsSlice.from_panel(panel, ticker, as_of)

  policies = create_policies(config)
  all_diag: dict[str, Any] = {
      'scenario': config.name,
      'ticker': ticker,
      'as_of_date': str(as_of.date()),
  }

  pre_maint_oe_result = policies['pre_maint_oe'].compute(data)
  all_diag.update({
      f'pre_maint_oe_{k}': v for k, v in pre_maint_oe_result.diag.items()
  })

  maint_capex_result = policies['maint_capex'].compute(data)
  all_diag.update({
      f'maint_capex_{k}': v for k, v in maint_capex_result.diag.items()
  })

  growth_result = policies['growth'].compute(data)
  all_diag.update({f'growth_{k}': v for k, v in growth_result.diag.items()})

  terminal_result = policies['terminal'].compute()
  all_diag.update({f'terminal_{k}': v for k, v in terminal_result.diag.items()})

  terminal_params = terminal_result.value

  if growth_result.diag.get('below_threshold', False):
    logger.debug('%s: Growth below threshold, using 0%% growth path', ticker)
    growth_path = [0.0] * config.n_years
    all_diag['growth_path_override'] = 'zero_growth'
  else:
    # Determine the terminal growth to fade towards
    fade_g_terminal = (terminal_params.value
                       if terminal_params.method == 'gordon' else 0.02)

    fade_result = policies['fade'].compute(
        g0=growth_result.value,
        g_terminal=fade_g_terminal,
        n_years=config.n_years,
    )
    all_diag.update({f'fade_{k}': v for k, v in fade_result.diag.items()})
    growth_path = fade_result.value

  shares_result = policies['shares'].compute(data)
  all_diag.update({f'shares_{k}': v for k, v in shares_result.diag.items()})

  discount_result = policies['discount'].compute()
  all_diag.update({f'discount_{k}': v for k, v in discount_result.diag.items()})

  # OE = Pre-Maintenance OE - Maintenance CAPEX
  oe0 = pre_maint_oe_result.value - maint_capex_result.value
  sh0 = data.latest_shares

  # Add fundamental data to diagnostics
  all_diag['fundamentals_pre_maint_oe'] = str(pre_maint_oe_result.value)
  all_diag['fundamentals_maint_capex'] = str(maint_capex_result.value)
  all_diag['fundamentals_shares'] = str(data.latest_shares)
  all_diag['fundamentals_oe0'] = str(oe0)
  all_diag['fundamentals_as_of_end'] = str(data.as_of_end.date())
  all_diag['fundamentals_filed'] = str(data.latest_filed.date())

  inputs = PreparedInputs(
      oe0=oe0,
      sh0=sh0,
      buyback_rate=shares_result.value,
      g0=growth_result.value,
      g_terminal=(terminal_params.value
                  if terminal_params.method == 'gordon' else 0.0),
      growth_path=growth_path,
      n_years=config.n_years,
      discount_rate=discount_result.value,
  )

  iv, pv_explicit, tv_component = compute_intrinsic_value(
      oe0=inputs.oe0,
      sh0=inputs.sh0,
      buyback_rate=inputs.buyback_rate,
      growth_path=inputs.growth_path,
      g_terminal=inputs.g_terminal,  # backward compatibility
      discount_rate=inputs.discount_rate,
      tv_method=terminal_params.method,
      tv_param=terminal_params.value,
  )

  market_slice = None
  if include_market_price:
    try:
      market_slice = get_price_after_filing(
          ticker, data.latest_filed, loader, market=market)
      all_diag['price_date'] = str(market_slice.price_date.date())
    except (FileNotFoundError, ValueError) as e:
      all_diag['price_error'] = str(e)

  price_to_iv = None
  margin_of_safety = None
  if market_slice and iv > 0:
    price_to_iv = market_slice.price / iv
    margin_of_safety = (iv - market_slice.price) / iv

  return ValuationResult(
      iv_per_share=iv,
      pv_explicit=pv_explicit,
      tv_component=tv_component,
      market_price=market_slice.price if market_slice else None,
      price_to_iv=price_to_iv,
      margin_of_safety=margin_of_safety,
      inputs=inputs,
      diag=all_diag,
  )


def main() -> None:
  """CLI entrypoint."""
  parser = argparse.ArgumentParser(description='Run DCF valuation')
  parser.add_argument('--ticker',
                      type=str,
                      required=True,
                      help='Company ticker')
  parser.add_argument('--as-of',
                      type=str,
                      required=True,
                      help='As-of date (YYYY-MM-DD)')
  parser.add_argument(
      '--scenario',
      type=str,
      default='default',
      choices=['default'],
      help='Scenario preset',
  )
  parser.add_argument(
      '--gold-path',
      type=Path,
      default=Path('data/gold/out/valuation_panel.parquet'),
      help='Path to Gold panel',
  )
  parser.add_argument(
      '--silver-dir',
      type=Path,
      default=Path('data/silver/out'),
      help='Path to Silver directory',
  )
  parser.add_argument(
      '--market',
      type=str,
      choices=['us', 'kr'],
      default='us',
      help='Market (us or kr)',
  )
  args = parser.parse_args()

  if args.scenario == 'default':
    config = ScenarioConfig.default()
  else:
    raise ValueError(f'Unknown scenario: {args.scenario}. Available: default')

  loader = ValuationDataLoader(
      gold_path=args.gold_path,
      silver_dir=args.silver_dir,
  )

  result = run_valuation(
      ticker=args.ticker,
      as_of_date=args.as_of,
      loader=loader,
      config=config,
      market=args.market,
  )

  separator = '=' * 70
  logger.info('\n%s', separator)
  logger.info('DCF Valuation - %s as of %s', args.ticker, args.as_of)
  logger.info('Scenario: %s', config.name)
  logger.info(separator)

  if result.inputs:
    logger.info('\nPrepared Inputs:')
    logger.info('  OE0: $%s', f'{result.inputs.oe0:,.0f}')
    logger.info('  Shares: %s', f'{result.inputs.sh0:,.0f}')
    logger.info('  Buyback Rate: %.2f%%', result.inputs.buyback_rate * 100)
    logger.info('  Initial Growth (g0): %.2f%%', result.inputs.g0 * 100)
    logger.info('  Terminal Growth (gT): %.2f%%',
                result.inputs.g_terminal * 100)
    logger.info('  Discount Rate (r): %.2f%%',
                result.inputs.discount_rate * 100)

  logger.info('\nValuation Result:')
  logger.info('  Intrinsic Value: $%.2f', result.iv_per_share)
  logger.info('  PV Explicit: $%.2f', result.pv_explicit)
  logger.info('  TV Component: $%.2f', result.tv_component)

  if result.market_price:
    logger.info('\nMarket Comparison:')
    logger.info('  Market Price: $%.2f', result.market_price)
    if result.price_to_iv is not None:
      logger.info('  Price/IV: %.2f%%', result.price_to_iv * 100)
    if result.margin_of_safety is not None:
      logger.info('  Margin of Safety: %.2f%%', result.margin_of_safety * 100)

  logger.info('%s\n', separator)


if __name__ == '__main__':
  logging.basicConfig(
      level=logging.INFO,
      format='%(message)s',
  )
  main()
