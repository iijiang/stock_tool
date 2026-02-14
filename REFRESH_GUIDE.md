# Refresh All Data - Quick Guide

## 📋 Overview

The `refresh_all.sh` script completely regenerates all screening and backtest data with fresh calculations.

## 🚀 Usage

```bash
./refresh_all.sh
```

## 🔄 What It Does

### 1. **Cleans Output Folder**
- Archives old files to `output_archive/<timestamp>/`
- Keeps `dashboard.html` intact

### 2. **Runs Screenings**
- S&P 500: Top 20 stocks
- Mid-Cap: Top 20 stocks

### 3. **Runs Backtests**
- S&P 500 (Top 10)
- Mid-Cap (Top 5)
- Combined (Top 10)
- Combined (Top 20)

### 4. **Generates Outputs**
- Ranking CSVs with top 20
- Portfolio CSVs
- Backtest monthly returns
- Summary JSON files
- Equity curve charts (PNG)
- **manifest.json** - File index for dashboard

## 📊 Dashboard Integration

The script updates `output/manifest.json` which tells the dashboard where to find the latest files. This eliminates hardcoded dates!

After running the script, the dashboard automatically loads the newest data:

```bash
# View dashboard
cd output
python3 -m http.server 8888
# Open: http://localhost:8888/dashboard.html
```

## 📂 File Structure

```
output/
├── manifest.json                          # ← Auto-generated file index
├── dashboard.html                         # ← Interactive dashboard
├── sp500_ranking_2026-02-15.csv          # ← New files with timestamp
├── sp500_top10_portfolio_2026-02-15.csv
├── midcap_ranking_2026-02-15.csv
├── midcap_top10_portfolio_2026-02-15.csv
└── backtest/
    ├── sp500_backtest_summary_2026-02-15.json
    ├── sp500_equity_curve_2026-02-15.png
    ├── midcap_backtest_summary_2026-02-15.json
    ├── midcap_equity_curve_2026-02-15.png
    ├── combined_backtest_summary_2026-02-15.json
    └── combined_equity_curve_2026-02-15.png

output_archive/
└── 2026-02-14_15-30-00/                   # ← Old files archived here
    ├── sp500_ranking_2026-02-14.csv
    └── backtest/
        └── ...
```

## ⏱️ Execution Time

Approximately 2-5 minutes depending on:
- Number of stocks in universe
- Network speed (Yahoo Finance API)
- Cache freshness
- System performance

## 🎯 When to Run

- **Daily:** Get fresh price data and rankings
- **Weekly:** Full historical refresh
- **After config changes:** When you modify scoring weights
- **After adding new stocks:** When updating universe CSV files

## 🔧 Advanced Options

### Custom Start Date
Edit the script to change backtest start date:
```bash
# Line with --start-date
--start-date 2020-01-01  # Change this
```

### Custom Universe Size
Edit to change portfolio size:
```bash
--top 20  # Change this
```

### Skip Archiving
Comment out the archive section to just overwrite files:
```bash
# if [ -d "${OUTPUT_DIR}" ]; then
#     ARCHIVE_DIR=...
# fi
```

## 📝 Example Output

```
════════════════════════════════════════════════════════════════
  STOCK TOOL FULL REFRESH
════════════════════════════════════════════════════════════════
Timestamp: 2026-02-15_09-30-00

📁 Step 1: Cleaning output folder...
   ✓ Archived old files to: output_archive/2026-02-15_09-30-00

📊 Step 2: Running S&P 500 screening (top 20)...
   ✓ S&P 500 screening completed

🚀 Step 3: Running Mid-Cap screening (top 20)...
   ✓ Mid-Cap screening completed

📈 Step 4: Running S&P 500 backtest (top 10)...
   ✓ S&P 500 backtest (top 10) completed

...

════════════════════════════════════════════════════════════════
  ✅ REFRESH COMPLETED SUCCESSFULLY
════════════════════════════════════════════════════════════════
Total files generated: 13

📊 View dashboard at: http://localhost:8888/dashboard.html
🗂️  Old files archived to: output_archive/2026-02-15_09-30-00
════════════════════════════════════════════════════════════════
```

## ⚠️ Troubleshooting

### "Virtual environment not found"
```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

### "Permission denied"
```bash
chmod +x refresh_all.sh
```

### "Yahoo Finance timeout"
- Check internet connection
- Run again (cache will help)
- Increase timeout in `src/data_fetcher.py`

### "No space left on device"
```bash
# Clean old archives
rm -rf output_archive/2026-01-*  # Delete January archives
```

## 💡 Tips

1. **Run overnight:** Schedule for when markets are closed
2. **Check logs:** All steps are logged to console
3. **Verify manifest:** Check `output/manifest.json` after completion
4. **Force refresh:** Use `--refresh` flag in commands for cache bypass
5. **Backup important data:** Archive folder preserves history

## 🔗 Related Files

- `src/main.py` - CLI entry point
- `src/universe.py` - Universe management
- `output/dashboard.html` - Interactive visualization
- `requirements.txt` - Python dependencies
