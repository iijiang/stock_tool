# Monthly Rotation Backtest - User Guide

## Overview

The backtest mode simulates a monthly rotation strategy using the same indicators and scoring logic as the screening tool, with an optional market regime filter.

## Strategy Description

### Monthly Rebalancing

- **Schedule**: End of each month (last trading day)
- **Portfolio Size**: Top N stocks (default: 10)
- **Position Sizing**: Equal-weight (1/N per stock)
- **Transaction Costs**: Optional (specify with `--tx-cost-bps`)

### Selection Process

At each month-end rebalance date:

1. **Compute Indicators** using only data available up to that date (no look-ahead bias):
   - 6M momentum (40% weight)
   - 12M momentum (30% weight)
   - Above MA200 (20% weight)
   - Lower volatility (10% weight)

2. **Rank Stocks** by composite score

3. **Select Top N** stocks for next month

4. **Check Regime Filter**:
   - If SPY adj_close < SPY MA200: Go 100% cash for next month
   - Otherwise: Hold equal-weight portfolio of selected stocks

5. **Calculate Returns** for the month ahead using actual price changes

### Performance Metrics

- **CAGR** (Compound Annual Growth Rate)
- **Total Return**
- **Annualized Volatility**
- **Sharpe Ratio** (risk-free rate = 0%)
- **Maximum Drawdown**
- **Win Rate** (% of positive months)
- **% Months in Cash** (due to regime filter)
- **Best/Worst Month**
- **Outperformance vs SPY**

## Usage

### Basic Backtest

```bash
python -m src.main --mode backtest --universe stock_pool/sp500.csv
```

This uses defaults:
- Start date: 2010-01-01
- Portfolio size: Top 10 stocks
- Regime filter: Enabled
- Transaction costs: 0 bps

### Custom Parameters

```bash
# Custom date range and portfolio size
python -m src.main --mode backtest \
  --universe stock_pool/sp500.csv \
  --start-date 2015-01-01 \
  --top 15

# With transaction costs (10 basis points)
python -m src.main --mode backtest \
  --universe stock_pool/sp500.csv \
  --top 10 \
  --tx-cost-bps 10

# Force refresh data
python -m src.main --mode backtest \
  --universe stock_pool/sp500.csv \
  --refresh
```

## Output Files

All backtest outputs are saved to `output/backtest/` directory:

### 1. Monthly Returns CSV

**File**: `backtest_monthly_returns_YYYY-MM-DD.csv`

Columns:
- `date`: End of month date
- `portfolio_return`: Portfolio return for that month (decimal)
- `spy_return`: SPY benchmark return (decimal)
- `in_cash`: 1 if regime filter triggered, 0 otherwise
- `selected_symbols`: Comma-separated list of selected stocks
- `n_selected`: Number of stocks actually selected (may be < N)

Example:
```csv
date,portfolio_return,spy_return,in_cash,selected_symbols,n_selected
2010-01-31,0.0523,0.0387,0,"AAPL,MSFT,GOOGL,AMZN,NVDA",5
2010-02-28,0.0312,0.0285,0,"AAPL,TSLA,META,NVDA,JPM",5
2010-03-31,0.0000,0.0612,1,"",0
```

### 2. Summary JSON

**File**: `backtest_summary_YYYY-MM-DD.json`

Contains:
```json
{
  "start_date": "2010-01-31",
  "end_date": "2026-02-28",
  "n_months": 193,
  "years": 16.08,
  "total_return": 2.4532,
  "cagr": 0.0827,
  "annualized_volatility": 0.1542,
  "sharpe_ratio": 0.536,
  "max_drawdown": -0.2347,
  "win_rate": 0.6322,
  "best_month": 0.1523,
  "worst_month": -0.1245,
  "pct_months_in_cash": 0.1865,
  "spy_total_return": 1.8523,
  "spy_cagr": 0.0645,
  "outperformance": 0.6009
}
```

### 3. Equity Curve Chart

**File**: `equity_curve_YYYY-MM-DD.png`

Visual comparison of portfolio vs SPY benchmark:
- X-axis: Time (monthly)
- Y-axis: Growth of $100
- Blue line: Portfolio (monthly rotation + regime filter)
- Red dashed line: SPY benchmark (buy & hold)

## Console Output

The backtest prints a comprehensive summary to console:

```
================================================================================
MONTHLY ROTATION BACKTEST
================================================================================
Universe: 30 stocks from sp500.csv
Portfolio Size: Top 10 (equal-weight)
Start Date: 2010-01-01
Regime Filter: ENABLED (SPY < MA200 → Cash)
Transaction Cost: 0.0 bps
================================================================================

[... processing logs ...]

================================================================================
BACKTEST PERFORMANCE SUMMARY
================================================================================

Period                                           Value
────────────────────────────────────────────────────────────────────────────
Start Date                                  2010-01-31
End Date                                    2026-02-28
Duration (years)                                 16.08
Number of Months                                   193

Portfolio Performance                            Value
────────────────────────────────────────────────────────────────────────────
Total Return                                    245.32%
CAGR                                              8.27%
Annualized Volatility                            15.42%
Sharpe Ratio (0% RF)                              0.54
Maximum Drawdown                                -23.47%

Monthly Statistics                               Value
────────────────────────────────────────────────────────────────────────────
Win Rate                                         63.22%
Best Month                                       15.23%
Worst Month                                     -12.45%
% Months in Cash                                 18.65%

Benchmark (SPY) Comparison                       Value
────────────────────────────────────────────────────────────────────────────
SPY Total Return                                185.23%
SPY CAGR                                          6.45%
Outperformance                                   60.09%
================================================================================
```

## Data Requirements

### Minimum History

Each stock needs at least **252 trading days** (12 months) of data to be included in the universe at any rebalance date.

### Handling Missing Data

- Stocks with insufficient history are **skipped** for that rebalance
- Portfolio holds available stocks (may be < N)
- Logs warnings but does not crash
- Records actual `n_selected` in output

### Survivorship Bias

⚠️ **Important**: The backtest uses the tickers provided in `stock_pool/sp500.csv`, which represents the **current** S&P 500 composition. This introduces survivorship bias as it excludes:
- Companies that were in the index but were delisted
- Companies that were replaced in the index
- Companies that went bankrupt

For academic-quality results, use a point-in-time universe dataset (not included).

## Caching

The backtest uses the same caching system as screening mode:

- **First run**: Downloads all historical data (slow)
- **Subsequent runs**: Uses cached data (fast)
- **Incremental updates**: Only fetches missing recent dates
- **Force refresh**: Use `--refresh` flag

## Understanding Results

### Win Rate

Percentage of months with positive returns. A win rate > 60% is generally strong for a monthly strategy.

### Sharpe Ratio

Risk-adjusted return metric (assuming 0% risk-free rate):
- **< 0**: Negative returns
- **0-0.5**: Poor risk-adjusted returns
- **0.5-1.0**: Good
- **1.0-2.0**: Very good
- **> 2.0**: Excellent (rare)

### Maximum Drawdown

Largest peak-to-trough decline:
- **< 10%**: Very low risk
- **10-20%**: Moderate risk
- **20-30%**: High risk
- **> 30%**: Very high risk

### Regime Filter Impact

- **% Months in Cash**: Shows how often regime filter triggered
- Higher cash percentage = more defensive
- Compare portfolio returns in "cash months" vs "invested months"

### Outperformance

Simple difference: Portfolio Total Return - SPY Total Return

Positive outperformance means the strategy beat buy-and-hold SPY.

## Troubleshooting

### "No valid stocks for backtest"

**Cause**: Start date is too recent; stocks need 252 days of history.

**Solution**: Use earlier start date (e.g., 2010-01-01).

### "Insufficient date range for backtest"

**Cause**: Not enough months between start date and today.

**Solution**: Ensure at least 2-3 months of data available.

### Empty selected_symbols in output

This is **normal** when:
1. Regime filter triggers (in_cash = 1)
2. All stocks lack sufficient data at that rebalance date

Check `n_selected` and `in_cash` columns to diagnose.

### Chart generation fails

**Solution**: Ensure matplotlib is installed:
```bash
pip install matplotlib
```

## Performance Optimization

### Speed Tips

1. **Use caching**: Don't use `--refresh` unless necessary
2. **Smaller universes**: Test with 20-30 stocks first
3. **Shorter periods**: Test with recent years before full backtest
4. **Disable progress bar**: Use `--no-progress` in scripts

### Example Timing

On typical hardware:
- **30 stocks, 2010-2026, first run**: ~30-60 seconds
- **30 stocks, cached data**: ~5-10 seconds
- **500 stocks, 2010-2026, first run**: ~15-20 minutes
- **500 stocks, cached data**: ~30-60 seconds

## Comparison with Screening Mode

| Feature | Screen Mode | Backtest Mode |
|---------|-------------|---------------|
| Purpose | Current snapshot | Historical simulation |
| Output | Today's rankings | Monthly time series |
| Time Period | Single point (now) | Historical range |
| Returns | Not calculated | Actual returns tracked |
| Regime Filter | Informational | Affects allocation |
| Files Created | 2 (ranking + portfolio) | 3 (returns + summary + chart) |

## Examples

### Conservative Backtest (Lower Risk)

```bash
# Use top 20 stocks for diversification
python -m src.main --mode backtest \
  --universe stock_pool/sp500.csv \
  --top 20 \
  --start-date 2010-01-01
```

### Aggressive Backtest (Higher Concentration)

```bash
# Top 5 stocks only
python -m src.main --mode backtest \
  --universe stock_pool/sp500.csv \
  --top 5 \
  --start-date 2015-01-01
```

### Realistic Backtest (With Costs)

```bash
# Include 10 bps transaction cost
python -m src.main --mode backtest \
  --universe stock_pool/sp500.csv \
  --top 10 \
  --tx-cost-bps 10
```

### Recent Period Only

```bash
# Last 3 years
python -m src.main --mode backtest \
  --universe stock_pool/sp500.csv \
  --start-date 2023-01-01
```

## Next Steps

After running backtest:

1. **Analyze the summary JSON** for key metrics
2. **Review monthly returns CSV** to identify patterns
3. **Study the equity curve** for drawdown periods
4. **Compare different parameters** (portfolio size, date ranges)
5. **Test on different universes** (mid-cap, growth stocks, etc.)

## Limitations

1. **Survivorship Bias**: Uses current universe composition
2. **No Position Limits**: Can be 100% in one sector if top stocks align
3. **Execution Assumptions**: Assumes perfect fills at month-end close
4. **No Dividends**: Uses adjusted close (includes dividends)
5. **No Slippage**: Beyond optional tx_cost_bps parameter
6. **No Margin**: Long-only, 100% invested or 100% cash

## Citation

When publishing results:

> "Backtest performed using monthly rotation strategy on [date range] with [N] stock universe. Results include [transaction cost] bps costs and market regime filter (SPY < MA200 → cash). Note: Results reflect survivorship bias due to use of current index composition."

---

For questions or issues, review logs with `--log-level DEBUG` flag.
