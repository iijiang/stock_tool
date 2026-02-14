"""
Quick validation script to verify installation and basic functionality.

Run this after setup to ensure everything is working correctly.
"""
import sys
from pathlib import Path

def validate_installation():
    """Validate that all components are properly installed."""
    print("=" * 60)
    print("Stock Screening Tool - Validation")
    print("=" * 60)
    
    errors = []
    warnings = []
    
    # Check Python version
    print("\n1. Checking Python version...")
    if sys.version_info < (3, 10):
        errors.append(f"Python 3.10+ required, found {sys.version_info.major}.{sys.version_info.minor}")
    else:
        print(f"   ✓ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    
    # Check dependencies
    print("\n2. Checking dependencies...")
    required_packages = ['pandas', 'numpy', 'yfinance', 'matplotlib', 'tqdm']
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"   ✓ {package}")
        except ImportError:
            errors.append(f"Missing package: {package}")
            print(f"   ✗ {package} - NOT FOUND")
    
    # Check project structure
    print("\n3. Checking project structure...")
    project_root = Path(__file__).parent
    
    required_files = [
        'src/__init__.py',
        'src/config.py',
        'src/cache.py',
        'src/data_fetcher.py',
        'src/indicators.py',
        'src/ranking.py',
        'src/reporting.py',
        'src/main.py',
        'src/utils.py',
        'stock_pool/sp500.csv',
        'requirements.txt',
        'README.md'
    ]
    
    for file_path in required_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"   ✓ {file_path}")
        else:
            errors.append(f"Missing file: {file_path}")
            print(f"   ✗ {file_path} - NOT FOUND")
    
    # Check import of main module
    print("\n4. Checking module imports...")
    try:
        from src.config import config
        print("   ✓ src.config")
        
        from src.cache import StockCache
        print("   ✓ src.cache")
        
        from src.data_fetcher import DataFetcher
        print("   ✓ src.data_fetcher")
        
        from src.indicators import IndicatorCalculator
        print("   ✓ src.indicators")
        
        from src.ranking import StockRanker
        print("   ✓ src.ranking")
        
        from src.reporting import Reporter
        print("   ✓ src.reporting")
        
    except ImportError as e:
        errors.append(f"Import error: {e}")
        print(f"   ✗ Import failed: {e}")
    
    # Check universe file
    print("\n5. Checking universe file...")
    universe_file = project_root / 'stock_pool' / 'sp500.csv'
    if universe_file.exists():
        import pandas as pd
        try:
            df = pd.read_csv(universe_file)
            if 'Symbol' in df.columns:
                n_symbols = len(df)
                print(f"   ✓ Universe file valid with {n_symbols} symbols")
            else:
                errors.append("Universe file missing 'Symbol' column")
                print("   ✗ Universe file missing 'Symbol' column")
        except Exception as e:
            errors.append(f"Error reading universe file: {e}")
            print(f"   ✗ Error reading file: {e}")
    
    # Print summary
    print("\n" + "=" * 60)
    if errors:
        print("VALIDATION FAILED")
        print("=" * 60)
        print("\nErrors found:")
        for error in errors:
            print(f"  - {error}")
        print("\nPlease fix these issues before running the tool.")
        return False
    elif warnings:
        print("VALIDATION PASSED (with warnings)")
        print("=" * 60)
        print("\nWarnings:")
        for warning in warnings:
            print(f"  - {warning}")
        print("\nThe tool should work, but consider addressing these warnings.")
        return True
    else:
        print("VALIDATION PASSED")
        print("=" * 60)
        print("\n✓ All checks passed! The tool is ready to use.")
        print("\nTo run:")
        print("  python -m src.main --universe stock_pool/sp500.csv")
        return True


if __name__ == '__main__':
    success = validate_installation()
    sys.exit(0 if success else 1)
