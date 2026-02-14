"""
Visualization module for backtest results.
"""
import logging
from pathlib import Path
from typing import Dict, Optional
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime


class BacktestVisualizer:
    """Create charts for backtest results."""
    
    def __init__(self, output_dir: Path):
        """
        Initialize visualizer.
        
        Args:
            output_dir: Directory for output files
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True, parents=True)
        self.logger = logging.getLogger(__name__)
        
        # Set style
        plt.style.use('seaborn-v0_8-darkgrid' if 'seaborn-v0_8-darkgrid' in plt.style.available else 'default')
    
    def create_performance_chart(self, 
                                history_df: pd.DataFrame,
                                results: Dict,
                                date: Optional[datetime] = None) -> Path:
        """
        Create comprehensive performance chart.
        
        Args:
            history_df: DataFrame with portfolio history
            results: Dict with backtest results
            date: Date for filename (default: today)
            
        Returns:
            Path to saved chart
        """
        if date is None:
            date = datetime.now()
        
        filename = f"backtest_chart_{date.strftime('%Y-%m-%d')}.png"
        filepath = self.output_dir / filename
        
        # Create figure with subplots
        fig = plt.figure(figsize=(14, 10))
        gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)
        
        # 1. Cumulative Returns (main chart)
        ax1 = fig.add_subplot(gs[0, :])
        self._plot_cumulative_returns(ax1, history_df, results)
        
        # 2. Drawdown
        ax2 = fig.add_subplot(gs[1, 0])
        self._plot_drawdown(ax2, history_df)
        
        # 3. Monthly Returns Distribution
        ax3 = fig.add_subplot(gs[1, 1])
        self._plot_monthly_returns_dist(ax3, history_df)
        
        # 4. Rolling Volatility
        ax4 = fig.add_subplot(gs[2, 0])
        self._plot_rolling_volatility(ax4, history_df)
        
        # 5. Cash vs Invested
        ax5 = fig.add_subplot(gs[2, 1])
        self._plot_cash_allocation(ax5, history_df)
        
        # Add title
        fig.suptitle(f'Backtest Performance Report\n{results["start_date"].strftime("%Y-%m-%d")} to {results["end_date"].strftime("%Y-%m-%d")}',
                    fontsize=14, fontweight='bold')
        
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"Saved performance chart to {filepath}")
        return filepath
    
    def _plot_cumulative_returns(self, ax, history_df: pd.DataFrame, results: Dict):
        """Plot cumulative returns vs benchmark."""
        # Calculate cumulative returns
        portfolio_cumulative = (1 + history_df['portfolio_return']).cumprod() * 100
        benchmark_cumulative = (1 + history_df['benchmark_return']).cumprod() * 100
        
        ax.plot(history_df.index, portfolio_cumulative, 
               label='Portfolio', linewidth=2, color='#2E86AB')
        ax.plot(history_df.index, benchmark_cumulative, 
               label='SPY Benchmark', linewidth=2, color='#A23B72', linestyle='--')
        
        ax.set_ylabel('Growth of $100', fontsize=10)
        ax.set_title('Cumulative Returns', fontsize=11, fontweight='bold')
        ax.legend(loc='upper left', fontsize=9)
        ax.grid(True, alpha=0.3)
        
        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        ax.xaxis.set_major_locator(mdates.YearLocator())
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        # Add performance text
        text = f'Total Return: {results["total_return"]:.1%}\n'
        text += f'CAGR: {results["cagr"]:.1%}\n'
        text += f'Sharpe: {results["sharpe_ratio"]:.2f}'
        ax.text(0.02, 0.98, text, transform=ax.transAxes,
               verticalalignment='top', fontsize=9,
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    def _plot_drawdown(self, ax, history_df: pd.DataFrame):
        """Plot drawdown over time."""
        cumulative = (1 + history_df['portfolio_return']).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        
        ax.fill_between(history_df.index, drawdown * 100, 0, 
                       color='#E63946', alpha=0.6)
        ax.set_ylabel('Drawdown (%)', fontsize=10)
        ax.set_title('Portfolio Drawdown', fontsize=11, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        ax.xaxis.set_major_locator(mdates.YearLocator())
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        # Add max drawdown text
        max_dd = drawdown.min() * 100
        ax.text(0.02, 0.02, f'Max DD: {max_dd:.1f}%',
               transform=ax.transAxes, fontsize=9,
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    def _plot_monthly_returns_dist(self, ax, history_df: pd.DataFrame):
        """Plot monthly returns distribution."""
        monthly_returns = history_df['portfolio_return'].resample('M').apply(lambda x: (1 + x).prod() - 1)
        
        # Histogram
        ax.hist(monthly_returns * 100, bins=30, color='#06A77D', 
               alpha=0.7, edgecolor='black')
        ax.axvline(0, color='red', linestyle='--', linewidth=1, alpha=0.7)
        
        ax.set_xlabel('Monthly Return (%)', fontsize=10)
        ax.set_ylabel('Frequency', fontsize=10)
        ax.set_title('Monthly Returns Distribution', fontsize=11, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add statistics
        mean_return = monthly_returns.mean() * 100
        win_rate = (monthly_returns > 0).sum() / len(monthly_returns) * 100
        text = f'Avg: {mean_return:.1f}%\nWin Rate: {win_rate:.0f}%'
        ax.text(0.98, 0.98, text, transform=ax.transAxes,
               verticalalignment='top', horizontalalignment='right',
               fontsize=9, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    def _plot_rolling_volatility(self, ax, history_df: pd.DataFrame):
        """Plot rolling volatility."""
        rolling_vol = history_df['portfolio_return'].rolling(window=60).std() * np.sqrt(252) * 100
        
        ax.plot(history_df.index, rolling_vol, color='#F18F01', linewidth=1.5)
        ax.fill_between(history_df.index, rolling_vol, alpha=0.3, color='#F18F01')
        
        ax.set_ylabel('Annualized Vol (%)', fontsize=10)
        ax.set_title('Rolling 60-Day Volatility', fontsize=11, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        ax.xaxis.set_major_locator(mdates.YearLocator())
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        # Add average volatility
        avg_vol = rolling_vol.mean()
        ax.axhline(avg_vol, color='red', linestyle='--', linewidth=1, alpha=0.5)
        ax.text(0.02, 0.98, f'Avg Vol: {avg_vol:.1f}%',
               transform=ax.transAxes, verticalalignment='top',
               fontsize=9, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    def _plot_cash_allocation(self, ax, history_df: pd.DataFrame):
        """Plot cash vs invested allocation over time."""
        cash_pct = history_df['cash'] / history_df['portfolio_value'] * 100
        invested_pct = (history_df['portfolio_value'] - history_df['cash']) / history_df['portfolio_value'] * 100
        
        ax.fill_between(history_df.index, 0, invested_pct, 
                       label='Invested', color='#2E86AB', alpha=0.6)
        ax.fill_between(history_df.index, invested_pct, 100, 
                       label='Cash', color='#95B8D1', alpha=0.6)
        
        ax.set_ylabel('Allocation (%)', fontsize=10)
        ax.set_title('Portfolio Allocation (Cash vs Invested)', fontsize=11, fontweight='bold')
        ax.legend(loc='upper left', fontsize=9)
        ax.set_ylim([0, 100])
        ax.grid(True, alpha=0.3)
        
        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        ax.xaxis.set_major_locator(mdates.YearLocator())
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        # Add cash time percentage
        cash_time_pct = (cash_pct > 50).sum() / len(cash_pct) * 100
        ax.text(0.98, 0.98, f'Cash Time: {cash_time_pct:.0f}%',
               transform=ax.transAxes, verticalalignment='top',
               horizontalalignment='right', fontsize=9,
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    def create_simple_chart(self, history_df: pd.DataFrame, 
                          date: Optional[datetime] = None) -> Path:
        """
        Create simple cumulative returns chart.
        
        Args:
            history_df: DataFrame with portfolio history
            date: Date for filename (default: today)
            
        Returns:
            Path to saved chart
        """
        if date is None:
            date = datetime.now()
        
        filename = f"backtest_simple_{date.strftime('%Y-%m-%d')}.png"
        filepath = self.output_dir / filename
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Calculate cumulative returns
        portfolio_cumulative = (1 + history_df['portfolio_return']).cumprod() * 100
        benchmark_cumulative = (1 + history_df['benchmark_return']).cumprod() * 100
        
        ax.plot(history_df.index, portfolio_cumulative, 
               label='Portfolio', linewidth=2.5, color='#2E86AB')
        ax.plot(history_df.index, benchmark_cumulative, 
               label='SPY Benchmark', linewidth=2, color='#A23B72', linestyle='--')
        
        ax.set_xlabel('Date', fontsize=11)
        ax.set_ylabel('Growth of $100', fontsize=11)
        ax.set_title('Backtest: Cumulative Returns', fontsize=13, fontweight='bold')
        ax.legend(loc='upper left', fontsize=10)
        ax.grid(True, alpha=0.3)
        
        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.xaxis.set_major_locator(mdates.YearLocator())
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"Saved simple chart to {filepath}")
        return filepath
