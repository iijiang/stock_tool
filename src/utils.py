"""
Utility functions for stock screening tool.
"""
import logging
from typing import List
import pandas as pd
from pathlib import Path


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Configure logging for the application."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(__name__)


def load_stock_universe(csv_path: Path) -> List[str]:
    """
    Load stock symbols from CSV file.
    
    Args:
        csv_path: Path to CSV file with 'Symbol' column
        
    Returns:
        List of ticker symbols
    """
    logger = logging.getLogger(__name__)
    
    try:
        df = pd.read_csv(csv_path)
        if 'Symbol' not in df.columns:
            raise ValueError("CSV must contain 'Symbol' column")
        
        symbols = df['Symbol'].dropna().str.strip().tolist()
        logger.info(f"Loaded {len(symbols)} symbols from {csv_path}")
        return symbols
    
    except Exception as e:
        logger.error(f"Error loading stock universe from {csv_path}: {e}")
        raise


def normalize_series(series: pd.Series, invert: bool = False) -> pd.Series:
    """
    Normalize series to 0-1 range using min-max scaling.
    
    Args:
        series: Input series
        invert: If True, invert the normalized values (for volatility)
        
    Returns:
        Normalized series
    """
    min_val = series.min()
    max_val = series.max()
    
    if max_val == min_val:
        return pd.Series(0.5, index=series.index)
    
    normalized = (series - min_val) / (max_val - min_val)
    
    if invert:
        normalized = 1 - normalized
    
    return normalized


def safe_divide(numerator: pd.Series, denominator: pd.Series, fill_value: float = 0.0) -> pd.Series:
    """
    Safely divide two series, handling division by zero.
    
    Args:
        numerator: Numerator series
        denominator: Denominator series
        fill_value: Value to use when denominator is zero
        
    Returns:
        Result series
    """
    result = numerator / denominator
    result = result.replace([float('inf'), float('-inf')], fill_value)
    result = result.fillna(fill_value)
    return result
