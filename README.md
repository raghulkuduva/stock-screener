# Momentum Stock Screener for Indian Stocks (NSE)

A Python-based momentum stock screener that identifies high-momentum stocks from Indian indices using technical indicators and ranking methodology.

## Features

- **Multiple Index Support**: Nifty 50, Nifty IT, Nifty Bank, Nifty Pharma, and more
- **Technical Indicators**: EMA100, EMA200, 52-week high, price consistency
- **4-Gate Screening**: Trend alignment, proximity to highs, price consistency, yearly performance
- **Momentum Ranking**: Ranks stocks by 6M and 12M returns
- **Detailed Reporting**: CSV exports with all metrics and rejection reasons
- **CLI Interface**: Easy-to-use command-line tool

## Installation

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

### Command Line

```bash
# Screen Nifty 50 for top 45 momentum stocks
python screener.py nifty_50

# Screen Nifty IT for top 10 stocks
python screener.py nifty_it --top-n 10

# Use standard (recommended) 1-year return formula
python screener.py nifty_50 --use-standard-return

# Save results to specific directory
python screener.py nifty_50 --output-dir ./results
```

### Python API

```python
from screener import run_screener, get_ticker_list

# Get list of tickers in an index
tickers = get_ticker_list("nifty_50")
print(f"Nifty 50 has {len(tickers)} stocks")

# Run the screener
results = run_screener(
    index_name="nifty_50",
    top_n=45,
    use_standard_one_year_return=True,  # Recommended
    save_csv=True,
)

# View top stocks
print(results[["ticker", "current_price", "return_12m", "final_rank"]])
```

## Available Indices

| Index | Description |
|-------|-------------|
| `nifty_50` | Nifty 50 - Top 50 companies |
| `nifty_next_50` | Nifty Next 50 |
| `nifty_100` | Nifty 100 (Nifty 50 + Next 50) |
| `nifty_it` | Nifty IT - Technology stocks |
| `nifty_bank` | Nifty Bank - Banking stocks |
| `nifty_pharma` | Nifty Pharma - Pharmaceutical stocks |
| `nifty_auto` | Nifty Auto - Automobile stocks |
| `nifty_fmcg` | Nifty FMCG - Consumer goods |
| `nifty_metal` | Nifty Metal - Metal & mining |
| `nifty_psu_bank` | Nifty PSU Bank |
| `nifty_realty` | Nifty Realty |
| `nifty_energy` | Nifty Energy |
| `nifty_infra` | Nifty Infrastructure |
| `nifty_midcap_50` | Nifty Midcap 50 |
| `nifty_midcap_100` | Nifty Midcap 100 |

## Screening Methodology

### Gatekeeping Filters (ALL must pass)

1. **Trend Alignment (Gate A)**
   - Current price ≥ EMA100
   - EMA100 ≥ EMA200

2. **Proximity to Highs (Gate B)**
   - Current price ≥ 75% of 52-week high

3. **Price Consistency (Gate C)**
   - Up days percentage > 40% in last 6 months

4. **Minimum Yearly Performance (Gate D)**
   - 1-year return ≥ 6.5%

### Ranking Methodology

- Rank by 6-month return (best = rank 1)
- Rank by 12-month return (best = rank 1)
- **Final Rank = Rank_6M + Rank_12M**
- Sort by Final Rank ascending
- Tie-breaker: higher 12M return, then higher 6M return

## Output Columns

| Column | Description |
|--------|-------------|
| `ticker` | Stock symbol |
| `current_price` | Latest adjusted close price |
| `ema100` | 100-day exponential moving average |
| `ema200` | 200-day exponential moving average |
| `52w_high` | 52-week high price |
| `within_25_pct_high` | Price within 25% of 52w high |
| `up_days_pct_6m` | Percentage of up days in 6 months |
| `one_year_return_standard` | Standard 1-year return |
| `return_6m` | 6-month return |
| `return_9m` | 9-month return |
| `return_12m` | 12-month return |
| `rank_6m` | Rank by 6-month return |
| `rank_12m` | Rank by 12-month return |
| `final_rank` | Combined ranking score |
| `gate_pass` | Whether stock passed all gates |
| `rejection_reasons` | Reasons for rejection (if any) |

## Output Files

When `save_csv=True`, two files are generated:

1. **`screener_all_{index}_{date}.csv`**: All processed tickers with metrics and rejection reasons
2. **`screener_top_{index}_{date}.csv`**: Top N selected stocks

## Running Tests

```bash
# Run all tests
pytest test_screener.py -v

# Run specific test class
pytest test_screener.py::TestComputeIndicators -v

# Run with coverage
pytest test_screener.py --cov=screener --cov-report=term-missing
```

## Notes on the 1-Year Return Formula

The screener implements two versions of the 1-year return formula:

1. **Standard (Recommended)**: `(current_price / price_1yr_ago - 1) * 100`
2. **Unconventional (Per Spec)**: `current_price / (price_1yr_ago - 1) * 100`

The unconventional formula is unusual and may produce unexpected results. Use `--use-standard-return` flag or set `use_standard_one_year_return=True` for the mathematically correct formula.

## Requirements

- Python 3.10+
- yfinance >= 0.2.40
- pandas >= 2.0.0
- numpy >= 1.24.0
- tqdm >= 4.66.0

## License

MIT License


