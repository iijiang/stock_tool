"""
Universe management module for stock screening and backtesting.

Provides clean abstraction for loading different stock universes:
- sp500: S&P 500 stocks
- midcap: Mid-cap growth stocks
- combined: Union of SP500 and MidCap (no duplicates)
"""
import logging
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)

# Universe definitions
UNIVERSE_FILES = {
    'sp500': 'stock_pool/sp500.csv',
    'midcap': 'stock_pool/midcap.csv',
}

VALID_UNIVERSES = ['sp500', 'midcap', 'combined']


def load_universe(name: str, base_path: Path = None) -> List[str]:
    """
    Load stock universe by name.
    
    Args:
        name: Universe name ('sp500', 'midcap', or 'combined')
        base_path: Base directory path (defaults to current working directory)
    
    Returns:
        List of ticker symbols (uppercase, no duplicates)
    
    Raises:
        ValueError: If universe name is invalid
        FileNotFoundError: If universe CSV file not found
    """
    name = name.lower()
    
    # Validate universe name
    if name not in VALID_UNIVERSES:
        raise ValueError(
            f"Invalid universe: '{name}'. "
            f"Valid options: {', '.join(VALID_UNIVERSES)}"
        )
    
    # Set base path
    if base_path is None:
        base_path = Path.cwd()
    
    # Handle combined universe
    if name == 'combined':
        sp500_tickers = _load_universe_file('sp500', base_path)
        midcap_tickers = _load_universe_file('midcap', base_path)
        
        # Merge and deduplicate
        combined_tickers = list(set(sp500_tickers + midcap_tickers))
        combined_tickers.sort()
        
        logger.info(
            f"Loaded combined universe: {len(sp500_tickers)} SP500 + "
            f"{len(midcap_tickers)} MidCap = {len(combined_tickers)} unique"
        )
        
        return combined_tickers
    
    # Handle single universe
    return _load_universe_file(name, base_path)


def _load_universe_file(name: str, base_path: Path) -> List[str]:
    """
    Load tickers from a universe CSV file.
    
    Args:
        name: Universe name (must be in UNIVERSE_FILES)
        base_path: Base directory path
    
    Returns:
        List of ticker symbols (uppercase)
    
    Raises:
        FileNotFoundError: If CSV file not found
    """
    # Get file path
    relative_path = UNIVERSE_FILES[name]
    file_path = base_path / relative_path
    
    # Check if file exists
    if not file_path.exists():
        raise FileNotFoundError(
            f"Universe file not found: {file_path}\n"
            f"Expected path: {relative_path}"
        )
    
    # Read CSV file
    tickers = []
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    # Parse tickers (skip header)
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Skip empty lines
        if not line:
            continue
        
        # Skip header row (contains "Symbol" or "symbol")
        if i == 0 and line.lower() in ['symbol', 'ticker']:
            continue
        if i == 0 and ',' in line and 'symbol' in line.lower():
            continue
        
        # Extract ticker (first column if CSV)
        ticker = line.split(',')[0].strip().upper()
        
        # Validate ticker format
        if ticker and ticker not in ['SYMBOL', 'TICKER']:
            tickers.append(ticker)
    
    logger.info(f"Loaded {len(tickers)} tickers from {name} universe")
    
    return tickers


def get_universe_display_name(name: str) -> str:
    """
    Get human-readable display name for universe.
    
    Args:
        name: Universe name
    
    Returns:
        Display name (e.g., 'SP500' -> 'S&P 500')
    """
    display_names = {
        'sp500': 'S&P 500',
        'midcap': 'Mid-Cap',
        'combined': 'Combined (S&P 500 + Mid-Cap)'
    }
    return display_names.get(name.lower(), name)


def validate_universe_size(tickers: List[str], top_n: int, universe_name: str) -> int:
    """
    Validate that universe has enough tickers for top N selection.
    
    Args:
        tickers: List of ticker symbols
        top_n: Desired portfolio size
        universe_name: Name of universe (for logging)
    
    Returns:
        Adjusted top_n (min of requested and available)
    """
    if len(tickers) < top_n:
        logger.warning(
            f"{universe_name} universe has only {len(tickers)} tickers, "
            f"but top {top_n} requested. Adjusting to top {len(tickers)}."
        )
        return len(tickers)
    
    return top_n
