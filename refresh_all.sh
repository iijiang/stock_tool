#!/bin/bash
# Full refresh script for stock screening and backtesting
# This script cleans output folder and regenerates all data

set -e  # Exit on error

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="${SCRIPT_DIR}"
OUTPUT_DIR="${PROJECT_ROOT}/output"
VENV_PYTHON="${PROJECT_ROOT}/venv/bin/python"
TIMESTAMP=$(date '+%Y-%m-%d_%H-%M-%S')

echo "════════════════════════════════════════════════════════════════"
echo "  STOCK TOOL FULL REFRESH"
echo "════════════════════════════════════════════════════════════════"
echo "Timestamp: ${TIMESTAMP}"
echo ""

# Check if virtual environment exists
if [ ! -f "${VENV_PYTHON}" ]; then
    echo "❌ Error: Virtual environment not found at ${VENV_PYTHON}"
    echo "   Please run: python3 -m venv venv && ./venv/bin/pip install -r requirements.txt"
    exit 1
fi

# Step 1: Clean/Archive output folder
echo "📁 Step 1: Cleaning output folder..."
if [ -d "${OUTPUT_DIR}" ]; then
    # Create archive folder with timestamp
    ARCHIVE_DIR="${PROJECT_ROOT}/output_archive/${TIMESTAMP}"
    mkdir -p "${ARCHIVE_DIR}"
    
    # Move old files to archive (except dashboard.html)
    if [ "$(ls -A ${OUTPUT_DIR}/*.csv 2>/dev/null)" ]; then
        mv ${OUTPUT_DIR}/*.csv "${ARCHIVE_DIR}/" 2>/dev/null || true
    fi
    if [ -d "${OUTPUT_DIR}/backtest" ] && [ "$(ls -A ${OUTPUT_DIR}/backtest 2>/dev/null)" ]; then
        mkdir -p "${ARCHIVE_DIR}/backtest"
        mv ${OUTPUT_DIR}/backtest/* "${ARCHIVE_DIR}/backtest/" 2>/dev/null || true
    fi
    
    echo "   ✓ Archived old files to: ${ARCHIVE_DIR}"
else
    mkdir -p "${OUTPUT_DIR}"
    mkdir -p "${OUTPUT_DIR}/backtest"
    echo "   ✓ Created output directories"
fi

cd "${PROJECT_ROOT}"

# Step 2: Run S&P 500 Screening
echo ""
echo "📊 Step 2: Running S&P 500 screening (top 20)..."
${VENV_PYTHON} -m src.main --mode screen --universe sp500 --top 20 --no-progress
echo "   ✓ S&P 500 screening completed"

# Step 3: Run Mid-Cap Screening
echo ""
echo "🚀 Step 3: Running Mid-Cap screening (top 20)..."
${VENV_PYTHON} -m src.main --mode screen --universe midcap --top 20 --no-progress
echo "   ✓ Mid-Cap screening completed"

# Step 4: Run S&P 500 Backtest (Top 10)
echo ""
echo "📈 Step 4: Running S&P 500 backtest (top 10)..."
${VENV_PYTHON} -m src.main --mode backtest --universe sp500 --top 10 --start-date 2022-01-01 --no-progress
echo "   ✓ S&P 500 backtest (top 10) completed"

# Step 5: Run Mid-Cap Backtest (Top 5)
echo ""
echo "📈 Step 5: Running Mid-Cap backtest (top 5)..."
${VENV_PYTHON} -m src.main --mode backtest --universe midcap --top 5 --start-date 2022-01-01 --no-progress
echo "   ✓ Mid-Cap backtest (top 5) completed"

# Step 6: Run Combined Backtest (Top 10)
echo ""
echo "📈 Step 6: Running Combined backtest (top 10)..."
${VENV_PYTHON} -m src.main --mode backtest --universe combined --top 10 --start-date 2022-01-01 --no-progress
echo "   ✓ Combined backtest (top 10) completed"

# Rename files to distinguish top 10
echo "   Renaming files to include '_top10' suffix..."
DATE_SUFFIX=$(date '+%Y-%m-%d')
for file in ${OUTPUT_DIR}/backtest/combined_backtest_*.csv ${OUTPUT_DIR}/backtest/combined_backtest_*.json ${OUTPUT_DIR}/backtest/combined_equity_*.png; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        newname=$(echo "$filename" | sed 's/combined_/combined_top10_/')
        mv "$file" "${OUTPUT_DIR}/backtest/${newname}"
        echo "      Renamed: $filename → $newname"
    fi
done

# Step 7: Run Combined Backtest (Top 20)
echo ""
echo "📈 Step 7: Running Combined backtest (top 20)..."
${VENV_PYTHON} -m src.main --mode backtest --universe combined --top 20 --start-date 2022-01-01 --no-progress
echo "   ✓ Combined backtest (top 20) completed"

# Rename files to distinguish top 20
echo "   Renaming files to include '_top20' suffix..."
for file in ${OUTPUT_DIR}/backtest/combined_backtest_*.csv ${OUTPUT_DIR}/backtest/combined_backtest_*.json ${OUTPUT_DIR}/backtest/combined_equity_*.png; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        newname=$(echo "$filename" | sed 's/combined_/combined_top20_/')
        mv "$file" "${OUTPUT_DIR}/backtest/${newname}"
        echo "      Renamed: $filename → $newname"
    fi
done

# Step 8: Generate summary report
echo ""
echo "📋 Step 8: Generating summary report..."
FILE_COUNT=$(find ${OUTPUT_DIR} -type f \( -name "*.csv" -o -name "*.json" -o -name "*.png" \) | wc -l | tr -d ' ')

# Create manifest.json for dashboard
echo "   Creating file manifest for dashboard..."
cat > ${OUTPUT_DIR}/manifest.json << EOF
{
  "generated": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "timestamp": "$(date '+%Y-%m-%d')",
  "files": {
    "sp500": {
      "ranking": "$(ls ${OUTPUT_DIR}/sp500_ranking_*.csv 2>/dev/null | head -1 | xargs basename)",
      "portfolio": "$(ls ${OUTPUT_DIR}/sp500_top*_portfolio_*.csv 2>/dev/null | head -1 | xargs basename)",
      "returns": "$(ls ${OUTPUT_DIR}/backtest/sp500_backtest_monthly_returns_*.csv 2>/dev/null | head -1 | xargs basename)",
      "summary": "$(ls ${OUTPUT_DIR}/backtest/sp500_backtest_summary_*.json 2>/dev/null | head -1 | xargs basename)",
      "equity": "$(ls ${OUTPUT_DIR}/backtest/sp500_equity_curve_*.png 2>/dev/null | head -1 | xargs basename)"
    },
    "midcap": {
      "ranking": "$(ls ${OUTPUT_DIR}/midcap_ranking_*.csv 2>/dev/null | head -1 | xargs basename)",
      "portfolio": "$(ls ${OUTPUT_DIR}/midcap_top*_portfolio_*.csv 2>/dev/null | head -1 | xargs basename)",
      "returns": "$(ls ${OUTPUT_DIR}/backtest/midcap_backtest_monthly_returns_*.csv 2>/dev/null | head -1 | xargs basename)",
      "summary": "$(ls ${OUTPUT_DIR}/backtest/midcap_backtest_summary_*.json 2>/dev/null | head -1 | xargs basename)",
      "equity": "$(ls ${OUTPUT_DIR}/backtest/midcap_equity_curve_*.png 2>/dev/null | head -1 | xargs basename)"
    },
    "combined_top10": {
      "returns": "$(ls ${OUTPUT_DIR}/backtest/combined_top10_backtest_monthly_returns_*.csv 2>/dev/null | head -1 | xargs basename)",
      "summary": "$(ls ${OUTPUT_DIR}/backtest/combined_top10_backtest_summary_*.json 2>/dev/null | head -1 | xargs basename)",
      "equity": "$(ls ${OUTPUT_DIR}/backtest/combined_top10_equity_curve_*.png 2>/dev/null | head -1 | xargs basename)"
    },
    "combined_top20": {
      "returns": "$(ls ${OUTPUT_DIR}/backtest/combined_top20_backtest_monthly_returns_*.csv 2>/dev/null | head -1 | xargs basename)",
      "summary": "$(ls ${OUTPUT_DIR}/backtest/combined_top20_backtest_summary_*.json 2>/dev/null | head -1 | xargs basename)",
      "equity": "$(ls ${OUTPUT_DIR}/backtest/combined_top20_equity_curve_*.png 2>/dev/null | head -1 | xargs basename)"
    }
  }
}
EOF
echo "   ✓ Manifest created"

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  ✅ REFRESH COMPLETED SUCCESSFULLY"
echo "════════════════════════════════════════════════════════════════"
echo "Total files generated: ${FILE_COUNT}"
echo ""
echo "📁 Output files:"
find ${OUTPUT_DIR} -type f \( -name "*.csv" -o -name "*.json" -o -name "*.png" \) -not -name "dashboard.html" | sort
echo ""
echo "📊 View dashboard at: http://localhost:8888/dashboard.html"
echo "   (Start server: cd output && python3 -m http.server 8888)"
echo ""
echo "🗂️  Old files archived to: ${ARCHIVE_DIR}"
echo "════════════════════════════════════════════════════════════════"
