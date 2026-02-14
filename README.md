# Stock Screening & Observation CLI Tool

A production-quality, modular Python CLI tool for screening and observing US stocks with no live trading. Built with clean architecture, intelligent caching, and extensible design.

## Features

- **Multi-factor Stock Ranking**: Composite scoring system with momentum, trend, and volatility factors
- **Intelligent Caching**: SQLite-based incremental updates (fetch only missing data)
- **Technical Indicators**: 6M/12M momentum, MA50/200, volatility, max drawdown, relative strength
- **Flexible Universe**: Start with S&P 500, easily extend to mid-cap stocks
- **Multiple Rankings**: Overall top 20, momentum leaders, trend-filtered stocks
- **Portfolio Snapshots**: Equal-weight portfolio generation
- **Data Source**: Uses yfinance for reliable market data
- **Comprehensive Output**: Console tables + timestamped CSV files

## Requirements

- Python 3.10+
- Internet connection for initial data download
- Dependencies: pandas, numpy, yfinance, matplotlib, tqdm

## Installation

### 1. Clone or Download

```bash
cd /path/to/stock_tool
```

### 2. Create Virtual Environment

```bash
# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## Quick Start

### Basic Usage

Run with the default S&P 500 demo universe (30 stocks):

```bash
python -m src.main --universe stock_pool/sp500.csv
```

This will:
1. Download historical data from 2010-01-01 (or update cache)
2. Calculate technical indicators
3. Rank all stocks by composite score
4. Display three tables: Top 20 Overall, Top 10 Momentum, Top 10 Trend-Filtered
5. Save results to `output/` directory

### Common Commands

```bash
# Get top 30 stocks
python -m src.main --universe stock_pool/sp500.csv --top 30

# Force refresh all data (bypass cache)
python -m src.main --universe stock_pool/sp500.csv --refresh

# Custom start date
python -m src.main --universe stock_pool/sp500.csv --start-date 2015-01-01

# Use different benchmark
python -m src.main --universe stock_pool/sp500.csv --benchmark QQQ

# Disable progress bar
python -m src.main --universe stock_pool/sp500.csv --no-progress

# Debug mode
python -m src.main --universe stock_pool/sp500.csv --log-level DEBUG
```

## Project Structure

```
stock_tool/
├── src/
│   ├── __init__.py          # Package initialization
│   ├── config.py            # Configuration management
│   ├── cache.py             # SQLite caching layer
│   ├── data_fetcher.py      # yfinance wrapper with caching
│   ├── indicators.py        # Technical indicator calculations
│   ├── ranking.py           # Multi-factor ranking system
│   ├── reporting.py         # Console/CSV output
│   ├── main.py              # CLI entry point
│   └── utils.py             # Helper functions
├── stock_pool/
│   └── sp500.csv            # Stock universe (Symbol column)
├── output/                  # Generated reports (auto-created)
│   ├── ranking_YYYY-MM-DD.csv
│   └── top10_portfolio_YYYY-MM-DD.csv
├── cache/                   # SQLite cache (auto-created)
│   └── stock_data.db
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Configuration

Default settings in `src/config.py`:

```python
start_date = "2010-01-01"
benchmark_symbol = "SPY"

# Lookback windows (trading days)
momentum_6m_days = 126
momentum_12m_days = 252
ma_short = 50
ma_long = 200

# Ranking weights (must sum to 1.0)
weight_6m_momentum = 0.40    # 40%
weight_12m_momentum = 0.30   # 30%
weight_above_ma200 = 0.20    # 20%
weight_volatility = 0.10     # 10%

# Top N settings
top_overall = 20
top_momentum = 10
top_trend = 10
```

Override via CLI arguments or edit `config.py` directly.

## Indicators Explained

### Momentum Indicators
- **6M Momentum**: Return over ~126 trading days (6 months)
- **12M Momentum**: Return over ~252 trading days (12 months)
- **Relative Strength**: 6M return vs benchmark (SPY)

### Trend Indicators
- **MA50**: 50-day moving average
- **MA200**: 200-day moving average
- **Above MA200**: Boolean (1 if price > MA200, else 0)

### Risk Indicators
- **Volatility**: Annualized standard deviation of daily returns
- **Max Drawdown**: Maximum peak-to-trough decline

## Ranking System

### Composite Score Formula

```
Score = 0.40 × norm(6M_momentum) 
      + 0.30 × norm(12M_momentum) 
      + 0.20 × above_MA200 
      + 0.10 × norm(volatility_inverted)
```

Where:
- `norm()` = min-max normalization to [0, 1]
- `volatility_inverted` = prefer lower volatility

### Three Output Rankings

1. **Overall Top 20**: By composite score
2. **Momentum Top 10**: By 6M momentum only (ignoring other factors)
3. **Trend-Filtered Top 10**: Only stocks above MA200, sorted by score

## Output Files

### ranking_YYYY-MM-DD.csv
Complete ranking of all stocks with columns:
- rank, symbol, score
- momentum_6m, momentum_12m
- above_ma200, volatility
- ma50, ma200, max_drawdown, current_price

### top10_portfolio_YYYY-MM-DD.csv
Top 10 stocks portfolio snapshot:
- symbol, rank, score, equal_weight (1/10 = 10% each)
- momentum metrics, technical levels

## Caching Behavior

### How Cache Works

1. **First Run**: Downloads all data from `start_date` to today
2. **Subsequent Runs**: Only fetches missing recent days (incremental update)
3. **Cache Check**: Auto-updates if last cached date is >2 days old
4. **Force Refresh**: Use `--refresh` flag to re-download everything

### Cache Location

SQLite database: `cache/stock_data.db`

### Cache Management

```bash
# Clear cache for fresh download
rm -rf cache/

# Incremental update (automatic)
python -m src.main --universe stock_pool/sp500.csv

# Force refresh specific run
python -m src.main --universe stock_pool/sp500.csv --refresh
```

## Stock Universe Management

### Using Default sp500.csv

Included demo file has 30 major stocks. Run as-is for testing.

### Creating Custom Universe

Create CSV with `Symbol` column:

```csv
Symbol
AAPL
MSFT
GOOGL
...
```

Then run:

```bash
python -m src.main --universe stock_pool/my_custom_universe.csv
```

### Adding Mid-Cap Universe

1. Create `stock_pool/midcap.csv` with mid-cap ticker symbols
2. Run: `python -m src.main --universe stock_pool/midcap.csv`

The tool automatically handles any universe file with the same structure.

### Generating S&P 500 List from Wikipedia

Optional helper script (requires beautifulsoup4):

```python
# helper_scripts/generate_sp500.py
import pandas as pd

# Fetch from Wikipedia
url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
tables = pd.read_html(url)
sp500 = tables[0]

# Save symbols
symbols = sp500[['Symbol']]
symbols.to_csv('stock_pool/sp500_full.csv', index=False)
print(f"Saved {len(symbols)} S&P 500 symbols")
```

## Data Quality & Error Handling

### Automatic Handling
- **Missing Data**: Stocks with insufficient history are skipped (logged)
- **Delisted Tickers**: Gracefully handled, excluded from ranking
- **API Failures**: Individual failures don't crash the tool
- **Short History**: Requires minimum 252 trading days (configurable)

### Validation Rules
- Min 252 days of data (12 months)
- Max 10% missing values in adj_close
- Valid OHLCV data from yfinance

### Common Issues

**No data returned**
- Check internet connection
- Verify ticker symbols are correct (uppercase, no spaces)
- Try `--refresh` flag

**yfinance reliability**
- Yahoo Finance may occasionally have outages
- Some tickers may not have full history
- Data may be delayed by 15-20 minutes

## Extensibility

### Adding New Indicators

Edit `src/indicators.py`:

```python
def calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> float:
    """Calculate RSI indicator."""
    delta = df['adj_close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs.iloc[-1]))
```

### Modifying Ranking Weights

Edit `src/config.py`:

```python
weight_6m_momentum = 0.35
weight_12m_momentum = 0.25
weight_above_ma200 = 0.20
weight_volatility = 0.20  # Increased weight
# Must sum to 1.0
```

### Adding New Rankings

Edit `src/ranking.py`:

```python
def get_low_volatility_leaders(self, ranked_df: pd.DataFrame, n: int = 10):
    """Get top N by lowest volatility."""
    df = ranked_df.copy()
    df = df.sort_values('volatility', ascending=True)
    return df.head(n)
```

## Performance

### Typical Run Times
- **First run** (30 stocks, downloading 14 years): ~30-60 seconds
- **Subsequent runs** (incremental update): ~5-10 seconds
- **Full S&P 500** (500 stocks, first run): ~10-15 minutes
- **Full S&P 500** (incremental): ~1-2 minutes

Use `--no-progress` flag for faster execution in scripts.

## Testing

### Manual Testing

```bash
# Test with demo universe
python -m src.main --universe stock_pool/sp500.csv

# Test cache refresh
python -m src.main --universe stock_pool/sp500.csv --refresh

# Test different date range
python -m src.main --universe stock_pool/sp500.csv --start-date 2020-01-01

# Test single symbol (create test.csv with one ticker)
echo "Symbol\nAAPL" > test_single.csv
python -m src.main --universe test_single.csv
```

### Expected Output

Console should show:
1. Report header with timestamp
2. TOP 20 STOCKS table
3. TOP 10 MOMENTUM LEADERS table
4. TOP 10 TREND-FILTERED STOCKS table
5. SUMMARY STATISTICS
6. Files saved confirmation

Output directory should contain:
- `ranking_YYYY-MM-DD.csv` (all stocks)
- `top10_portfolio_YYYY-MM-DD.csv` (top 10 with weights)

## Troubleshooting

### ImportError: No module named 'src'

Make sure to run from the `stock_tool` directory with `-m` flag:

```bash
cd stock_tool
python -m src.main --universe stock_pool/sp500.csv
```

### SSL Certificate Errors

Update certifi:

```bash
pip install --upgrade certifi
```

### yfinance Warnings

Warnings like "Failed to get ticker..." are normal for:
- Recently delisted stocks
- Ticker symbol changes
- Temporary API issues

The tool logs these and continues with remaining stocks.

### Empty Output

Check logs for:
- Invalid universe file path
- No symbols in CSV
- All stocks failed validation (increase `--start-date` to recent date)

## Logging

### Log Levels

- **DEBUG**: Detailed execution info (cache hits, data validation)
- **INFO**: General progress (default)
- **WARNING**: Skipped stocks, data issues
- **ERROR**: Failures that don't crash the tool

### Enable Debug Logging

```bash
python -m src.main --universe stock_pool/sp500.csv --log-level DEBUG
```

Logs print to console with timestamps.

## Future Enhancements

Potential additions (not yet implemented):
- [ ] Backtesting engine with historical portfolios
- [ ] Cumulative return charts (matplotlib)
- [ ] Sector/industry grouping analysis
- [ ] Fundamental data integration (P/E, EPS growth)
- [ ] Risk-adjusted return metrics (Sharpe, Sortino)
- [ ] Export to Excel with formatting
- [ ] Web dashboard (Flask/Streamlit)
- [ ] Scheduled runs with cron
- [ ] Alert system for ranking changes

## License

This is a demo/educational tool. Use at your own risk. Not financial advice.

## Support

For issues or questions:
1. Check this README thoroughly
2. Review log output with `--log-level DEBUG`
3. Verify yfinance is working: `python -c "import yfinance; print(yfinance.__version__)"`

## Credits

- **Data Source**: [yfinance](https://github.com/ranaroussi/yfinance) (Yahoo Finance API)
- **Architecture**: Clean separation of concerns, modular design
- **Caching**: SQLite for efficient incremental updates

---

**Disclaimer**: This tool is for observation and screening purposes only. It does not provide investment advice and is not intended for live trading. Always do your own research and consult financial professionals before making investment decisions.
