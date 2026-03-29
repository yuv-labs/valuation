"""
Compare intrinsic values using different scenario configs.

Creates charts showing IV from different scenarios vs market price.
Uses JSON config files for flexible scenario comparison.

Usage:
  # Using specific config files
  python -m valuation.analysis.plot_prices \\
      --ticker AAPL \\
      --configs scenarios/capex_experiments/*.json \\
      --start-date 2020-01-01

  # Using config directory
  python -m valuation.analysis.plot_prices \\
      --ticker GOOGL \\
      --config-dir scenarios/discount_experiments \\
      --output-dir charts/discount_comparison

  # Multiple tickers with configs
  python -m valuation.analysis.plot_prices \\
      --tickers AAPL GOOGL META MSFT \\
      --config-dir scenarios/capex_experiments
"""

import argparse
from concurrent.futures import as_completed
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Optional

import matplotlib

matplotlib.use('Agg')
from matplotlib.figure import Figure  # pylint: disable=wrong-import-position
import matplotlib.pyplot as plt  # pylint: disable=wrong-import-position
import pandas as pd  # pylint: disable=wrong-import-position

# pylint: disable=wrong-import-position
from valuation.data_loader import ValuationDataLoader
from valuation.domain.types import FundamentalsSlice
from valuation.engine.dcf import compute_intrinsic_value
from valuation.run import get_price_after_filing
from valuation.scenarios.config import ScenarioConfig
from valuation.scenarios.registry import create_policies

# pylint: enable=wrong-import-position

logger = logging.getLogger(__name__)


def _get_price_at_date(ticker_prices: pd.DataFrame,
                       target_date: pd.Timestamp) -> Optional[float]:
  """Get closing price at or before target_date."""
  valid = ticker_prices[ticker_prices['date'] <= target_date]
  if valid.empty:
    return None
  return float(valid.iloc[-1]['close'])


def find_common_and_different_policies(
    scenarios: list[ScenarioConfig]
) -> tuple[dict[str, str], list[dict[str, str]]]:
  """
  Find common policies across scenarios and what differs.

  Returns:
    (common_policies, different_policies_per_scenario)
  """
  if not scenarios:
    return {}, []

  policy_fields = [
      'pre_maint_oe', 'maint_capex', 'growth', 'fade', 'shares', 'terminal',
      'discount'
  ]
  common: dict[str, str] = {}
  different_per_scenario: list[dict[str, str]] = [{} for _ in scenarios]

  for field in policy_fields:
    values = [getattr(s, field) for s in scenarios]
    if len(set(values)) == 1:
      common[field] = values[0]
    else:
      for idx, value in enumerate(values):
        different_per_scenario[idx][field] = value

  n_years_values = [s.n_years for s in scenarios]
  if len(set(n_years_values)) == 1:
    common['n_years'] = f'{n_years_values[0]}y'
  else:
    for idx, value in enumerate(n_years_values):
      different_per_scenario[idx]['n_years'] = f'{value}y'

  return common, different_per_scenario


def get_policy_display_name(key: str) -> str:
  """Get short display name for a policy key."""
  names = {
      'pre_maint_oe': 'pre_oe',
      'maint_capex': 'capex',
      'discount': 'disc',
      'growth': 'growth',
      'fade': 'fade',
      'shares': 'shares',
      'terminal': 'term',
      'n_years': 'years',
  }
  return names.get(key, key)


def create_short_label(different_policies: dict[str, str],
                       scenario_name: str) -> str:
  """Create short label showing only different policies."""
  if not different_policies:
    return scenario_name

  parts = []
  for key in [
      'pre_maint_oe', 'maint_capex', 'discount', 'growth', 'fade', 'shares',
      'terminal', 'n_years'
  ]:
    if key in different_policies:
      parts.append(different_policies[key])

  return ' | '.join(parts) if parts else scenario_name


def create_legend_header(different_policies_list: list[dict[str, str]]) -> str:
  """Create column header for legend entries."""
  if not different_policies_list or not different_policies_list[0]:
    return ''

  keys_order = [
      'pre_maint_oe', 'maint_capex', 'discount', 'growth', 'fade', 'shares',
      'terminal', 'n_years'
  ]
  header_parts = []
  for key in keys_order:
    if key in different_policies_list[0]:
      header_parts.append(get_policy_display_name(key))

  return ' | '.join(header_parts)


def create_fixed_policies_text(common_policies: dict[str, str]) -> str:
  """Create text showing fixed/common policies."""
  if not common_policies:
    return ''

  common_parts = []
  for key in [
      'pre_maint_oe', 'maint_capex', 'discount', 'growth', 'fade', 'shares',
      'terminal', 'n_years'
  ]:
    if key in common_policies:
      display_name = get_policy_display_name(key)
      common_parts.append(f'{display_name}={common_policies[key]}')

  return '[fixed] ' + ', '.join(common_parts) if common_parts else ''


def load_configs_from_files(config_paths: list[Path]) -> list[ScenarioConfig]:
  """Load scenario configs from JSON files."""
  configs = []
  for path in config_paths:
    try:
      with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
      config = ScenarioConfig.from_dict(data)
      configs.append(config)
      logger.info('Loaded config: %s from %s', config.name, path.name)
    except Exception as e:  # pylint: disable=broad-except
      print(f'Error on {path}: {e}')
      logger.error('Failed to load %s: %s', path, e)
  return configs


def load_configs_from_dir(config_dir: Path) -> list[ScenarioConfig]:
  """Load all JSON configs from a directory."""
  json_files = sorted(config_dir.glob('*.json'))
  return load_configs_from_files(json_files)


def calculate_iv_for_date(
    panel: pd.DataFrame,
    ticker: str,
    as_of_date: pd.Timestamp,
    scenario: ScenarioConfig,
    loader: ValuationDataLoader,
    market: str = 'us',
) -> Optional[dict[str, Any]]:
  """
  Calculate IV for a single date using a specific scenario.

  Args:
      panel: Full Gold panel (split-adjusted)
      ticker: Company ticker
      as_of_date: As-of date for PIT filtering
      scenario: ScenarioConfig with policy settings
      loader: Data loader for accessing price data

  Returns:
      Dict with iv, growth, diagnostics or None if calculation fails
  """
  try:
    fundamentals = FundamentalsSlice.from_panel(
        panel=panel,
        ticker=ticker,
        as_of_date=as_of_date,
    )
  except (ValueError, KeyError):
    return None

  policies = create_policies(scenario)

  pre_maint_oe_result = policies['pre_maint_oe'].compute(fundamentals)
  if pd.isna(pre_maint_oe_result.value):
    return None

  maint_capex_result = policies['maint_capex'].compute(fundamentals)
  if pd.isna(maint_capex_result.value):
    return None

  oe0 = pre_maint_oe_result.value - maint_capex_result.value

  growth_result = policies['growth'].compute(fundamentals)

  if pd.isna(growth_result.value) or growth_result.diag.get(
      'below_threshold', False):
    return {
        'iv': 0.0,
        'growth': 0.0,
        'oe0': oe0,
        'shares': fundamentals.latest_shares,
        'buyback': 0.0,
        'market_price': None,
        'pv_explicit': 0.0,
        'terminal_value': 0.0,
    }

  terminal_result = policies['terminal'].compute()
  terminal_params = terminal_result.value
  fade_g_terminal = (terminal_params.value
                     if terminal_params.method == 'gordon' else 0.02)

  fade_result = policies['fade'].compute(
      g0=growth_result.value,
      g_terminal=fade_g_terminal,
      n_years=scenario.n_years,
  )

  shares_result = policies['shares'].compute(fundamentals)
  sh0 = fundamentals.latest_shares
  buyback_rate = shares_result.value

  discount_result = policies['discount'].compute()
  discount_rate = discount_result.value

  iv, pv_explicit, tv = compute_intrinsic_value(
      oe0=oe0,
      sh0=sh0,
      buyback_rate=buyback_rate,
      growth_path=fade_result.value,
      g_terminal=(terminal_params.value
                  if terminal_params.method == 'gordon' else 0.0),
      discount_rate=discount_rate,
      tv_method=terminal_params.method,
      tv_param=terminal_params.value,
  )

  if pd.isna(iv):
    return None

  display_iv = max(0.0, iv)

  try:
    market_slice = get_price_after_filing(
        ticker, fundamentals.latest_filed, loader,
        market=market)
    market_price = market_slice.price
  except (FileNotFoundError, ValueError):
    market_price = None

  return {
      'iv': display_iv,
      'growth': growth_result.value,
      'oe0': oe0,
      'shares': sh0,
      'buyback': buyback_rate,
      'market_price': market_price,
      'pv_explicit': pv_explicit,
      'terminal_value': tv,
  }


def plot_scenario_comparison(
    ticker: str,
    panel: pd.DataFrame,
    scenarios: list[ScenarioConfig],
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
    output_dir: Path,
    loader: ValuationDataLoader,
    month_interval: int = 3,
    market: str = 'us',
) -> None:
  """Plot IV comparison for different scenarios vs market price."""
  ticker_panel = panel[panel['ticker'] == ticker].copy()

  if ticker_panel.empty:
    logger.warning('No data for %s', ticker)
    return

  ticker_panel = ticker_panel.sort_values('end')
  ticker_panel = ticker_panel[(ticker_panel['end'] >= start_date) &
                              (ticker_panel['end'] <= end_date)]

  if len(ticker_panel) < 4:
    logger.warning('Insufficient data for %s', ticker)
    return

  if not scenarios:
    logger.error('No scenarios provided')
    return

  freq = f'{month_interval}ME' if month_interval > 1 else 'ME'
  backtest_dates = pd.date_range(start=start_date, end=end_date, freq=freq)

  results: dict[str, list] = {'dates': [], 'market_price': []}
  for scenario in scenarios:
    results[scenario.name] = []

  logger.info(
      'Calculating IVs for %d scenarios across %d dates (%d-month interval)...',
      len(scenarios), len(backtest_dates), month_interval)

  prices = loader.load_prices()
  symbol = ticker if market == 'kr' else f'{ticker}.US'
  ticker_prices = prices[prices['symbol'] == symbol].sort_values('date')

  for as_of_date in backtest_dates:
    market_price = _get_price_at_date(ticker_prices, as_of_date)
    if market_price is None:
      continue

    scenario_ivs: dict[str, Optional[float]] = {}

    for scenario in scenarios:
      result = calculate_iv_for_date(
          panel, ticker, as_of_date, scenario, loader,
          market=market)
      if result:
        scenario_ivs[scenario.name] = result['iv']
      else:
        scenario_ivs[scenario.name] = None

    results['dates'].append(as_of_date)
    results['market_price'].append(market_price)
    for scenario in scenarios:
      results[scenario.name].append(scenario_ivs.get(scenario.name))

  if len(results['dates']) == 0:
    logger.warning('No valid results for %s', ticker)
    return

  iv_count = sum(1 for i in range(len(results['dates']))
                 if any(results[s.name][i] is not None for s in scenarios))
  logger.info('Generated %d dates (%d with IV data)', len(results['dates']),
              iv_count)

  common_policies, different_policies = find_common_and_different_policies(
      scenarios)

  fig = Figure(figsize=(14, 8))
  ax = fig.add_subplot(111)

  markers = ['o', 's', '^', 'v', 'D', 'p', '*', 'X', 'P', 'h']
  colors = plt.colormaps['tab10'].colors  # type: ignore[attr-defined]

  for idx, scenario in enumerate(scenarios):
    marker = markers[idx % len(markers)]
    color = colors[idx % len(colors)]

    short_label = create_short_label(different_policies[idx], scenario.name)

    iv_series = pd.Series(results[scenario.name], index=results['dates'])
    valid_mask = iv_series.notna()
    if valid_mask.any():
      ax.plot(iv_series.index[valid_mask],
              iv_series[valid_mask],
              marker=marker,
              linestyle='-',
              label=short_label,
              linewidth=2,
              markersize=6,
              alpha=0.8,
              color=color)

  ax.plot(results['dates'],
          results['market_price'],
          'D-',
          label='Market Price',
          linewidth=2.5,
          markersize=7,
          color='red',
          alpha=1.0)

  ax.set_xlabel('Quarter End Date', fontsize=12, fontweight='bold')
  currency_symbol = '₩' if market == 'kr' else '$'
  ax.set_ylabel(
      f'Price per Share ({currency_symbol})', fontsize=12, fontweight='bold')

  title = f'{ticker} - Intrinsic Value Comparison vs Market Price'
  ax.set_title(title, fontsize=14, fontweight='bold', pad=20)

  fixed_text = create_fixed_policies_text(common_policies)
  if fixed_text:
    ax.text(0.5,
            0.98,
            fixed_text,
            transform=ax.transAxes,
            ha='center',
            va='top',
            fontsize=9,
            family='monospace',
            fontweight='bold',
            color='#333333',
            bbox={
                'facecolor': 'white',
                'alpha': 0.9,
                'edgecolor': '#888888',
                'boxstyle': 'round,pad=0.3'
            })

  legend = ax.legend(loc='upper left',
                     fontsize=9,
                     framealpha=0.95,
                     bbox_to_anchor=(0, 0.92))

  legend_header = create_legend_header(different_policies)
  if legend_header:
    legend.set_title(legend_header, prop={'size': 8, 'family': 'monospace'})
    legend.get_title().set_ha('center')

  ax.grid(True, alpha=0.3, linestyle='--')

  fig.tight_layout()

  scenario_names = '__'.join([s.name for s in scenarios])
  scenario_hash = hashlib.md5(scenario_names.encode()).hexdigest()[:8]
  n_scenarios = len(scenarios)

  filename = f'{ticker}__comparison__{n_scenarios}scenarios_{scenario_hash}.png'
  output_path = output_dir / filename
  fig.savefig(output_path, dpi=150, bbox_inches='tight')
  logger.info('Saved: %s', output_path)


def main() -> None:
  """CLI entrypoint for scenario comparison analysis."""
  parser = argparse.ArgumentParser(
      description='Compare IVs from different scenario configs',
      formatter_class=argparse.RawDescriptionHelpFormatter,
      epilog="""
Examples:
  # Using config files
  python -m valuation.analysis.plot_prices \\
      --ticker AAPL \\
      --configs scenarios/capex_experiments/*.json

  # Using config directory
  python -m valuation.analysis.plot_prices \\
      --ticker GOOGL \\
      --config-dir scenarios/discount_experiments

  # Multiple tickers
  python -m valuation.analysis.plot_prices \\
      --tickers AAPL GOOGL META \\
      --config-dir scenarios/capex_experiments \\
      --output-dir charts/comparison
      """)

  parser.add_argument('--ticker', type=str, help='Single ticker to analyze')
  parser.add_argument('--tickers',
                      nargs='+',
                      help='Multiple tickers (e.g., AAPL GOOGL META)')
  parser.add_argument('--tickers-file',
                      type=Path,
                      help='Path to file with ticker list')

  config_group = parser.add_mutually_exclusive_group(required=True)
  config_group.add_argument('--configs',
                            nargs='+',
                            type=Path,
                            help='Config file paths')
  config_group.add_argument('--config-dir',
                            type=Path,
                            help='Directory with config files')

  parser.add_argument('--start-date',
                      default='2020-01-01',
                      help='Start date (YYYY-MM-DD)')
  parser.add_argument('--end-date',
                      default='2025-12-31',
                      help='End date (YYYY-MM-DD)')
  parser.add_argument('--output-dir',
                      type=Path,
                      default=Path('output/analysis/price_charts'),
                      help='Output directory for charts')
  parser.add_argument('--gold-path',
                      type=Path,
                      default=Path('data/gold/out/backtest_panel.parquet'),
                      help='Path to Gold panel')
  parser.add_argument('--silver-dir',
                      type=Path,
                      default=Path('data/silver/out'),
                      help='Path to Silver directory')
  parser.add_argument('--market',
                      type=str,
                      choices=['us', 'kr'],
                      default='us',
                      help='Market (us or kr)')
  parser.add_argument('--month-interval',
                      type=int,
                      default=3,
                      help='Backtest interval in months (default: 3)')
  parser.add_argument('--concurrency',
                      type=int,
                      default=1,
                      help='Number of parallel workers (default: 1)')
  parser.add_argument('--verbose',
                      '-v',
                      action='store_true',
                      help='Verbose output')

  args = parser.parse_args()

  logging.basicConfig(
      level=logging.DEBUG if args.verbose else logging.INFO,
      format='%(asctime)s [%(levelname)s] %(message)s',
      datefmt='%Y-%m-%d %H:%M:%S',
  )

  if args.configs:
    configs = load_configs_from_files(args.configs)
  else:
    configs = load_configs_from_dir(args.config_dir)

  if not configs:
    logger.error('No valid configs loaded')
    return

  logger.info('Loaded %d scenarios', len(configs))

  if args.ticker:
    tickers = [args.ticker]
  elif args.tickers_file:
    if not args.tickers_file.exists():
      raise FileNotFoundError(f'File not found: {args.tickers_file}')

    with open(args.tickers_file, 'r', encoding='utf-8') as f:
      tickers = [
          line.strip()
          for line in f
          if line.strip() and not line.strip().startswith('#')
      ]

    if not tickers:
      raise ValueError('No tickers found in file')

    logger.info('Loaded %d tickers from %s', len(tickers), args.tickers_file)
  elif args.tickers:
    tickers = args.tickers
  else:
    logger.error('Must specify --ticker, --tickers, or --tickers-file')
    return

  args.output_dir.mkdir(parents=True, exist_ok=True)

  logger.info('Loading data from: %s', args.gold_path)
  loader = ValuationDataLoader(
      gold_path=args.gold_path,
      silver_dir=args.silver_dir,
  )
  panel = loader.load_panel()

  start = pd.Timestamp(args.start_date)
  end = pd.Timestamp(args.end_date)

  logger.info('Analyzing %d companies: %s', len(tickers), ', '.join(tickers))
  logger.info('Period: %s to %s', args.start_date, args.end_date)
  logger.info('Scenarios: %s', [c.name for c in configs])

  def process_ticker(ticker: str) -> str:
    plot_scenario_comparison(
        ticker=ticker,
        panel=panel,
        scenarios=configs,
        start_date=start,
        end_date=end,
        output_dir=args.output_dir,
        loader=loader,
        month_interval=args.month_interval,
        market=args.market,
    )
    return ticker

  if args.concurrency > 1:
    logger.info('Using %d parallel workers', args.concurrency)
    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
      futures = {executor.submit(process_ticker, t): t for t in tickers}
      for future in as_completed(futures):
        future.result()
        ticker = futures[future]
        logger.info('Completed: %s', ticker)
  else:
    for ticker in tickers:
      logger.info('Processing %s...', ticker)
      process_ticker(ticker)

  logger.info('All charts saved to: %s', args.output_dir)


if __name__ == '__main__':
  main()
