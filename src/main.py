"""
Main CLI entry point for stock screening tool.
"""
import argparse
import logging
from datetime import datetime
from pathlib import Path
import sys
from typing import Dict

from .config import config
from .utils import setup_logging, load_stock_universe
from .cache import StockCache
from .data_fetcher import DataFetcher
from .indicators import IndicatorCalculator
from .ranking import StockRanker
from .reporting import Reporter
from .backtest import BacktestRunner
from .visualization import BacktestVisualizer


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="US Stock Screening & Observation CLI Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Screening mode (default)
  python -m src.main --mode screen --universe stock_pool/sp500.csv
  python -m src.main --universe stock_pool/sp500.csv --top 30

  # Backtest mode
  python -m src.main --mode backtest --universe stock_pool/sp500.csv --top 10
  python -m src.main --mode backtest --universe stock_pool/sp500.csv --start-date 2010-01-01 --tx-cost-bps 10
        """
    )
    
    parser.add_argument(
        '--mode',
        type=str,
        default='screen',
        choices=['screen', 'backtest'],
        help='Mode: screen (current screening) or backtest (historical simulation)'
    )
    
    parser.add_argument(
        '--universe',
        type=str,
        default='stock_pool/sp500.csv',
        help='Path to stock universe CSV file (default: stock_pool/sp500.csv)'
    )
    
    parser.add_argument(
        '--top',
        type=int,
        default=config.top_overall,
        help=f'Number of top stocks to display (default: {config.top_overall})'
    )
    
    parser.add_argument(
        '--start-date',
        type=str,
        default=config.start_date,
        help=f'Start date for historical data YYYY-MM-DD (default: {config.start_date})'
    )
    
    parser.add_argument(
        '--refresh',
        action='store_true',
        help='Force refresh all data (bypass cache)'
    )
    
    parser.add_argument(
        '--benchmark',
        type=str,
        default=config.benchmark_symbol,
        help=f'Benchmark symbol (default: {config.benchmark_symbol})'
    )
    
    parser.add_argument(
        '--log-level',
        type=str,
        default=config.log_level,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level (default: INFO)'
    )
    
    parser.add_argument(
        '--no-progress',
        action='store_true',
        help='Disable progress bar'
    )
    
    # Backtest-specific arguments
    parser.add_argument(
        '--tx-cost-bps',
        type=float,
        default=0.0,
        help='Transaction cost in basis points for backtest (default: 0)'
    )
    
    return parser.parse_args()


def main():
    """Main execution flow."""
    args = parse_args()
    
    # Setup logging
    logger = setup_logging(args.log_level)
    
    # Route to backtest or screening mode
    if args.mode == 'backtest':
        logger.info("Starting backtest mode")
        run_backtest(args, logger)
    else:
        logger.info("Starting stock screening tool")
        run_screening(args, logger)


def run_backtest(args, logger):
    """Run backtest mode."""
    try:
        # Resolve universe file path
        universe_path = Path(args.universe)
        if not universe_path.is_absolute():
            universe_path = config.project_root / universe_path
        
        if not universe_path.exists():
            logger.error(f"Universe file not found: {universe_path}")
            print(f"Error: Universe file not found: {universe_path}")
            sys.exit(1)
        
        # Load stock universe
        logger.info(f"Loading stock universe from {universe_path}")
        symbols = load_stock_universe(universe_path)
        
        if not symbols:
            logger.error("No symbols loaded from universe file")
            sys.exit(1)
        
        # Initialize components
        cache = StockCache(config.cache_db_path)
        fetcher = DataFetcher(cache, start_date=args.start_date)
        calculator = IndicatorCalculator(
            momentum_6m_days=config.momentum_6m_days,
            momentum_12m_days=config.momentum_12m_days,
            ma_short=config.ma_short,
            ma_long=config.ma_long
        )
        ranker = StockRanker(
            weight_6m=config.weight_6m_momentum,
            weight_12m=config.weight_12m_momentum,
            weight_ma200=config.weight_above_ma200,
            weight_vol=config.weight_volatility
        )
        reporter = Reporter(config.output_dir)
        visualizer = BacktestVisualizer(config.output_dir)
        
        # Print header
        print("\n" + "=" * 80)
        print("MONTHLY ROTATION BACKTEST")
        print("=" * 80)
        print(f"Universe: {len(symbols)} stocks from {universe_path.name}")
        print(f"Portfolio Size: Top {args.top} (equal-weight)")
        print(f"Start Date: {args.start_date}")
        print(f"Regime Filter: ENABLED (SPY < MA200 → Cash)")
        print(f"Transaction Cost: {args.tx_cost_bps} bps")
        print("=" * 80)
        print()
        
        # Fetch benchmark data (required for backtest)
        logger.info(f"Fetching benchmark data: {args.benchmark}")
        benchmark_df = fetcher.fetch_benchmark(
            args.benchmark,
            start_date=args.start_date,
            force_refresh=args.refresh
        )
        
        if benchmark_df is None or benchmark_df.empty:
            logger.error(f"Benchmark data required for backtest")
            print("Error: Could not fetch benchmark data. Backtest requires SPY data.")
            sys.exit(1)
        
        # Fetch stock data
        logger.info(f"Fetching data for {len(symbols)} stocks...")
        stock_data = fetcher.fetch_multiple(
            symbols,
            start_date=args.start_date,
            force_refresh=args.refresh,
            show_progress=not args.no_progress
        )
        
        if not stock_data:
            logger.error("No stock data could be fetched")
            print("Error: Could not fetch any stock data.")
            sys.exit(1)
        
        logger.info(f"Successfully fetched {len(stock_data)} stocks")
        
        # Initialize and run backtest
        backtest_runner = BacktestRunner(
            calculator=calculator,
            ranker=ranker,
            output_dir=config.output_dir
        )
        
        logger.info("Running backtest simulation...")
        results = backtest_runner.run(
            stock_data=stock_data,
            benchmark_data=benchmark_df,
            top_n=args.top,
            regime_filter=True,  # Always enabled
            tx_cost_bps=args.tx_cost_bps
        )
        
        if not results:
            logger.error("Backtest failed")
            print("Error: Backtest simulation failed.")
            sys.exit(1)
        
        # Print results
        summary = results['summary']
        print_backtest_summary(summary)
        
        # Print files saved
        print("\n" + "=" * 80)
        print("BACKTEST FILES SAVED")
        print("=" * 80)
        print(f"Monthly Returns: {results['returns_file']}")
        print(f"Summary (JSON):  {results['summary_file']}")
        if results.get('chart_file'):
            print(f"Equity Curve:    {results['chart_file']}")
        print("=" * 80)
        print()
        
        logger.info("Backtest completed successfully")
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        print("\nInterrupted by user")
        sys.exit(0)
    
    except Exception as e:
        logger.error(f"Fatal error in backtest: {e}", exc_info=True)
        print(f"Error: {e}")
        sys.exit(1)


def print_backtest_summary(summary: Dict):
    """Print backtest summary to console."""
    print("\n" + "=" * 80)
    print("BACKTEST PERFORMANCE SUMMARY")
    print("=" * 80)
    
    print(f"\n{'Period':40} {'Value':>15}")
    print("-" * 80)
    print(f"{'Start Date':40} {summary['start_date']:>15}")
    print(f"{'End Date':40} {summary['end_date']:>15}")
    print(f"{'Duration (years)':40} {summary['years']:>14.2f}")
    print(f"{'Number of Months':40} {summary['n_months']:>15}")
    
    print(f"\n{'Portfolio Performance':40} {'Value':>15}")
    print("-" * 80)
    print(f"{'Total Return':40} {summary['total_return']:>14.2%}")
    print(f"{'CAGR':40} {summary['cagr']:>14.2%}")
    print(f"{'Annualized Volatility':40} {summary['annualized_volatility']:>14.2%}")
    print(f"{'Sharpe Ratio (0% RF)':40} {summary['sharpe_ratio']:>14.2f}")
    print(f"{'Maximum Drawdown':40} {summary['max_drawdown']:>14.2%}")
    
    print(f"\n{'Monthly Statistics':40} {'Value':>15}")
    print("-" * 80)
    print(f"{'Win Rate':40} {summary['win_rate']:>14.2%}")
    print(f"{'Best Month':40} {summary['best_month']:>14.2%}")
    print(f"{'Worst Month':40} {summary['worst_month']:>14.2%}")
    print(f"{'% Months in Cash':40} {summary['pct_months_in_cash']:>14.2%}")
    
    print(f"\n{'Benchmark (SPY) Comparison':40} {'Value':>15}")
    print("-" * 80)
    print(f"{'SPY Total Return':40} {summary['spy_total_return']:>14.2%}")
    print(f"{'SPY CAGR':40} {summary['spy_cagr']:>14.2%}")
    print(f"{'Outperformance':40} {summary['outperformance']:>14.2%}")
    
    print("=" * 80)


def run_screening(args, logger):
    """Run stock screening mode."""
    try:
        # Initialize config
        config = Config()
        
        # Resolve universe file path
        universe_path = Path(args.universe)
        if not universe_path.is_absolute():
            universe_path = Path.cwd() / universe_path
        
        if not universe_path.exists():
            logger.error(f"Universe file not found: {universe_path}")
            print(f"Error: Universe file not found: {universe_path}")
            sys.exit(1)
        
        # Load stock universe
        logger.info(f"Loading stock universe from {universe_path}")
        symbols = load_stock_universe(universe_path)
        
        if not symbols:
            logger.error("No symbols loaded from universe file")
            sys.exit(1)
        
        # Initialize components
        cache = StockCache(config.cache_db_path)
        fetcher = DataFetcher(cache, start_date=args.start_date)
        calculator = IndicatorCalculator(
            momentum_6m_days=config.momentum_6m_days,
            momentum_12m_days=config.momentum_12m_days,
            ma_short=config.ma_short,
            ma_long=config.ma_long
        )
        ranker = StockRanker(
            weight_6m=config.weight_6m_momentum,
            weight_12m=config.weight_12m_momentum,
            weight_ma200=config.weight_above_ma200,
            weight_vol=config.weight_volatility
        )
        reporter = Reporter(config.output_dir)
        
        # Print report header
        reporter.print_report_header(
            universe_file=universe_path.name,
            n_symbols=len(symbols)
        )
        
        # Fetch benchmark data
        logger.info(f"Fetching benchmark data: {args.benchmark}")
        benchmark_df = fetcher.fetch_benchmark(
            args.benchmark,
            start_date=args.start_date,
            force_refresh=args.refresh
        )
        
        if benchmark_df is None or benchmark_df.empty:
            logger.warning(f"Could not fetch benchmark {args.benchmark}, continuing without relative strength")
            benchmark_df = None
        
        # Fetch stock data
        logger.info(f"Fetching data for {len(symbols)} stocks...")
        stock_data = fetcher.fetch_multiple(
            symbols,
            start_date=args.start_date,
            force_refresh=args.refresh,
            show_progress=not args.no_progress
        )
        
        if not stock_data:
            logger.error("No stock data could be fetched")
            print("Error: Could not fetch any stock data. Check your internet connection and try again.")
            sys.exit(1)
        
        logger.info(f"Successfully fetched {len(stock_data)} stocks")
        
        # Calculate indicators
        logger.info("Calculating indicators...")
        indicators = {}
        relative_strengths = {}
        
        for symbol, df in stock_data.items():
            # Validate data quality
            if not fetcher.validate_data_quality(df, min_days=config.momentum_12m_days):
                logger.warning(f"Skipping {symbol} - insufficient data quality")
                continue
            
            # Calculate indicators
            ind = calculator.calculate_all(df)
            indicators[symbol] = ind
            
            # Calculate relative strength if benchmark available
            if benchmark_df is not None:
                rs = calculator.calculate_relative_strength(
                    df, benchmark_df, lookback_days=config.momentum_6m_days
                )
                relative_strengths[symbol] = rs
        
        if not indicators:
            logger.error("No valid indicators calculated")
            print("Error: Could not calculate indicators for any stocks.")
            sys.exit(1)
        
        logger.info(f"Calculated indicators for {len(indicators)} stocks")
        
        # Rank stocks
        logger.info("Ranking stocks...")
        ranked_df = ranker.rank_stocks(indicators)
        
        if ranked_df.empty:
            logger.error("Ranking failed - no valid stocks")
            print("Error: Could not rank stocks.")
            sys.exit(1)
        
        # Add relative strength if available
        if relative_strengths:
            ranked_df = ranker.add_relative_strength(ranked_df, relative_strengths)
        
        # Get top stocks
        top_overall = ranker.get_top_n(ranked_df, args.top)
        top_momentum = ranker.get_momentum_leaders(ranked_df, config.top_momentum)
        top_trend = ranker.get_trend_filtered(ranked_df, config.top_trend)
        
        # Create portfolio snapshot from top 10
        portfolio = ranker.create_portfolio_snapshot(ranker.get_top_n(ranked_df, 10))
        
        # Get summary stats
        stats = ranker.get_summary_stats(ranked_df)
        
        # Display results
        reporter.print_overall_top(top_overall, args.top)
        reporter.print_momentum_leaders(top_momentum, config.top_momentum)
        reporter.print_trend_filtered(top_trend, config.top_trend)
        reporter.print_summary_stats(stats)
        
        # Save to files
        ranking_file = reporter.save_ranking_csv(ranked_df)
        portfolio_file = reporter.save_portfolio_csv(portfolio)
        
        reporter.print_files_saved(ranking_file, portfolio_file)
        
        logger.info("Stock screening completed successfully")
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        print("\nInterrupted by user")
        sys.exit(0)
    
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
