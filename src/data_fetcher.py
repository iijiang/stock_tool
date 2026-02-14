"""
Data fetching module using yfinance with caching support.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd
import yfinance as yf
from tqdm import tqdm

from .cache import StockCache


class DataFetcher:
    """Fetch stock data from yfinance with intelligent caching."""
    
    def __init__(self, cache: StockCache, start_date: str = "2010-01-01"):
        """
        Initialize data fetcher.
        
        Args:
            cache: StockCache instance
            start_date: Default start date for historical data (YYYY-MM-DD)
        """
        self.cache = cache
        self.start_date = start_date
        self.logger = logging.getLogger(__name__)
    
    def fetch_symbol(self, symbol: str, start_date: Optional[str] = None, 
                     force_refresh: bool = False) -> Optional[pd.DataFrame]:
        """
        Fetch data for a single symbol with caching.
        
        Args:
            symbol: Stock ticker symbol
            start_date: Start date (YYYY-MM-DD), uses default if None
            force_refresh: If True, bypass cache and re-download
            
        Returns:
            DataFrame with OHLCV data and adj_close, or None if error
        """
        start = start_date or self.start_date
        
        # Check if we need to refresh
        if force_refresh:
            self.logger.info(f"Force refresh for {symbol}")
            self.cache.clear_symbol(symbol)
            return self._download_and_cache(symbol, start)
        
        # Try to get from cache
        last_cached_date = self.cache.get_last_date(symbol)
        
        if last_cached_date:
            # Check if cache is recent (within 2 days)
            last_date = datetime.strptime(last_cached_date, '%Y-%m-%d')
            days_old = (datetime.now() - last_date).days
            
            if days_old <= 2:
                # Cache is fresh, use it
                self.logger.debug(f"Using fresh cache for {symbol} (last: {last_cached_date})")
                return self.cache.get_cached_data(symbol, start)
            else:
                # Update cache with recent data
                self.logger.debug(f"Updating cache for {symbol} from {last_cached_date}")
                return self._update_cache(symbol, start, last_cached_date)
        else:
            # No cache, download all
            self.logger.debug(f"No cache for {symbol}, downloading from {start}")
            return self._download_and_cache(symbol, start)
    
    def _download_and_cache(self, symbol: str, start_date: str) -> Optional[pd.DataFrame]:
        """Download data from yfinance and cache it."""
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, auto_adjust=False)
            
            if df.empty:
                self.logger.warning(f"No data returned for {symbol}")
                return None
            
            # Ensure we have required columns
            required_cols = ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
            if not all(col in df.columns for col in required_cols):
                self.logger.error(f"Missing required columns for {symbol}")
                return None
            
            # Cache the data
            self.cache.save_data(symbol, df)
            
            # Return from cache to ensure consistent format
            return self.cache.get_cached_data(symbol, start_date)
        
        except Exception as e:
            self.logger.error(f"Error downloading {symbol}: {e}")
            return None
    
    def _update_cache(self, symbol: str, start_date: str, last_cached_date: str) -> Optional[pd.DataFrame]:
        """Update cache with recent data."""
        try:
            # Download from day after last cached date
            last_date = datetime.strptime(last_cached_date, '%Y-%m-%d')
            update_start = (last_date + timedelta(days=1)).strftime('%Y-%m-%d')
            
            ticker = yf.Ticker(symbol)
            df_new = ticker.history(start=update_start, auto_adjust=False)
            
            if not df_new.empty:
                # Cache new data
                self.cache.save_data(symbol, df_new)
                self.logger.debug(f"Added {len(df_new)} new rows for {symbol}")
            
            # Return full dataset from cache
            return self.cache.get_cached_data(symbol, start_date)
        
        except Exception as e:
            self.logger.error(f"Error updating cache for {symbol}: {e}")
            # Fall back to cached data
            return self.cache.get_cached_data(symbol, start_date)
    
    def fetch_multiple(self, symbols: List[str], start_date: Optional[str] = None,
                      force_refresh: bool = False, show_progress: bool = True) -> Dict[str, pd.DataFrame]:
        """
        Fetch data for multiple symbols.
        
        Args:
            symbols: List of ticker symbols
            start_date: Start date (YYYY-MM-DD)
            force_refresh: Force re-download all symbols
            show_progress: Show progress bar
            
        Returns:
            Dict mapping symbol to DataFrame
        """
        self.logger.info(f"Fetching data for {len(symbols)} symbols")
        
        results = {}
        iterator = tqdm(symbols, desc="Fetching data") if show_progress else symbols
        
        for symbol in iterator:
            df = self.fetch_symbol(symbol, start_date, force_refresh)
            if df is not None and not df.empty:
                results[symbol] = df
            else:
                self.logger.warning(f"Skipping {symbol} - no valid data")
        
        self.logger.info(f"Successfully fetched {len(results)}/{len(symbols)} symbols")
        return results
    
    def fetch_benchmark(self, benchmark_symbol: str = "SPY", start_date: Optional[str] = None,
                       force_refresh: bool = False) -> Optional[pd.DataFrame]:
        """
        Fetch benchmark data (e.g., SPY for S&P 500).
        
        Args:
            benchmark_symbol: Benchmark ticker
            start_date: Start date
            force_refresh: Force refresh
            
        Returns:
            DataFrame with benchmark data
        """
        self.logger.info(f"Fetching benchmark: {benchmark_symbol}")
        return self.fetch_symbol(benchmark_symbol, start_date, force_refresh)
    
    def validate_data_quality(self, df: pd.DataFrame, min_days: int = 252) -> bool:
        """
        Check if data has sufficient history and quality.
        
        Args:
            df: DataFrame to validate
            min_days: Minimum number of trading days required
            
        Returns:
            True if data quality is acceptable
        """
        if df is None or df.empty:
            return False
        
        if len(df) < min_days:
            return False
        
        # Check for excessive missing data
        if df['adj_close'].isna().sum() > len(df) * 0.1:  # More than 10% missing
            return False
        
        return True
