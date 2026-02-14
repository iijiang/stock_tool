"""
Helper script to generate S&P 500 stock list from Wikipedia.

Usage:
    python helper_generate_sp500.py
    
Output:
    stock_pool/sp500_full.csv
"""
import pandas as pd
from pathlib import Path


def generate_sp500_list():
    """Fetch S&P 500 constituents from Wikipedia and save to CSV."""
    print("Fetching S&P 500 list from Wikipedia...")
    
    try:
        # Wikipedia maintains an updated list
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        tables = pd.read_html(url)
        
        # First table contains the constituents
        sp500_table = tables[0]
        
        # Extract symbols
        symbols = sp500_table[['Symbol']].copy()
        
        # Clean symbols (some may have extra characters)
        symbols['Symbol'] = symbols['Symbol'].str.strip()
        
        # Save to CSV
        output_path = Path(__file__).parent.parent / 'stock_pool' / 'sp500_full.csv'
        symbols.to_csv(output_path, index=False)
        
        print(f"✓ Successfully saved {len(symbols)} S&P 500 symbols to {output_path}")
        print(f"\nTo use: python -m src.main --universe stock_pool/sp500_full.csv")
        
    except Exception as e:
        print(f"Error fetching S&P 500 list: {e}")
        print("\nAlternative: Manually create sp500_full.csv with Symbol column")


if __name__ == '__main__':
    generate_sp500_list()
