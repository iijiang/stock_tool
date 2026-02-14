"""
SQLite-based caching layer for stock data.
"""
import sqlite3
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Tuple
import pandas as pd


class StockCache:
    """SQLite cache for stock price data."""
    
    def __init__(self, db_path: Path):
        """
        Initialize cache connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._init_db()
    
    def _init_db(self):
        """Create database schema if not exists."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS stock_prices (
                    symbol TEXT NOT NULL,
                    date TEXT NOT NULL,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    adj_close REAL,
                    volume INTEGER,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (symbol, date)
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_symbol ON stock_prices(symbol)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_date ON stock_prices(date)
            """)
            conn.commit()
    
    def get_cached_data(self, symbol: str, start_date: Optional[str] = None) -> Optional[pd.DataFrame]:
        """
        Retrieve cached data for a symbol.
        
        Args:
            symbol: Stock ticker symbol
            start_date: Optional start date filter (YYYY-MM-DD)
            
        Returns:
            DataFrame with cached data or None if not found
        """
        query = "SELECT date, open, high, low, close, adj_close, volume FROM stock_prices WHERE symbol = ?"
        params = [symbol]
        
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        
        query += " ORDER BY date ASC"
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                df = pd.read_sql_query(query, conn, params=params)
                
            if df.empty:
                return None
            
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            self.logger.debug(f"Retrieved {len(df)} cached rows for {symbol}")
            return df
        
        except Exception as e:
            self.logger.error(f"Error retrieving cached data for {symbol}: {e}")
            return None
    
    def get_last_date(self, symbol: str) -> Optional[str]:
        """
        Get the most recent date in cache for a symbol.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Latest date as string (YYYY-MM-DD) or None
        """
        query = "SELECT MAX(date) as last_date FROM stock_prices WHERE symbol = ?"
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                result = conn.execute(query, [symbol]).fetchone()
                return result[0] if result and result[0] else None
        
        except Exception as e:
            self.logger.error(f"Error getting last date for {symbol}: {e}")
            return None
    
    def save_data(self, symbol: str, df: pd.DataFrame):
        """
        Save or update stock data in cache.
        
        Args:
            symbol: Stock ticker symbol
            df: DataFrame with columns: Open, High, Low, Close, Adj Close, Volume
                Index should be DatetimeIndex
        """
        if df.empty:
            self.logger.warning(f"Empty DataFrame provided for {symbol}, skipping cache")
            return
        
        # Prepare data for insertion
        df = df.copy()
        df.reset_index(inplace=True)
        
        # Rename columns to match our schema
        column_mapping = {
            'Date': 'date',
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Adj Close': 'adj_close',
            'Volume': 'volume'
        }
        df.rename(columns=column_mapping, inplace=True)
        
        # Ensure date is in string format
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
        df['symbol'] = symbol
        df['updated_at'] = datetime.now().isoformat()
        
        # Select only the columns we need
        columns = ['symbol', 'date', 'open', 'high', 'low', 'close', 'adj_close', 'volume', 'updated_at']
        df = df[columns]
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                df.to_sql('stock_prices', conn, if_exists='append', index=False, method='multi')
                conn.commit()
                self.logger.debug(f"Saved {len(df)} rows for {symbol}")
        
        except sqlite3.IntegrityError:
            # Handle duplicate entries by updating
            self._upsert_data(symbol, df)
        
        except Exception as e:
            self.logger.error(f"Error saving data for {symbol}: {e}")
            raise
    
    def _upsert_data(self, symbol: str, df: pd.DataFrame):
        """Update existing records or insert new ones."""
        with sqlite3.connect(self.db_path) as conn:
            for _, row in df.iterrows():
                conn.execute("""
                    INSERT OR REPLACE INTO stock_prices 
                    (symbol, date, open, high, low, close, adj_close, volume, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, tuple(row))
            conn.commit()
            self.logger.debug(f"Upserted {len(df)} rows for {symbol}")
    
    def clear_symbol(self, symbol: str):
        """
        Delete all cached data for a symbol.
        
        Args:
            symbol: Stock ticker symbol
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM stock_prices WHERE symbol = ?", [symbol])
                conn.commit()
                self.logger.info(f"Cleared cache for {symbol}")
        
        except Exception as e:
            self.logger.error(f"Error clearing cache for {symbol}: {e}")
    
    def clear_all(self):
        """Delete all cached data."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM stock_prices")
                conn.commit()
                self.logger.info("Cleared all cache data")
        
        except Exception as e:
            self.logger.error(f"Error clearing all cache: {e}")
    
    def get_cached_symbols(self) -> List[str]:
        """Get list of all symbols in cache."""
        query = "SELECT DISTINCT symbol FROM stock_prices ORDER BY symbol"
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                result = conn.execute(query).fetchall()
                return [row[0] for row in result]
        
        except Exception as e:
            self.logger.error(f"Error getting cached symbols: {e}")
            return []
