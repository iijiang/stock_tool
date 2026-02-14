"""
Monthly rotation backtest engine with market regime filtering.
Modular, testable functions following requirements.
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
import json
from pathlib import Path

from .indicators import IndicatorCalculator
from .ranking import StockRanker


def get_month_ends(price_df: pd.DataFrame) -> List[pd.Timestamp]:
    """
    Extract month-end dates from price DataFrame.
    
    Args:
        price_df: DataFrame with DatetimeIndex
        
    Returns:
        List of month-end timestamps (last trading day of each month)
    """
    if price_df.empty:
        return []
    
    # Group by year-month and get last date of each month
    month_ends = price_df.groupby([price_df.index.year, price_df.index.month]).apply(
        lambda x: x.index[-1]
    ).tolist()
    
    return month_ends


def compute_indicators(prices: pd.Series, asof_date: pd.Timestamp,
                      calculator: IndicatorCalculator) -> Dict[str, float]:
    """
    Compute indicators for a single stock using data up to asof_date.
    
    Args:
        prices: Series with DatetimeIndex and adj_close values
        asof_date: Compute indicators using only data up to this date
        calculator: IndicatorCalculator instance
        
    Returns:
        Dict with indicator values
    """
    # Filter data up to asof_date (no look-ahead)
    prices_pit = prices[prices.index <= asof_date]
    
    if len(prices_pit) < calculator.momentum_12m_days:
        return {}
    
    # Create DataFrame format expected by calculator
    df = pd.DataFrame({'adj_close': prices_pit})
    
    indicators = calculator.calculate_all(df)
    return indicators


def score_universe(indicator_dict: Dict[str, Dict[str, float]],
                  ranker: StockRanker) -> pd.DataFrame:
    """
    Score and rank stocks based on indicators.
    
    Args:
        indicator_dict: Dict mapping symbol to indicators
        ranker: StockRanker instance
        
    Returns:
        DataFrame with rankings and scores
    """
    if not indicator_dict:
        return pd.DataFrame()
    
    ranked_df = ranker.rank_stocks(indicator_dict)
    return ranked_df


def check_regime_filter(spy_prices: pd.Series, asof_date: pd.Timestamp,
                       ma_period: int = 200) -> bool:
    """
    Check if regime filter triggers cash position.
    
    Args:
        spy_prices: SPY adjusted close Series
        asof_date: Date to check
        ma_period: MA period (default 200)
        
    Returns:
        True if should go to cash (SPY < MA200), False otherwise
    """
    spy_pit = spy_prices[spy_prices.index <= asof_date]
    
    if len(spy_pit) < ma_period:
        return False  # Not enough data, stay invested
    
    current_price = spy_pit.iloc[-1]
    ma200 = spy_pit.rolling(window=ma_period).mean().iloc[-1]
    
    return current_price < ma200


def run_backtest(universe_prices: Dict[str, pd.Series],
                spy_prices: pd.Series,
                month_ends: List[pd.Timestamp],
                calculator: IndicatorCalculator,
                ranker: StockRanker,
                top_n: int = 10,
                regime_filter: bool = True,
                tx_cost_bps: float = 0.0) -> Tuple[pd.DataFrame, Dict]:
    """
    Run monthly rotation backtest.
    
    Args:
        universe_prices: Dict mapping symbol to adj_close Series
        spy_prices: SPY adj_close Series
        month_ends: List of rebalance dates (month-ends)
        calculator: IndicatorCalculator instance
        ranker: StockRanker instance
        top_n: Number of stocks in portfolio
        regime_filter: Enable SPY < MA200 cash filter
        tx_cost_bps: Transaction cost in basis points (default 0)
        
    Returns:
        Tuple of (results_df, summary_dict)
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Running backtest: {len(month_ends)} periods, Top {top_n}, "
               f"Regime Filter: {regime_filter}, Tx Cost: {tx_cost_bps} bps")
    
    results = []
    
    for i in range(len(month_ends) - 1):
        current_date = month_ends[i]
        next_date = month_ends[i + 1]
        
        logger.debug(f"Rebalance {i+1}/{len(month_ends)-1}: {current_date.date()}")
        
        # Check regime filter at current month-end
        in_cash = False
        if regime_filter:
            in_cash = check_regime_filter(spy_prices, current_date)
        
        # Select portfolio for next month
        selected_symbols = []
        n_selected = 0
        
        if not in_cash:
            # Compute indicators for all stocks using data up to current_date
            indicator_dict = {}
            for symbol, prices in universe_prices.items():
                ind = compute_indicators(prices, current_date, calculator)
                if ind:  # Only include stocks with valid indicators
                    indicator_dict[symbol] = ind
            
            # Rank and select top N
            if indicator_dict:
                ranked_df = score_universe(indicator_dict, ranker)
                if not ranked_df.empty:
                    top_stocks = ranked_df.head(top_n)
                    selected_symbols = top_stocks['symbol'].tolist()
                    n_selected = len(selected_symbols)
        
        # Calculate portfolio return for next month
        portfolio_return = 0.0
        
        if selected_symbols:
            stock_returns = []
            for symbol in selected_symbols:
                if symbol in universe_prices:
                    prices = universe_prices[symbol]
                    # Get prices at current_date and next_date
                    price_current = prices[prices.index <= current_date].iloc[-1]
                    prices_next = prices[prices.index <= next_date]
                    if not prices_next.empty:
                        price_next = prices_next.iloc[-1]
                        ret = (price_next - price_current) / price_current
                        stock_returns.append(ret)
            
            if stock_returns:
                # Equal-weight average
                portfolio_return = np.mean(stock_returns)
                
                # Apply transaction cost (flat cost on rebalance)
                if tx_cost_bps > 0:
                    portfolio_return -= tx_cost_bps / 10000.0
        
        # SPY return for comparison
        spy_current = spy_prices[spy_prices.index <= current_date].iloc[-1]
        spy_next_prices = spy_prices[spy_prices.index <= next_date]
        if not spy_next_prices.empty:
            spy_next = spy_next_prices.iloc[-1]
            spy_return = (spy_next - spy_current) / spy_current
        else:
            spy_return = 0.0
        
        # Record results
        results.append({
            'date': next_date,
            'portfolio_return': portfolio_return,
            'spy_return': spy_return,
            'in_cash': 1 if in_cash else 0,
            'selected_symbols': ','.join(selected_symbols) if selected_symbols else '',
            'n_selected': n_selected
        })
    
    results_df = pd.DataFrame(results)
    results_df.set_index('date', inplace=True)
    
    # Compute summary statistics
    summary = compute_performance_metrics(results_df)
    
    return results_df, summary


def compute_performance_metrics(results_df: pd.DataFrame) -> Dict:
    """
    Compute comprehensive performance metrics from backtest results.
    
    Args:
        results_df: DataFrame with portfolio_return, spy_return columns
        
    Returns:
        Dict with performance metrics
    """
    if results_df.empty:
        return {}
    
    # Cumulative returns
    portfolio_cumulative = (1 + results_df['portfolio_return']).cumprod()
    spy_cumulative = (1 + results_df['spy_return']).cumprod()
    
    total_return = portfolio_cumulative.iloc[-1] - 1
    spy_total_return = spy_cumulative.iloc[-1] - 1
    
    # CAGR
    n_months = len(results_df)
    years = n_months / 12.0
    cagr = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0
    spy_cagr = (1 + spy_total_return) ** (1 / years) - 1 if years > 0 else 0
    
    # Volatility (annualized)
    monthly_vol = results_df['portfolio_return'].std()
    annualized_vol = monthly_vol * np.sqrt(12)
    
    # Sharpe (assuming risk-free = 0)
    avg_monthly_return = results_df['portfolio_return'].mean()
    sharpe = (avg_monthly_return * 12) / annualized_vol if annualized_vol > 0 else 0
    
    # Max drawdown
    cumulative = (1 + results_df['portfolio_return']).cumprod()
    running_max = cumulative.expanding().max()
    drawdown = (cumulative - running_max) / running_max
    max_drawdown = drawdown.min()
    
    # Win rate
    win_rate = (results_df['portfolio_return'] > 0).sum() / len(results_df)
    
    # Cash metrics
    pct_months_in_cash = results_df['in_cash'].mean()
    
    # Best/worst months
    best_month = results_df['portfolio_return'].max()
    worst_month = results_df['portfolio_return'].min()
    
    # Start/end dates
    start_date = results_df.index[0]
    end_date = results_df.index[-1]
    
    summary = {
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'n_months': n_months,
        'years': years,
        'total_return': float(total_return),
        'cagr': float(cagr),
        'annualized_volatility': float(annualized_vol),
        'sharpe_ratio': float(sharpe),
        'max_drawdown': float(max_drawdown),
        'win_rate': float(win_rate),
        'best_month': float(best_month),
        'worst_month': float(worst_month),
        'pct_months_in_cash': float(pct_months_in_cash),
        'spy_total_return': float(spy_total_return),
        'spy_cagr': float(spy_cagr),
        'outperformance': float(total_return - spy_total_return)
    }
    
    return summary


def plot_equity_curve(results_df: pd.DataFrame, output_path: Path):
    """
    Create equity curve chart comparing portfolio vs SPY.
    
    Args:
        results_df: DataFrame with portfolio_return, spy_return
        output_path: Path to save PNG file
    """
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    
    # Calculate cumulative returns (starting from $100)
    portfolio_cumulative = (1 + results_df['portfolio_return']).cumprod() * 100
    spy_cumulative = (1 + results_df['spy_return']).cumprod() * 100
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    ax.plot(results_df.index, portfolio_cumulative, 
           label='Portfolio (Monthly Rotation)', linewidth=2.5, color='#2E86AB')
    ax.plot(results_df.index, spy_cumulative, 
           label='SPY Benchmark', linewidth=2, color='#A23B72', linestyle='--')
    
    ax.set_xlabel('Date', fontsize=11)
    ax.set_ylabel('Growth of $100', fontsize=11)
    ax.set_title('Backtest: Monthly Rotation Equity Curve', fontsize=13, fontweight='bold')
    ax.legend(loc='upper left', fontsize=10)
    ax.grid(True, alpha=0.3)
    
    # Format x-axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.xaxis.set_major_locator(mdates.YearLocator())
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()


class BacktestRunner:
    """High-level backtest orchestrator."""
    
    def __init__(self, 
                 calculator: IndicatorCalculator,
                 ranker: StockRanker,
                 output_dir: Path):
        """
        Initialize backtest runner.
        
        Args:
            calculator: IndicatorCalculator instance
            ranker: StockRanker instance
            output_dir: Output directory
        """
        self.calculator = calculator
        self.ranker = ranker
        self.output_dir = output_dir
        self.logger = logging.getLogger(__name__)
        
        # Create backtest subdirectory
        self.backtest_dir = output_dir / 'backtest'
        self.backtest_dir.mkdir(exist_ok=True, parents=True)
    
    def run(self,
            stock_data: Dict[str, pd.DataFrame],
            benchmark_data: pd.DataFrame,
            top_n: int = 10,
            regime_filter: bool = True,
            tx_cost_bps: float = 0.0) -> Dict:
        """
        Run complete backtest and generate outputs.
        
        Args:
            stock_data: Dict mapping symbol to price DataFrame
            benchmark_data: SPY price DataFrame
            top_n: Portfolio size
            regime_filter: Enable regime filter
            tx_cost_bps: Transaction cost in basis points
            
        Returns:
            Dict with results and file paths
        """
        self.logger.info("Preparing data for backtest...")
        
        # Extract adjusted close series
        universe_prices = {}
        for symbol, df in stock_data.items():
            if 'adj_close' in df.columns and len(df) >= self.calculator.momentum_12m_days:
                universe_prices[symbol] = df['adj_close']
        
        if not universe_prices:
            self.logger.error("No valid stocks for backtest")
            return {}
        
        spy_prices = benchmark_data['adj_close']
        
        # Get month-end dates
        month_ends = get_month_ends(benchmark_data)
        
        if len(month_ends) < 2:
            self.logger.error("Insufficient date range for backtest")
            return {}
        
        self.logger.info(f"Backtest period: {month_ends[0].date()} to {month_ends[-1].date()}")
        self.logger.info(f"Universe: {len(universe_prices)} stocks, Periods: {len(month_ends)-1}")
        
        # Run backtest
        results_df, summary = run_backtest(
            universe_prices=universe_prices,
            spy_prices=spy_prices,
            month_ends=month_ends,
            calculator=self.calculator,
            ranker=self.ranker,
            top_n=top_n,
            regime_filter=regime_filter,
            tx_cost_bps=tx_cost_bps
        )
        
        if results_df.empty:
            self.logger.error("Backtest produced no results")
            return {}
        
        # Generate outputs
        timestamp = datetime.now().strftime('%Y-%m-%d')
        
        # 1. Monthly returns CSV
        returns_file = self.backtest_dir / f'backtest_monthly_returns_{timestamp}.csv'
        results_df.to_csv(returns_file)
        self.logger.info(f"Saved monthly returns: {returns_file}")
        
        # 2. Summary JSON
        summary_file = self.backtest_dir / f'backtest_summary_{timestamp}.json'
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        self.logger.info(f"Saved summary: {summary_file}")
        
        # 3. Equity curve chart
        chart_file = self.backtest_dir / f'equity_curve_{timestamp}.png'
        try:
            plot_equity_curve(results_df, chart_file)
            self.logger.info(f"Saved chart: {chart_file}")
        except Exception as e:
            self.logger.warning(f"Could not create chart: {e}")
            chart_file = None
        
        return {
            'results_df': results_df,
            'summary': summary,
            'returns_file': returns_file,
            'summary_file': summary_file,
            'chart_file': chart_file
        }
