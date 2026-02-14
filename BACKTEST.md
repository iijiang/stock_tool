# Monthly Rotation Backtest System

## Overview

This backtesting engine simulates a **monthly rotation strategy** that:
- Ranks stocks using the same composite scoring logic as the screener
- Rebalances monthly to hold the top N stocks (equal-weighted)
- Implements a regime filter: moves to 100% cash when SPY < MA200
- Tracks performance with full transaction cost accounting

## Strategy Logic

### Composite Scoring (Same as Screener)
- **40%** - 6-month momentum (126-day return)
- **30%** - 12-month momentum (252-day return)
- **20%** - Above MA200 (1 if price > MA200, else 0)
- **10%** - Lower volatility (inverted 60-day standard deviation)

### Regime Filter
When SPY closes below its 200-day moving average → move to 100% cash (risk-off mode).

### Rebalancing
- **Frequency:** Monthly (on last trading day of each month)
- **Selection:** Top N stocks by composite score
- **Weighting:** Equal-weight across selected stocks
- **Lookback:** Minimum 252 trading days of history required

## Usage

### Basic Command
```bash
./venv/bin/python -m src.main --mode backtest \
  --universe stock_pool/sp500.csv \
  --top 10 \
  --start-date 2022-01-01
```

### With Transaction Costs
```bash
./venv/bin/python -m src.main --mode backtest \
  --universe stock_pool/sp500.csv \
  --top 10 \
  --start-date 2022-01-01 \
  --tx-cost-bps 5
```

### Parameters
- `--mode backtest` - Run backtest mode (vs `screen` for regular screening)
- `--universe` - Path to stock universe CSV file
- `--top` - Number of stocks to hold (default: 10)
- `--start-date` - Backtest start date (YYYY-MM-DD format)
- `--tx-cost-bps` - Transaction cost in basis points (default: 0)
- `--benchmark` - Benchmark ticker (default: SPY)
- `--refresh` - Force refresh all data from Yahoo Finance
- `--no-progress` - Hide progress bars

## Output Files

All backtest results are saved to `output/backtest/` with timestamp:

### 1. Monthly Returns CSV
**File:** `backtest_monthly_returns_YYYY-MM-DD.csv`

Contains month-by-month performance data:
- `date` - Month-end date
- `portfolio_value` - Portfolio value at month-end
- `cash_pct` - Percentage of portfolio in cash
- `monthly_return` - Return for the month
- `spy_close` - SPY closing price
- `spy_ma200` - SPY 200-day moving average
- `in_cash_mode` - Boolean indicating if regime filter triggered

### 2. Summary JSON
**File:** `backtest_summary_YYYY-MM-DD.json`

Complete performance statistics:
```json
{
  "start_date": "2022-02-28",
  "end_date": "2026-02-13",
  "years": 4.08,
  "n_months": 49,
  "total_return": 0.7258,
  "cagr": 0.1430,
  "annualized_volatility": 0.1203,
  "sharpe_ratio": 1.18,
  "max_drawdown": -0.0943,
  "win_rate": 0.4694,
  "best_month": 0.1173,
  "worst_month": -0.0659,
  "pct_months_in_cash": 0.1020,
  "spy_total_return": 0.6019,
  "spy_cagr": 0.1223,
  "outperformance": 0.1239
}
```

### 3. Equity Curve Chart
**File:** `equity_curve_YYYY-MM-DD.png`

Visual representation showing:
- Portfolio value over time (blue line)
- SPY benchmark comparison (orange line)
- Monthly rebalancing points (blue dots)
- Cash-only periods (red dots)

## Performance Metrics Explained

| Metric | Description |
|--------|-------------|
| **Total Return** | Cumulative return from start to end |
| **CAGR** | Compound Annual Growth Rate (annualized return) |
| **Annualized Volatility** | Standard deviation of monthly returns × √12 |
| **Sharpe Ratio** | CAGR ÷ Volatility (risk-adjusted returns, 0% risk-free rate) |
| **Maximum Drawdown** | Largest peak-to-trough decline |
| **Win Rate** | Percentage of months with positive returns |
| **% Months in Cash** | Percentage of time regime filter was active |
| **Outperformance** | Total return vs SPY benchmark |

## Example Results

Using S&P 500 universe (30 stocks sample), Top 10 portfolio, 2022-2026:

```
Period:                 2022-02-28 to 2026-02-13 (4.08 years)
Total Return:           +72.58%  (vs SPY +60.19%)
CAGR:                   14.30%   (vs SPY 12.23%)
Sharpe Ratio:           1.18
Max Drawdown:           -9.43%
Win Rate:               46.94%
Months in Cash:         10.20%
Outperformance:         +12.39%
```

**Key Insight:** The strategy delivered 14.3% CAGR with a Sharpe ratio of 1.18, outperforming SPY by 12.4 percentage points over 4+ years while maintaining lower drawdowns.

## Data Requirements

- **Minimum History:** 252 trading days (1 year) before backtest start
- **Data Source:** Yahoo Finance via yfinance
- **Caching:** SQLite database stores historical data for faster reruns
- **Validation:** Automatically skips stocks with insufficient data quality

## Technical Implementation

### Point-in-Time Data Handling
- All indicators calculated using data available **at rebalancing date only**
- No look-ahead bias (peeking at future data)
- Forward-fills missing data to simulate real-world constraints

### Transaction Costs
- Applied on both buys and sells
- Calculated as: `cost = abs(trade_value) * (tx_cost_bps / 10000)`
- Deducted from portfolio cash immediately

### Regime Filter Logic
```python
if spy_close < spy_ma200:
    # Sell all positions, hold 100% cash
    # Avoid whipsaws with clear entry/exit rules
```

## Troubleshooting

### "No symbols loaded from universe file"
- Check that CSV file exists and contains valid ticker symbols
- Verify path is correct (relative to project root)

### "Benchmark data required for backtest"
- SPY data is mandatory for regime filter
- Check internet connection or use `--refresh` flag

### "ModuleNotFoundError: No module named 'pandas'"
- Activate virtual environment: `source venv/bin/activate`
- Or use venv Python directly: `./venv/bin/python -m src.main ...`

### Syntax errors after editing
- Run validation: `./venv/bin/python -m py_compile src/main.py`
- Check for unclosed quotes, parentheses, or indentation issues

## Extending the Backtest

### Adding New Metrics
Edit `src/backtest.py` → `compute_performance_metrics()` function

### Modifying Scoring Weights
Edit `src/config.py` → adjust `weight_6m_momentum`, `weight_12m_momentum`, etc.

### Testing Different Rebalancing Frequencies
Edit `src/backtest.py` → `get_month_ends()` function to use weekly/quarterly dates

### Disabling Regime Filter
Currently always enabled. To make optional, modify `run_backtest()` in `src/main.py`

## Validation

The backtest engine has been validated against:
- ✅ Point-in-time data integrity (no look-ahead bias)
- ✅ Transaction cost accounting accuracy
- ✅ Benchmark comparison calculations
- ✅ Drawdown computation correctness
- ✅ Monthly return aggregation

## References

- Data source: [Yahoo Finance](https://finance.yahoo.com/) via [yfinance](https://github.com/ranaroussi/yfinance)
- Strategy concept: Monthly momentum rotation with regime filtering
- Risk management: Moving average-based trend filter

---

For questions or issues, review the logs in the terminal output or check `src/utils.py` logging configuration.
