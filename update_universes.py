#!/usr/bin/env python3
"""
Update sp500.csv and midcap.csv from ETF holdings files.

This extracts:
- ALL holdings from SPY (S&P 500) - typically ~500 stocks
- Top 30 holdings from IJH (iShares Mid-Cap) for focused mid-cap exposure

The system will then dynamically select top N stocks based on momentum/score.
"""
import pandas as pd
from pathlib import Path

# Paths
stock_pool_dir = Path(__file__).parent / "stock_pool"
spy_file = stock_pool_dir / "holdings-daily-us-en-spy.xlsx"
ijh_file = stock_pool_dir / "IJH_holdings.csv"
sp500_output = stock_pool_dir / "sp500.csv"
midcap_output = stock_pool_dir / "midcap.csv"

def extract_spy_all():
    """Extract ALL holdings from SPY Excel file."""
    print("📊 Reading SPY holdings (all ~500 stocks)...")
    
    # Read Excel file, first row has headers
    df = pd.read_excel(spy_file, skiprows=4, header=0)
    
    # The ticker column should be 'Ticker'
    if 'Ticker' not in df.columns:
        # Print columns for debugging
        print(f"   Available columns: {df.columns.tolist()}")
        raise ValueError("Could not find 'Ticker' column in SPY file")
    
    # Filter out any NaN rows
    df = df[df['Ticker'].notna()]
    
    # Get ALL tickers
    all_tickers = df['Ticker'].tolist()
    
    print(f"   ✓ Found {len(all_tickers)} SPY holdings")
    return all_tickers

def extract_ijh_top30():
    """Extract top 30 holdings from IJH CSV file."""
    print("📊 Reading IJH (Mid-Cap) holdings...")
    
    # Read CSV file, skip header rows
    df = pd.read_csv(ijh_file, skiprows=10)
    
    # Filter for equity holdings only
    if 'Type' in df.columns:
        df = df[df['Type'] == 'EQUITY']
    
    # Get ticker column
    ticker_col = 'Ticker' if 'Ticker' in df.columns else df.columns[0]
    
    # Already sorted by weight, get top 30
    top30 = df.head(30)[ticker_col].tolist()
    
    # Clean tickers (remove quotes and whitespace)
    top30 = [str(t).strip().strip('"') for t in top30 if pd.notna(t)]
    
    print(f"   ✓ Found {len(top30)} IJH holdings")
    return top30

def save_csv(tickers, output_file):
    """Save tickers to CSV file."""
    df = pd.DataFrame({'Symbol': tickers})
    df.to_csv(output_file, index=False)
    print(f"   ✓ Saved {len(tickers)} tickers to {output_file.name}")

def main():
    print("=" * 60)
    print("  UPDATING STOCK UNIVERSES FROM ETF HOLDINGS")
    print("=" * 60)
    print()
    
    # Extract ALL from SPY (full S&P 500)
    spy_tickers = extract_spy_all()
    save_csv(spy_tickers, sp500_output)
    print()
    
    # Extract top 30 from IJH (focused mid-cap)
    ijh_tickers = extract_ijh_top30()
    save_csv(ijh_tickers, midcap_output)
    print()
    
    # Show combined stats
    combined = set(spy_tickers + ijh_tickers)
    print("=" * 60)
    print(f"  ✅ COMPLETE")
    print("=" * 60)
    print(f"SP500 tickers:    {len(spy_tickers)} (full universe)")
    print(f"MidCap tickers:   {len(ijh_tickers)} (top 30)")
    print(f"Combined unique:  {len(combined)}")
    print()
    
    # Show first 10 of each
    print("SP500 Top 10:", ', '.join(spy_tickers[:10]))
    print("MidCap Top 10:", ', '.join(ijh_tickers[:10]))
    print()
    print("💡 Usage:")
    print("   python -m src.main --mode screen --universe sp500 --top 30")
    print("   python -m src.main --mode backtest --universe sp500 --top 10")
    print()

if __name__ == "__main__":
    main()
