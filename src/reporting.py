"""
Reporting module for console output and file generation.
"""
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
import pandas as pd


class Reporter:
    """Generate reports for stock screening results."""
    
    def __init__(self, output_dir: Path):
        """
        Initialize reporter.
        
        Args:
            output_dir: Directory for output files
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True, parents=True)
        self.logger = logging.getLogger(__name__)
    
    def print_table(self, df: pd.DataFrame, title: str, max_rows: Optional[int] = None):
        """
        Print formatted table to console.
        
        Args:
            df: DataFrame to display
            title: Table title
            max_rows: Maximum rows to display
        """
        if df.empty:
            print(f"\n{title}")
            print("No data available")
            return
        
        print(f"\n{'=' * 80}")
        print(f"{title}")
        print('=' * 80)
        
        display_df = df.head(max_rows) if max_rows else df
        
        # Format percentages
        format_dict = {}
        if 'momentum_6m' in display_df.columns:
            format_dict['momentum_6m'] = '{:.2%}'.format
        if 'momentum_12m' in display_df.columns:
            format_dict['momentum_12m'] = '{:.2%}'.format
        if 'volatility' in display_df.columns:
            format_dict['volatility'] = '{:.2%}'.format
        if 'score' in display_df.columns:
            format_dict['score'] = '{:.3f}'.format
        if 'equal_weight' in display_df.columns:
            format_dict['equal_weight'] = '{:.2%}'.format
        if 'current_price' in display_df.columns:
            format_dict['current_price'] = '${:.2f}'.format
        
        # Format output
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', 20)
        
        print(display_df.to_string(index=False, formatters=format_dict))
        print()
    
    def print_summary_stats(self, stats: Dict[str, any]):
        """
        Print summary statistics.
        
        Args:
            stats: Dictionary of statistics
        """
        if not stats:
            return
        
        print(f"\n{'=' * 80}")
        print("SUMMARY STATISTICS")
        print('=' * 80)
        
        print(f"Total Stocks Analyzed: {stats.get('total_stocks', 0)}")
        print(f"Average 6M Momentum: {stats.get('avg_momentum_6m', 0):.2%}")
        print(f"Average 12M Momentum: {stats.get('avg_momentum_12m', 0):.2%}")
        print(f"Average Volatility: {stats.get('avg_volatility', 0):.2%}")
        print(f"% Above MA200: {stats.get('pct_above_ma200', 0):.1f}%")
        print(f"Top Score: {stats.get('top_score', 0):.3f}")
        print(f"Median Score: {stats.get('median_score', 0):.3f}")
        print()
    
    def save_ranking_csv(self, df: pd.DataFrame, date: Optional[datetime] = None, universe_name: str = None) -> Path:
        """
        Save full ranking to CSV.
        
        Args:
            df: Ranked DataFrame
            date: Date for filename (default: today)
            universe_name: Universe name for filename prefix (optional)
            
        Returns:
            Path to saved file
        """
        if date is None:
            date = datetime.now()
        
        # Add universe prefix if provided
        prefix = f"{universe_name}_" if universe_name else ""
        filename = f"{prefix}ranking_{date.strftime('%Y-%m-%d')}.csv"
        filepath = self.output_dir / filename
        
        # Select and order columns
        output_cols = [
            'rank', 'symbol', 'score', 'momentum_6m', 'momentum_12m',
            'above_ma200', 'volatility', 'ma50', 'ma200',
            'max_drawdown', 'current_price'
        ]
        
        # Include only available columns
        available_cols = [col for col in output_cols if col in df.columns]
        output_df = df[available_cols].copy()
        
        # Format for CSV
        if 'momentum_6m' in output_df.columns:
            output_df['momentum_6m_pct'] = output_df['momentum_6m'] * 100
        if 'momentum_12m' in output_df.columns:
            output_df['momentum_12m_pct'] = output_df['momentum_12m'] * 100
        if 'volatility' in output_df.columns:
            output_df['volatility_pct'] = output_df['volatility'] * 100
        
        output_df.to_csv(filepath, index=False, float_format='%.4f')
        self.logger.info(f"Saved ranking to {filepath}")
        
        return filepath
    
    def save_portfolio_csv(self, df: pd.DataFrame, date: Optional[datetime] = None, universe_name: str = None) -> Path:
        """
        Save portfolio snapshot to CSV.
        
        Args:
            df: Portfolio DataFrame
            date: Date for filename (default: today)
            universe_name: Universe name for filename prefix (optional)
            
        Returns:
            Path to saved file
        """
        if date is None:
            date = datetime.now()
        
        # Add universe prefix if provided
        prefix = f"{universe_name}_" if universe_name else ""
        filename = f"{prefix}top10_portfolio_{date.strftime('%Y-%m-%d')}.csv"
        filepath = self.output_dir / filename
        
        # Save as-is
        output_df = df.copy()
        
        # Format for CSV
        if 'momentum_6m' in output_df.columns:
            output_df['momentum_6m_pct'] = output_df['momentum_6m'] * 100
        if 'momentum_12m' in output_df.columns:
            output_df['momentum_12m_pct'] = output_df['momentum_12m'] * 100
        if 'volatility' in output_df.columns:
            output_df['volatility_pct'] = output_df['volatility'] * 100
        if 'equal_weight' in output_df.columns:
            output_df['equal_weight_pct'] = output_df['equal_weight'] * 100
        
        output_df.to_csv(filepath, index=False, float_format='%.4f')
        self.logger.info(f"Saved portfolio to {filepath}")
        
        return filepath
    
    def print_report_header(self, universe_name: str, n_symbols: int, date: Optional[datetime] = None):
        """
        Print report header.
        
        Args:
            universe_name: Stock universe name (e.g., 'S&P 500', 'Mid-Cap')
            n_symbols: Number of symbols analyzed
            date: Report date
        """
        if date is None:
            date = datetime.now()
        
        print("\n" + "=" * 80)
        print("STOCK SCREENING REPORT")
        print("=" * 80)
        print(f"Generated: {date.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Universe: {universe_name}")
        print(f"Symbols Analyzed: {n_symbols}")
        print("=" * 80)
    
    def print_overall_top(self, df: pd.DataFrame, n: int = 20):
        """Print overall top N stocks."""
        display_cols = ['rank', 'symbol', 'score', 'momentum_6m', 'momentum_12m', 
                       'above_ma200', 'volatility']
        available_cols = [col for col in display_cols if col in df.columns]
        
        self.print_table(
            df[available_cols].head(n),
            f"TOP {n} STOCKS (by Composite Score)",
            max_rows=n
        )
    
    def print_momentum_leaders(self, df: pd.DataFrame, n: int = 10):
        """Print momentum leaders."""
        display_cols = ['momentum_rank', 'symbol', 'momentum_6m', 'momentum_12m', 
                       'score', 'current_price']
        available_cols = [col for col in display_cols if col in df.columns]
        
        # Rename rank for clarity
        display_df = df.copy()
        if 'momentum_rank' not in display_df.columns and 'rank' in display_df.columns:
            display_df['momentum_rank'] = display_df['rank']
        
        self.print_table(
            display_df[available_cols].head(n),
            f"TOP {n} MOMENTUM LEADERS (by 6M Return)",
            max_rows=n
        )
    
    def print_trend_filtered(self, df: pd.DataFrame, n: int = 10):
        """Print trend-filtered stocks."""
        display_cols = ['trend_rank', 'symbol', 'score', 'momentum_6m', 
                       'ma50', 'ma200', 'current_price']
        available_cols = [col for col in display_cols if col in df.columns]
        
        # Rename rank for clarity
        display_df = df.copy()
        if 'trend_rank' not in display_df.columns and 'rank' in display_df.columns:
            display_df['trend_rank'] = display_df['rank']
        
        self.print_table(
            display_df[available_cols].head(n),
            f"TOP {n} TREND-FILTERED STOCKS (Above MA200)",
            max_rows=n
        )
    
    def print_files_saved(self, ranking_file: Path, portfolio_file: Path):
        """
        Print saved file information.
        
        Args:
            ranking_file: Path to ranking CSV
            portfolio_file: Path to portfolio CSV
        """
        print("=" * 80)
        print("FILES SAVED")
        print("=" * 80)
        print(f"Full Ranking: {ranking_file}")
        print(f"Portfolio: {portfolio_file}")
        print("=" * 80)
        print()
    
    def print_backtest_header(self, start_date: datetime, end_date: datetime, 
                             universe_size: int, top_n: int, regime_filter: bool):
        """
        Print backtest header.
        
        Args:
            start_date: Backtest start date
            end_date: Backtest end date
            universe_size: Number of stocks in universe
            top_n: Number of stocks in portfolio
            regime_filter: Whether regime filter is enabled
        """
        print("\n" + "=" * 80)
        print("MONTHLY ROTATION BACKTEST")
        print("=" * 80)
        print(f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        print(f"Universe: {universe_size} stocks")
        print(f"Portfolio Size: Top {top_n} stocks (equal-weight)")
        print(f"Regime Filter: {'ENABLED (SPY < MA200 → Cash)' if regime_filter else 'DISABLED'}")
        print(f"Rebalance: Monthly (end of month)")
        print("=" * 80)
        print()
    
    def print_backtest_results(self, results: Dict):
        """
        Print backtest performance summary.
        
        Args:
            results: Dict with backtest results
        """
        if not results:
            print("No backtest results to display")
            return
        
        print("\n" + "=" * 80)
        print("BACKTEST PERFORMANCE SUMMARY")
        print("=" * 80)
        
        print(f"\n{'Portfolio Performance':40} {'Value':>15}")
        print("-" * 80)
        print(f"{'Initial Capital':40} ${results['initial_capital']:>14,.2f}")
        print(f"{'Final Value':40} ${results['final_value']:>14,.2f}")
        print(f"{'Total Return':40} {results['total_return']:>14.2%}")
        print(f"{'CAGR':40} {results['cagr']:>14.2%}")
        
        print(f"\n{'Risk Metrics':40} {'Value':>15}")
        print("-" * 80)
        print(f"{'Annualized Volatility':40} {results['volatility']:>14.2%}")
        print(f"{'Sharpe Ratio':40} {results['sharpe_ratio']:>14.2f}")
        print(f"{'Maximum Drawdown':40} {results['max_drawdown']:>14.2%}")
        print(f"{'Win Rate (Monthly)':40} {results['win_rate']:>14.2%}")
        
        print(f"\n{'Benchmark Comparison (SPY)':40} {'Value':>15}")
        print("-" * 80)
        print(f"{'Benchmark Total Return':40} {results['benchmark_total_return']:>14.2%}")
        print(f"{'Benchmark CAGR':40} {results['benchmark_cagr']:>14.2%}")
        print(f"{'Outperformance':40} {results['outperformance']:>14.2%}")
        
        print(f"\n{'Trading Activity':40} {'Value':>15}")
        print("-" * 80)
        print(f"{'Number of Rebalances':40} {results['n_rebalances']:>15,}")
        print(f"{'Number of Trades':40} {results['n_trades']:>15,}")
        print(f"{'Duration (years)':40} {results['years']:>14.1f}")
        
        print("=" * 80)
        print()
    
    def save_backtest_results(self, results: Dict, date: Optional[datetime] = None) -> Path:
        """
        Save backtest summary to CSV.
        
        Args:
            results: Dict with backtest results
            date: Date for filename (default: today)
            
        Returns:
            Path to saved file
        """
        if date is None:
            date = datetime.now()
        
        filename = f"backtest_summary_{date.strftime('%Y-%m-%d')}.csv"
        filepath = self.output_dir / filename
        
        # Create summary DataFrame
        summary_data = {
            'Metric': [
                'Initial Capital',
                'Final Value',
                'Total Return',
                'CAGR',
                'Volatility',
                'Sharpe Ratio',
                'Max Drawdown',
                'Win Rate',
                'Benchmark Return',
                'Benchmark CAGR',
                'Outperformance',
                'Rebalances',
                'Trades',
                'Years'
            ],
            'Value': [
                results['initial_capital'],
                results['final_value'],
                results['total_return'],
                results['cagr'],
                results['volatility'],
                results['sharpe_ratio'],
                results['max_drawdown'],
                results['win_rate'],
                results['benchmark_total_return'],
                results['benchmark_cagr'],
                results['outperformance'],
                results['n_rebalances'],
                results['n_trades'],
                results['years']
            ]
        }
        
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_csv(filepath, index=False)
        
        self.logger.info(f"Saved backtest summary to {filepath}")
        return filepath
    
    def save_backtest_history(self, history_df: pd.DataFrame, 
                             date: Optional[datetime] = None) -> Path:
        """
        Save daily portfolio history to CSV.
        
        Args:
            history_df: DataFrame with daily portfolio values
            date: Date for filename (default: today)
            
        Returns:
            Path to saved file
        """
        if date is None:
            date = datetime.now()
        
        filename = f"backtest_history_{date.strftime('%Y-%m-%d')}.csv"
        filepath = self.output_dir / filename
        
        # Select key columns
        output_cols = ['portfolio_value', 'cash', 'invested_value', 
                      'benchmark_price', 'portfolio_return', 'benchmark_return']
        available_cols = [col for col in output_cols if col in history_df.columns]
        
        output_df = history_df[available_cols].copy()
        output_df.to_csv(filepath, float_format='%.4f')
        
        self.logger.info(f"Saved backtest history to {filepath}")
        return filepath
    
    def save_trades_log(self, trades_df: pd.DataFrame, 
                       date: Optional[datetime] = None) -> Path:
        """
        Save trade log to CSV.
        
        Args:
            trades_df: DataFrame with trade records
            date: Date for filename (default: today)
            
        Returns:
            Path to saved file
        """
        if date is None:
            date = datetime.now()
        
        filename = f"backtest_trades_{date.strftime('%Y-%m-%d')}.csv"
        filepath = self.output_dir / filename
        
        trades_df.to_csv(filepath, index=False, float_format='%.4f')
        
        self.logger.info(f"Saved trades log to {filepath}")
        return filepath
    
    def print_backtest_files_saved(self, summary_file: Path, history_file: Path, 
                                   trades_file: Path, charts_file: Optional[Path] = None):
        """
        Print saved backtest files.
        
        Args:
            summary_file: Path to summary CSV
            history_file: Path to history CSV
            trades_file: Path to trades CSV
            charts_file: Optional path to charts image
        """
        print("=" * 80)
        print("BACKTEST FILES SAVED")
        print("=" * 80)
        print(f"Summary: {summary_file}")
        print(f"History: {history_file}")
        print(f"Trades: {trades_file}")
        if charts_file:
            print(f"Charts: {charts_file}")
        print("=" * 80)
        print()
