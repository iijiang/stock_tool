# Quick Start Guide

## 1. Setup (First Time Only)

```bash
cd /Users/yi/finance/stock_tool

# Option A: Use setup script (macOS/Linux)
./setup.sh

# Option B: Manual setup
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Validate Installation

```bash
source venv/bin/activate  # If not already activated
python validate.py
```

You should see "VALIDATION PASSED" ✓

## 3. Run the Tool

```bash
# Basic run with demo universe (30 stocks)
python -m src.main --universe stock_pool/sp500.csv

# This will take 30-60 seconds on first run (downloading data)
# Subsequent runs are much faster (5-10 seconds)
```

## 4. Expected Output

You should see:
- Report header with timestamp
- TOP 20 STOCKS (by Composite Score)
- TOP 10 MOMENTUM LEADERS (by 6M Return)
- TOP 10 TREND-FILTERED STOCKS (Above MA200)
- SUMMARY STATISTICS
- Files saved confirmation

Check the `output/` directory for CSV files.

## 5. Common Commands

```bash
# Get top 30 stocks
python -m src.main --universe stock_pool/sp500.csv --top 30

# Force refresh all data
python -m src.main --universe stock_pool/sp500.csv --refresh

# Different date range
python -m src.main --universe stock_pool/sp500.csv --start-date 2020-01-01

# Help
python -m src.main --help
```

## 6. Generate Full S&P 500 List

```bash
# Optional: Get all 500+ stocks from Wikipedia
cd helper_scripts
python generate_sp500.py
cd ..

# Then run with full list
python -m src.main --universe stock_pool/sp500_full.csv
```

This will take 10-15 minutes on first run.

## Troubleshooting

**Import errors**: Make sure you're in the stock_tool directory and virtual environment is activated

**No data returned**: Check internet connection, try `--refresh` flag

**SSL errors**: Update certifi: `pip install --upgrade certifi`

See README.md for comprehensive documentation.
