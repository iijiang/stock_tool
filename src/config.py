"""
Configuration management for stock screening tool.
"""
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class Config:
    """Configuration parameters for stock screening."""
    
    # Data settings
    start_date: str = "2010-01-01"
    benchmark_symbol: str = "SPY"
    
    # Lookback windows (trading days)
    momentum_6m_days: int = 126
    momentum_12m_days: int = 252
    ma_short: int = 50
    ma_long: int = 200
    
    # Ranking weights
    weight_6m_momentum: float = 0.40
    weight_12m_momentum: float = 0.30
    weight_above_ma200: float = 0.20
    weight_volatility: float = 0.10
    
    # Top N settings
    top_overall: int = 20
    top_momentum: int = 10
    top_trend: int = 10
    
    # Paths
    project_root: Path = Path(__file__).parent.parent
    cache_dir: Path = project_root / "cache"
    output_dir: Path = project_root / "output"
    stock_pool_dir: Path = project_root / "stock_pool"
    
    # Cache settings
    cache_db: str = "stock_data.db"
    
    # Logging
    log_level: str = "INFO"
    
    def __post_init__(self):
        """Ensure directories exist."""
        self.cache_dir.mkdir(exist_ok=True, parents=True)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        self.stock_pool_dir.mkdir(exist_ok=True, parents=True)
    
    @property
    def cache_db_path(self) -> Path:
        """Full path to cache database."""
        return self.cache_dir / self.cache_db
    
    def get_output_filename(self, prefix: str, date: Optional[datetime] = None) -> str:
        """Generate output filename with date."""
        if date is None:
            date = datetime.now()
        date_str = date.strftime("%Y-%m-%d")
        return f"{prefix}_{date_str}.csv"


# Global config instance
config = Config()
