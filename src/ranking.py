"""
Stock ranking system with composite scoring.
"""
import logging
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np

from .utils import normalize_series


class StockRanker:
    """Rank stocks based on multi-factor composite score."""
    
    def __init__(self, weight_6m: float = 0.40, weight_12m: float = 0.30,
                 weight_ma200: float = 0.20, weight_vol: float = 0.10):
        """
        Initialize ranker with factor weights.
        
        Args:
            weight_6m: Weight for 6-month momentum
            weight_12m: Weight for 12-month momentum
            weight_ma200: Weight for Above MA200
            weight_vol: Weight for volatility (inverted)
        """
        self.weight_6m = weight_6m
        self.weight_12m = weight_12m
        self.weight_ma200 = weight_ma200
        self.weight_vol = weight_vol
        self.logger = logging.getLogger(__name__)
        
        # Validate weights sum to 1
        total = weight_6m + weight_12m + weight_ma200 + weight_vol
        if abs(total - 1.0) > 0.01:
            self.logger.warning(f"Weights sum to {total}, not 1.0")
    
    def rank_stocks(self, indicators_dict: Dict[str, Dict[str, float]]) -> pd.DataFrame:
        """
        Rank stocks based on indicators.
        
        Args:
            indicators_dict: Dict mapping symbol to indicators dict
            
        Returns:
            DataFrame with rankings and scores
        """
        if not indicators_dict:
            self.logger.warning("No indicators provided for ranking")
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame.from_dict(indicators_dict, orient='index')
        df.index.name = 'symbol'
        df.reset_index(inplace=True)
        
        # Filter out stocks with insufficient data
        initial_count = len(df)
        df = df.dropna(subset=['momentum_6m', 'momentum_12m', 'volatility'])
        filtered_count = len(df)
        
        if filtered_count < initial_count:
            self.logger.info(f"Filtered out {initial_count - filtered_count} stocks with missing data")
        
        if df.empty:
            self.logger.warning("No valid stocks after filtering")
            return pd.DataFrame()
        
        # Calculate composite score
        df = self._calculate_composite_score(df)
        
        # Sort by score descending
        df = df.sort_values('score', ascending=False)
        
        # Add rank
        df['rank'] = range(1, len(df) + 1)
        
        return df
    
    def _calculate_composite_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate normalized composite score.
        
        Args:
            df: DataFrame with indicator columns
            
        Returns:
            DataFrame with added 'score' column
        """
        # Normalize each factor to 0-1 scale
        norm_6m = normalize_series(df['momentum_6m'])
        norm_12m = normalize_series(df['momentum_12m'])
        norm_ma200 = df['above_ma200']  # Already 0 or 1
        norm_vol = normalize_series(df['volatility'], invert=True)  # Lower vol is better
        
        # Calculate weighted composite score
        df['score'] = (
            self.weight_6m * norm_6m +
            self.weight_12m * norm_12m +
            self.weight_ma200 * norm_ma200 +
            self.weight_vol * norm_vol
        )
        
        # Store normalized components for analysis
        df['norm_6m'] = norm_6m
        df['norm_12m'] = norm_12m
        df['norm_vol'] = norm_vol
        
        return df
    
    def get_top_n(self, ranked_df: pd.DataFrame, n: int = 20) -> pd.DataFrame:
        """
        Get top N stocks from ranked DataFrame.
        
        Args:
            ranked_df: DataFrame from rank_stocks()
            n: Number of top stocks to return
            
        Returns:
            DataFrame with top N stocks
        """
        return ranked_df.head(n).copy()
    
    def get_momentum_leaders(self, ranked_df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
        """
        Get top N stocks by 6-month momentum only.
        
        Args:
            ranked_df: DataFrame from rank_stocks()
            n: Number of stocks to return
            
        Returns:
            DataFrame with top momentum stocks
        """
        df = ranked_df.copy()
        df = df.sort_values('momentum_6m', ascending=False)
        df['momentum_rank'] = range(1, len(df) + 1)
        return df.head(n)
    
    def get_trend_filtered(self, ranked_df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
        """
        Get top N stocks that are above MA200, sorted by score.
        
        Args:
            ranked_df: DataFrame from rank_stocks()
            n: Number of stocks to return
            
        Returns:
            DataFrame with trend-filtered stocks
        """
        df = ranked_df[ranked_df['above_ma200'] == 1].copy()
        
        if df.empty:
            self.logger.warning("No stocks above MA200")
            return pd.DataFrame()
        
        df = df.sort_values('score', ascending=False)
        df['trend_rank'] = range(1, len(df) + 1)
        return df.head(n)
    
    def create_portfolio_snapshot(self, top_stocks: pd.DataFrame) -> pd.DataFrame:
        """
        Create equal-weight portfolio snapshot.
        
        Args:
            top_stocks: DataFrame with selected stocks
            
        Returns:
            DataFrame with portfolio weights
        """
        df = top_stocks.copy()
        n = len(df)
        
        if n == 0:
            return pd.DataFrame()
        
        df['equal_weight'] = 1.0 / n
        
        # Select key columns for portfolio
        portfolio_cols = [
            'symbol', 'rank', 'score', 'equal_weight', 
            'momentum_6m', 'momentum_12m', 'above_ma200',
            'volatility', 'current_price'
        ]
        
        # Include only available columns
        available_cols = [col for col in portfolio_cols if col in df.columns]
        
        return df[available_cols]
    
    def add_relative_strength(self, df: pd.DataFrame, 
                             rs_dict: Dict[str, float]) -> pd.DataFrame:
        """
        Add relative strength scores to ranked DataFrame.
        
        Args:
            df: Ranked DataFrame
            rs_dict: Dict mapping symbol to relative strength
            
        Returns:
            DataFrame with added 'rel_strength' column
        """
        df = df.copy()
        df['rel_strength'] = df['symbol'].map(rs_dict)
        return df
    
    def get_summary_stats(self, ranked_df: pd.DataFrame) -> Dict[str, any]:
        """
        Calculate summary statistics for ranked stocks.
        
        Args:
            ranked_df: DataFrame from rank_stocks()
            
        Returns:
            Dict with summary statistics
        """
        if ranked_df.empty:
            return {}
        
        stats = {
            'total_stocks': len(ranked_df),
            'avg_momentum_6m': ranked_df['momentum_6m'].mean(),
            'avg_momentum_12m': ranked_df['momentum_12m'].mean(),
            'avg_volatility': ranked_df['volatility'].mean(),
            'pct_above_ma200': (ranked_df['above_ma200'].sum() / len(ranked_df)) * 100,
            'top_score': ranked_df['score'].iloc[0] if len(ranked_df) > 0 else np.nan,
            'median_score': ranked_df['score'].median()
        }
        
        return stats
