"""
Technical indicators calculation module.
"""
import logging
from typing import Dict, Optional
import pandas as pd
import numpy as np


class IndicatorCalculator:
    """Calculate technical indicators for stock screening."""
    
    def __init__(self, momentum_6m_days: int = 126, momentum_12m_days: int = 252,
                 ma_short: int = 50, ma_long: int = 200):
        """
        Initialize indicator calculator.
        
        Args:
            momentum_6m_days: Trading days for 6-month momentum (~126)
            momentum_12m_days: Trading days for 12-month momentum (~252)
            ma_short: Short moving average period
            ma_long: Long moving average period
        """
        self.momentum_6m_days = momentum_6m_days
        self.momentum_12m_days = momentum_12m_days
        self.ma_short = ma_short
        self.ma_long = ma_long
        self.logger = logging.getLogger(__name__)
    
    def calculate_all(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate all indicators for a stock.
        
        Args:
            df: DataFrame with at least 'adj_close' column
            
        Returns:
            Dict with calculated indicators
        """
        if df is None or df.empty:
            return self._empty_indicators()
        
        try:
            adj_close = df['adj_close'].dropna()
            
            if len(adj_close) < self.momentum_12m_days:
                self.logger.warning(f"Insufficient data: {len(adj_close)} days < {self.momentum_12m_days}")
                return self._empty_indicators()
            
            indicators = {}
            
            # Momentum returns
            indicators['momentum_6m'] = self._calculate_momentum(adj_close, self.momentum_6m_days)
            indicators['momentum_12m'] = self._calculate_momentum(adj_close, self.momentum_12m_days)
            
            # Moving averages
            indicators['ma50'] = self._calculate_ma(adj_close, self.ma_short)
            indicators['ma200'] = self._calculate_ma(adj_close, self.ma_long)
            
            # Current price vs MA200
            current_price = adj_close.iloc[-1]
            indicators['above_ma200'] = 1 if current_price > indicators['ma200'] else 0
            
            # Volatility (annualized)
            indicators['volatility'] = self._calculate_volatility(adj_close)
            
            # Max drawdown
            indicators['max_drawdown'] = self._calculate_max_drawdown(adj_close)
            
            # Current price for reference
            indicators['current_price'] = current_price
            
            return indicators
        
        except Exception as e:
            self.logger.error(f"Error calculating indicators: {e}")
            return self._empty_indicators()
    
    def _calculate_momentum(self, prices: pd.Series, lookback_days: int) -> float:
        """
        Calculate momentum return over lookback period.
        
        Args:
            prices: Price series
            lookback_days: Number of days to look back
            
        Returns:
            Return as decimal (e.g., 0.15 for 15% return)
        """
        if len(prices) < lookback_days:
            return np.nan
        
        current = prices.iloc[-1]
        past = prices.iloc[-lookback_days]
        
        if past == 0 or np.isnan(past):
            return np.nan
        
        return (current - past) / past
    
    def _calculate_ma(self, prices: pd.Series, period: int) -> float:
        """
        Calculate simple moving average.
        
        Args:
            prices: Price series
            period: MA period
            
        Returns:
            Latest MA value
        """
        if len(prices) < period:
            return np.nan
        
        return prices.rolling(window=period).mean().iloc[-1]
    
    def _calculate_volatility(self, prices: pd.Series, annual_trading_days: int = 252) -> float:
        """
        Calculate annualized volatility from daily returns.
        
        Args:
            prices: Price series
            annual_trading_days: Trading days per year
            
        Returns:
            Annualized volatility
        """
        returns = prices.pct_change().dropna()
        
        if len(returns) < 20:  # Need minimum data
            return np.nan
        
        daily_vol = returns.std()
        annualized_vol = daily_vol * np.sqrt(annual_trading_days)
        
        return annualized_vol
    
    def _calculate_max_drawdown(self, prices: pd.Series) -> float:
        """
        Calculate maximum drawdown from peak.
        
        Args:
            prices: Price series
            
        Returns:
            Max drawdown as positive decimal (e.g., 0.20 for -20% drawdown)
        """
        cumulative = (1 + prices.pct_change()).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        
        return abs(drawdown.min())
    
    def calculate_relative_strength(self, stock_df: pd.DataFrame, benchmark_df: pd.DataFrame,
                                    lookback_days: int = 126) -> float:
        """
        Calculate relative strength vs benchmark.
        
        Args:
            stock_df: Stock price DataFrame
            benchmark_df: Benchmark price DataFrame
            lookback_days: Lookback period
            
        Returns:
            Relative strength ratio
        """
        try:
            # Align dates
            stock_prices = stock_df['adj_close'].dropna()
            benchmark_prices = benchmark_df['adj_close'].dropna()
            
            # Find common date range
            common_dates = stock_prices.index.intersection(benchmark_prices.index)
            
            if len(common_dates) < lookback_days:
                return np.nan
            
            stock_aligned = stock_prices.loc[common_dates]
            benchmark_aligned = benchmark_prices.loc[common_dates]
            
            # Calculate returns over lookback period
            stock_return = self._calculate_momentum(stock_aligned, lookback_days)
            benchmark_return = self._calculate_momentum(benchmark_aligned, lookback_days)
            
            if np.isnan(stock_return) or np.isnan(benchmark_return):
                return np.nan
            
            # Relative strength = stock return - benchmark return
            return stock_return - benchmark_return
        
        except Exception as e:
            self.logger.error(f"Error calculating relative strength: {e}")
            return np.nan
    
    def _empty_indicators(self) -> Dict[str, float]:
        """Return dict with NaN indicators."""
        return {
            'momentum_6m': np.nan,
            'momentum_12m': np.nan,
            'ma50': np.nan,
            'ma200': np.nan,
            'above_ma200': 0,
            'volatility': np.nan,
            'max_drawdown': np.nan,
            'current_price': np.nan
        }
