"""
Momentum Stock Screener for Indian Stocks (NSE)

A comprehensive stock screener that identifies momentum stocks from Indian indices
using technical indicators and ranking methodology.

Key Features:
- Fetches historical data from yfinance
- Applies gatekeeping filters (trend, price strength, consistency, performance)
- Ranks survivors by momentum (6M, 9M, 12M returns)
- Outputs detailed CSV reports with rejection reasons

Author: Stock Screener
Version: 1.0.0
"""

import logging
import warnings
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import yfinance as yf
from tqdm import tqdm

# Suppress yfinance FutureWarnings
warnings.filterwarnings("ignore", category=FutureWarning)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# =============================================================================
# Constants
# =============================================================================

# Trading days approximations
TRADING_DAYS_PER_YEAR = 252
TRADING_DAYS_6M = 126
TRADING_DAYS_9M = 189
TRADING_DAYS_12M = 252
MIN_TRADING_DAYS_REQUIRED = 300  # Minimum days needed for analysis

# Gatekeeping thresholds
PROXIMITY_TO_HIGH_THRESHOLD = 0.75  # Within 25% of 52-week high
UP_DAYS_PCT_THRESHOLD = 40.0  # Minimum percentage of green days
ONE_YEAR_RETURN_THRESHOLD = 6.5  # Minimum 1-year return for gatekeeper


# =============================================================================
# Index Ticker Mappings
# =============================================================================

def get_ticker_list(index_name: str) -> List[str]:
    """
    Maps index name to a list of NSE ticker symbols compatible with yfinance.
    
    Parameters
    ----------
    index_name : str
        Name of the index. Supported: 'nifty_50', 'nifty_next_50', 'nifty_100',
        'nifty_it', 'nifty_bank', 'nifty_pharma', 'nifty_auto', 'nifty_fmcg',
        'nifty_metal', 'nifty_realty', 'nifty_energy', 'nifty_infra',
        'nifty_psu_bank', 'nifty_midcap_50', 'nifty_midcap_100'
    
    Returns
    -------
    List[str]
        List of ticker symbols with '.NS' suffix for NSE.
    
    Raises
    ------
    ValueError
        If index_name is not recognized.
    
    Examples
    --------
    >>> tickers = get_ticker_list('nifty_50')
    >>> print(len(tickers))
    50
    """
    # Nifty 50 constituents (as of 2024 - update periodically)
    NIFTY_50 = [
        "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
        "HINDUNILVR", "ITC", "SBIN", "BHARTIARTL", "KOTAKBANK",
        "LT", "HCLTECH", "AXISBANK", "ASIANPAINT", "MARUTI",
        "SUNPHARMA", "TITAN", "BAJFINANCE", "DMART", "ULTRACEMCO",
        "NTPC", "ONGC", "NESTLEIND", "WIPRO", "M&M",
        "POWERGRID", "JSWSTEEL", "TATAMOTORS", "ADANIENT", "ADANIPORTS",
        "TATASTEEL", "COALINDIA", "HINDALCO", "TECHM", "BAJAJFINSV",
        "GRASIM", "DIVISLAB", "BRITANNIA", "CIPLA", "DRREDDY",
        "APOLLOHOSP", "EICHERMOT", "TATACONSUM", "SBILIFE", "BPCL",
        "HEROMOTOCO", "INDUSINDBK", "BAJAJ-AUTO", "HDFCLIFE", "UPL"
    ]
    
    # Nifty IT
    NIFTY_IT = [
        "TCS", "INFY", "HCLTECH", "WIPRO", "TECHM",
        "LTIM", "MPHASIS", "COFORGE", "PERSISTENT", "LTTS"
    ]
    
    # Nifty Bank
    NIFTY_BANK = [
        "HDFCBANK", "ICICIBANK", "KOTAKBANK", "AXISBANK", "SBIN",
        "INDUSINDBK", "BANDHANBNK", "FEDERALBNK", "IDFCFIRSTB", "PNB",
        "BANKBARODA", "AUBANK"
    ]
    
    # Nifty Pharma
    NIFTY_PHARMA = [
        "SUNPHARMA", "DRREDDY", "CIPLA", "DIVISLAB", "APOLLOHOSP",
        "LUPIN", "AUROPHARMA", "BIOCON", "TORNTPHARM", "ALKEM",
        "ABBOTINDIA", "IPCALAB", "GLENMARK", "LAURUSLABS", "ZYDUSLIFE"
    ]
    
    # Nifty Auto
    NIFTY_AUTO = [
        "TATAMOTORS", "M&M", "MARUTI", "BAJAJ-AUTO", "HEROMOTOCO",
        "EICHERMOT", "BHARATFORG", "BALKRISIND", "MOTHERSON", "TVSMOTOR",
        "ASHOKLEY", "BOSCHLTD", "MRF", "EXIDEIND", "AMARAJABAT"
    ]
    
    # Nifty FMCG
    NIFTY_FMCG = [
        "HINDUNILVR", "ITC", "NESTLEIND", "BRITANNIA", "TATACONSUM",
        "DABUR", "MARICO", "GODREJCP", "COLPAL", "PGHH",
        "EMAMILTD", "VBL", "UBL", "MCDOWELL-N", "RADICO"
    ]
    
    # Nifty Metal
    NIFTY_METAL = [
        "TATASTEEL", "JSWSTEEL", "HINDALCO", "COALINDIA", "VEDL",
        "JINDALSTEL", "SAIL", "NMDC", "APLAPOLLO", "NATIONALUM",
        "MOIL", "RATNAMANI", "WELCORP", "HINDCOPPER", "JSWENERGY"
    ]
    
    # Nifty PSU Bank
    NIFTY_PSU_BANK = [
        "SBIN", "PNB", "BANKBARODA", "CANBK", "UNIONBANK",
        "INDIANB", "IOB", "CENTRALBK", "BANKINDIA", "MAHABANK",
        "UCOBANK", "PSB"
    ]
    
    # Nifty Realty
    NIFTY_REALTY = [
        "DLF", "GODREJPROP", "OBEROIRLTY", "PHOENIXLTD", "PRESTIGE",
        "BRIGADE", "SOBHA", "SUNTECK", "LODHA", "MAHLIFE"
    ]
    
    # Nifty Energy
    NIFTY_ENERGY = [
        "RELIANCE", "ONGC", "NTPC", "POWERGRID", "BPCL",
        "IOC", "GAIL", "ADANIGREEN", "TATAPOWER", "ADANIENSOL"
    ]
    
    # Nifty Infra
    NIFTY_INFRA = [
        "LT", "ADANIPORTS", "POWERGRID", "NTPC", "ULTRACEMCO",
        "GRASIM", "BHARTIARTL", "DLF", "SIEMENS", "ABB"
    ]
    
    # Nifty MidCap 50
    NIFTY_MIDCAP_50 = [
        "MUTHOOTFIN", "PAGEIND", "VOLTAS", "INDIGO", "PIIND",
        "MFSL", "IDFCFIRSTB", "FEDERALBNK", "ASTRAL", "POLYCAB",
        "TRENT", "JUBLFOOD", "LALPATHLAB", "CUMMINSIND", "PERSISTENT",
        "COFORGE", "CROMPTON", "ESCORTS", "OBEROIRLTY", "GODREJPROP",
        "MRF", "SYNGENE", "INDIANB", "AUROPHARMA", "ACC",
        "AMBUJACEM", "ATUL", "BATAINDIA", "CANBK", "CONCOR",
        "DEEPAKNTR", "DIXON", "GLAND", "GMRINFRA", "GNFC",
        "GSPL", "HAL", "HINDPETRO", "ICICIGI", "IDEA",
        "IRCTC", "IRFC", "LICHSGFIN", "LTTS", "LUPIN",
        "MANAPPURAM", "MAXHEALTH", "METROPOLIS", "NAM-INDIA", "NATIONALUM"
    ]
    
    # Nifty Next 50
    NIFTY_NEXT_50 = [
        "ADANIENSOL", "ADANIGREEN", "ADANIPOWER", "ATGL", "AWL",
        "BANKBARODA", "BEL", "BERGEPAINT", "BOSCHLTD", "CANBK",
        "CHOLAFIN", "COLPAL", "DLF", "GAIL", "GODREJCP",
        "HAL", "HAVELLS", "ICICIGI", "ICICIPRULI", "INDHOTEL",
        "INDIGO", "IOC", "IRFC", "JINDALSTEL", "JSWENERGY",
        "LICI", "LODHA", "MARICO", "MAXHEALTH", "NHPC",
        "NYKAA", "OFSS", "PAYTM", "PFC", "PIDILITIND",
        "PNB", "POLYCAB", "RECLTD", "SAIL", "SHREECEM",
        "SHRIRAMFIN", "SIEMENS", "SRF", "TATAPOWER", "TORNTPHARM",
        "TRENT", "UNIONBANK", "VBL", "VEDL", "ZOMATO"
    ]
    
    # Nifty 100 = Nifty 50 + Nifty Next 50 (removing duplicates)
    NIFTY_100 = list(set(NIFTY_50 + NIFTY_NEXT_50))
    
    # Nifty MidCap 100 (sample - extend as needed)
    NIFTY_MIDCAP_100 = list(set(NIFTY_MIDCAP_50 + [
        "AARTIIND", "ABCAPITAL", "AJANTPHARM", "ALKYLAMINE", "ANGELONE",
        "APLAPOLLO", "BALRAMCHIN", "BHARATFORG", "BHEL", "BSE",
        "CANFINHOME", "CARBORUNIV", "CDSL", "CENTRALBK", "CLEAN",
        "COCHINSHIP", "CUB", "CUMMINSIND", "CYIENT", "DALBHARAT",
        "EMAMILTD", "ENDURANCE", "FACT", "FINCABLES", "FLUOROCHEM",
        "FORTIS", "FSL", "GESHIP", "GLAXO", "GLENMARK",
        "GUJGASLTD", "HEG", "HONAUT", "IPCALAB", "IRCTC",
        "ISEC", "IEX", "JKCEMENT", "JMFINANCIL", "JSL",
        "JUBLINGREA", "KAJARIACER", "KALYANKJIL", "KEI", "KEC"
    ]))
    
    # =========================================================================
    # US MARKET INDICES
    # =========================================================================
    
    # S&P 500 Top 50 (by market cap)
    SP500_TOP50 = [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
        "META", "TSLA", "BRK-B", "UNH", "JNJ",
        "V", "XOM", "JPM", "PG", "MA",
        "HD", "CVX", "MRK", "ABBV", "LLY",
        "PEP", "COST", "KO", "AVGO", "WMT",
        "MCD", "CSCO", "TMO", "ACN", "ABT",
        "DHR", "VZ", "ADBE", "CRM", "NKE",
        "CMCSA", "NEE", "TXN", "PM", "UPS",
        "RTX", "INTC", "ORCL", "AMD", "HON",
        "IBM", "QCOM", "LOW", "SPGI", "CAT"
    ]
    
    # NASDAQ 100 Top Stocks
    NASDAQ_100 = [
        "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN",
        "NVDA", "META", "TSLA", "AVGO", "COST",
        "ASML", "PEP", "CSCO", "AZN", "ADBE",
        "NFLX", "AMD", "TMUS", "TXN", "CMCSA",
        "INTC", "QCOM", "HON", "AMGN", "INTU",
        "AMAT", "ISRG", "BKNG", "SBUX", "VRTX",
        "MDLZ", "GILD", "ADI", "ADP", "LRCX",
        "REGN", "MU", "PANW", "PYPL", "SNPS",
        "KLAC", "CDNS", "MELI", "CSX", "ORLY",
        "MAR", "MRVL", "NXPI", "MNST", "FTNT",
        "CTAS", "PCAR", "WDAY", "ADSK", "CHTR",
        "DXCM", "KDP", "AEP", "MRNA", "KHC",
        "PAYX", "CPRT", "MCHP", "ODFL", "EXC",
        "ROST", "LULU", "IDXX", "FAST", "GEHC",
        "EA", "VRSK", "CTSH", "BKR", "CSGP",
        "FANG", "XEL", "ON", "DDOG", "ANSS",
        "ZS", "CDW", "GFS", "TTWO", "ILMN",
        "WBD", "BIIB", "DLTR", "WBA", "ALGN",
        "ENPH", "SIRI", "JD", "LCID", "ZM"
    ]
    
    # Dow Jones 30
    DOW_JONES_30 = [
        "AAPL", "AMGN", "AXP", "BA", "CAT",
        "CRM", "CSCO", "CVX", "DIS", "DOW",
        "GS", "HD", "HON", "IBM", "INTC",
        "JNJ", "JPM", "KO", "MCD", "MMM",
        "MRK", "MSFT", "NKE", "PG", "TRV",
        "UNH", "V", "VZ", "WBA", "WMT"
    ]
    
    # Magnificent 7 - Top Tech Giants
    MAGNIFICENT_7 = [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA"
    ]
    
    # US Tech Leaders (Extended)
    US_TECH = [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
        "META", "TSLA", "AVGO", "ADBE", "CRM",
        "AMD", "INTC", "QCOM", "TXN", "AMAT",
        "LRCX", "MU", "SNPS", "CDNS", "KLAC",
        "NFLX", "PYPL", "NOW", "PANW", "INTU",
        "ORCL", "IBM", "CSCO", "DELL", "HPQ"
    ]
    
    # US Financials
    US_FINANCIALS = [
        "JPM", "BAC", "WFC", "GS", "MS",
        "C", "BLK", "SCHW", "AXP", "SPGI",
        "CB", "PNC", "USB", "TFC", "COF",
        "BK", "AIG", "MET", "PRU", "ALL"
    ]
    
    # US Healthcare
    US_HEALTHCARE = [
        "UNH", "JNJ", "LLY", "PFE", "ABBV",
        "MRK", "TMO", "ABT", "DHR", "BMY",
        "AMGN", "GILD", "VRTX", "REGN", "ISRG",
        "MDT", "SYK", "ZTS", "BDX", "CI"
    ]
    
    # Index mapping - Indian Markets
    INDEX_MAP = {
        "nifty_50": NIFTY_50,
        "nifty_next_50": NIFTY_NEXT_50,
        "nifty_100": NIFTY_100,
        "nifty_it": NIFTY_IT,
        "nifty_bank": NIFTY_BANK,
        "nifty_pharma": NIFTY_PHARMA,
        "nifty_auto": NIFTY_AUTO,
        "nifty_fmcg": NIFTY_FMCG,
        "nifty_metal": NIFTY_METAL,
        "nifty_psu_bank": NIFTY_PSU_BANK,
        "nifty_realty": NIFTY_REALTY,
        "nifty_energy": NIFTY_ENERGY,
        "nifty_infra": NIFTY_INFRA,
        "nifty_midcap_50": NIFTY_MIDCAP_50,
        "nifty_midcap_100": NIFTY_MIDCAP_100,
    }
    
    # Index mapping - US Markets
    US_INDEX_MAP = {
        "sp500_top50": SP500_TOP50,
        "nasdaq_100": NASDAQ_100,
        "dow_jones_30": DOW_JONES_30,
        "magnificent_7": MAGNIFICENT_7,
        "us_tech": US_TECH,
        "us_financials": US_FINANCIALS,
        "us_healthcare": US_HEALTHCARE,
    }
    
    index_lower = index_name.lower().strip()
    
    # Check Indian indices first
    if index_lower in INDEX_MAP:
        # Add .NS suffix for NSE tickers
        tickers = [f"{ticker}.NS" for ticker in INDEX_MAP[index_lower]]
        logger.info(f"Loaded {len(tickers)} tickers for Indian index '{index_name}'")
        return tickers
    
    # Check US indices
    if index_lower in US_INDEX_MAP:
        # US tickers don't need suffix
        tickers = US_INDEX_MAP[index_lower]
        logger.info(f"Loaded {len(tickers)} tickers for US index '{index_name}'")
        return tickers
    
    # Index not found
    all_indices = sorted(list(INDEX_MAP.keys()) + list(US_INDEX_MAP.keys()))
    raise ValueError(
        f"Unknown index: '{index_name}'. Available indices: {', '.join(all_indices)}"
    )
    
    return tickers


# =============================================================================
# Data Fetching
# =============================================================================

def fetch_price_history(
    tickers: List[str],
    period: str = "2y",
    interval: str = "1d",
    batch_size: int = 50,
    show_progress: bool = True,
) -> pd.DataFrame:
    """
    Fetches historical OHLCV data for multiple tickers using yfinance.
    
    Downloads data in batches to avoid overloading the API and handles
    rate limits gracefully.
    
    Parameters
    ----------
    tickers : List[str]
        List of ticker symbols (with .NS suffix for NSE).
    period : str, optional
        Data period. Default '2y' for 2 years.
    interval : str, optional
        Data interval. Default '1d' for daily.
    batch_size : int, optional
        Number of tickers to fetch per batch. Default 50.
    show_progress : bool, optional
        Whether to show progress bar. Default True.
    
    Returns
    -------
    pd.DataFrame
        MultiIndex DataFrame with columns: Open, High, Low, Close, Adj Close, Volume.
        Index is (Date, Ticker).
    
    Notes
    -----
    - Tickers with no data or errors are logged and skipped.
    - Data is cleaned to remove rows with all NaN values.
    """
    logger.info(f"Fetching price history for {len(tickers)} tickers...")
    
    all_data = []
    failed_tickers = []
    
    # Process in batches
    batches = [tickers[i:i + batch_size] for i in range(0, len(tickers), batch_size)]
    
    iterator = tqdm(batches, desc="Downloading batches", disable=not show_progress)
    
    for batch in iterator:
        try:
            # Download batch
            data = yf.download(
                tickers=batch,
                period=period,
                interval=interval,
                group_by="ticker",
                auto_adjust=False,
                threads=True,
                progress=False,
            )
            
            if data.empty:
                failed_tickers.extend(batch)
                continue
            
            # Handle single ticker case (no multi-level columns)
            if len(batch) == 1:
                ticker = batch[0]
                data.columns = pd.MultiIndex.from_product([[ticker], data.columns])
            
            # Stack to get (Date, Ticker) MultiIndex
            for ticker in batch:
                if ticker in data.columns.get_level_values(0):
                    ticker_data = data[ticker].copy()
                    ticker_data["Ticker"] = ticker
                    ticker_data = ticker_data.reset_index()
                    ticker_data = ticker_data.rename(columns={"index": "Date"})
                    
                    # Skip if all NaN
                    if ticker_data[["Open", "High", "Low", "Close"]].isna().all().all():
                        failed_tickers.append(ticker)
                        continue
                    
                    all_data.append(ticker_data)
                else:
                    failed_tickers.append(ticker)
        
        except Exception as e:
            logger.warning(f"Batch download error: {e}")
            failed_tickers.extend(batch)
    
    if failed_tickers:
        logger.warning(f"Failed to fetch data for {len(failed_tickers)} tickers: {failed_tickers[:10]}...")
    
    if not all_data:
        raise RuntimeError("No data fetched for any ticker. Check internet connection and ticker symbols.")
    
    # Combine all data
    combined = pd.concat(all_data, ignore_index=True)
    
    # Convert Date to datetime
    combined["Date"] = pd.to_datetime(combined["Date"])
    
    # Set MultiIndex
    combined = combined.set_index(["Date", "Ticker"])
    
    # Sort index
    combined = combined.sort_index()
    
    # Forward fill small gaps (1-2 days max)
    combined = combined.groupby(level="Ticker").apply(
        lambda x: x.ffill(limit=2)
    )
    
    # Reset the extra index level if created
    if isinstance(combined.index, pd.MultiIndex) and combined.index.nlevels > 2:
        combined = combined.droplevel(0)
    
    logger.info(f"Successfully fetched data for {combined.index.get_level_values('Ticker').nunique()} tickers")
    
    return combined


# =============================================================================
# Indicator Computation
# =============================================================================

def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes all technical indicators required for gatekeeping and ranking.
    
    Parameters
    ----------
    df : pd.DataFrame
        Price history DataFrame with MultiIndex (Date, Ticker).
        Must contain columns: Open, High, Low, Close, Adj Close, Volume.
    
    Returns
    -------
    pd.DataFrame
        DataFrame with one row per ticker containing:
        - ticker: Ticker symbol
        - current_price: Latest adjusted close price
        - ema100, ema200: Exponential moving averages
        - 52w_high: 52-week high price
        - within_25_pct_high: Boolean, price >= 0.75 * 52w_high
        - up_days_pct_6m: Percentage of up days in last 6 months
        - one_year_return_unconventional: User's formula (price / (price_1yr_ago - 1) * 100)
        - one_year_return_standard: Standard formula ((price / price_1yr_ago - 1) * 100)
        - return_6m, return_9m, return_12m: Period returns
        - price_6m_ago, price_9m_ago, price_12m_ago: Historical prices
        - trading_days: Number of trading days available
        - data_sufficient: Boolean, has enough data for analysis
    
    Notes
    -----
    - Uses Adj Close for all calculations
    - EMA computed using ewm(span=N, adjust=False)
    - 52-week high computed using rolling(252).max()
    
    IMPORTANT: The `one_year_return_unconventional` formula is:
        current_price / (price_1_year_ago - 1) * 100
    This is an unusual formula and likely unintended. The standard formula is:
        (current_price / price_1_year_ago - 1) * 100
    The code implements both; recommend using `use_standard_one_year_return=True`.
    """
    logger.info("Computing indicators for all tickers...")
    
    results = []
    tickers = df.index.get_level_values("Ticker").unique()
    
    for ticker in tqdm(tickers, desc="Computing indicators"):
        try:
            # Get ticker data
            ticker_df = df.xs(ticker, level="Ticker").copy()
            ticker_df = ticker_df.sort_index()
            
            # Skip if insufficient data
            trading_days = len(ticker_df)
            data_sufficient = trading_days >= MIN_TRADING_DAYS_REQUIRED
            
            # Use Adj Close for calculations
            adj_close = ticker_df["Adj Close"].dropna()
            close = ticker_df["Close"].dropna()
            
            if len(adj_close) < MIN_TRADING_DAYS_REQUIRED:
                results.append({
                    "ticker": ticker,
                    "trading_days": trading_days,
                    "data_sufficient": False,
                    "rejection_reasons": "Insufficient data (< 300 trading days)",
                })
                continue
            
            # Current price (latest)
            current_price = adj_close.iloc[-1]
            
            # EMA100 and EMA200
            ema100 = adj_close.ewm(span=100, adjust=False).mean().iloc[-1]
            ema200 = adj_close.ewm(span=200, adjust=False).mean().iloc[-1]
            
            # 52-week high (252 trading days)
            if len(adj_close) >= TRADING_DAYS_12M:
                high_52w = adj_close.rolling(window=TRADING_DAYS_12M).max().iloc[-1]
            else:
                high_52w = adj_close.max()
            
            # Within 25% of 52-week high
            within_25_pct_high = current_price >= PROXIMITY_TO_HIGH_THRESHOLD * high_52w
            
            # Up days percentage in last 6 months (126 trading days)
            if len(close) >= TRADING_DAYS_6M:
                last_6m = close.iloc[-TRADING_DAYS_6M:]
                up_days = (last_6m.diff() > 0).sum()
                up_days_pct_6m = (up_days / (TRADING_DAYS_6M - 1)) * 100  # -1 for diff
            else:
                up_days_pct_6m = np.nan
            
            # Historical prices for returns
            price_6m_ago = adj_close.iloc[-TRADING_DAYS_6M] if len(adj_close) >= TRADING_DAYS_6M else np.nan
            price_9m_ago = adj_close.iloc[-TRADING_DAYS_9M] if len(adj_close) >= TRADING_DAYS_9M else np.nan
            price_12m_ago = adj_close.iloc[-TRADING_DAYS_12M] if len(adj_close) >= TRADING_DAYS_12M else np.nan
            
            # Standard returns
            return_6m = ((current_price / price_6m_ago) - 1) * 100 if pd.notna(price_6m_ago) else np.nan
            return_9m = ((current_price / price_9m_ago) - 1) * 100 if pd.notna(price_9m_ago) else np.nan
            return_12m = ((current_price / price_12m_ago) - 1) * 100 if pd.notna(price_12m_ago) else np.nan
            
            # One-year returns (both formulas)
            # STANDARD FORMULA (recommended):
            one_year_return_standard = return_12m
            
            # UNCONVENTIONAL FORMULA (as specified by user):
            # NOTE: This formula is unusual: current_price / (price_1_year_ago - 1) * 100
            # It divides by (price - 1) instead of price, which produces unexpected results.
            # This is implemented to match the user's specification but is NOT recommended.
            # When price_12m_ago is close to 1, this can produce extremely large values.
            # When price_12m_ago < 1, this produces negative values (division by negative).
            if pd.notna(price_12m_ago) and (price_12m_ago - 1) != 0:
                one_year_return_unconventional = (current_price / (price_12m_ago - 1)) * 100
            else:
                one_year_return_unconventional = np.nan
            
            results.append({
                "ticker": ticker,
                "current_price": current_price,
                "ema100": ema100,
                "ema200": ema200,
                "52w_high": high_52w,
                "within_25_pct_high": within_25_pct_high,
                "up_days_pct_6m": up_days_pct_6m,
                "one_year_return_unconventional": one_year_return_unconventional,
                "one_year_return_standard": one_year_return_standard,
                "return_6m": return_6m,
                "return_9m": return_9m,
                "return_12m": return_12m,
                "price_6m_ago": price_6m_ago,
                "price_9m_ago": price_9m_ago,
                "price_12m_ago": price_12m_ago,
                "trading_days": trading_days,
                "data_sufficient": data_sufficient,
                "rejection_reasons": "",
            })
            
        except Exception as e:
            logger.warning(f"Error computing indicators for {ticker}: {e}")
            results.append({
                "ticker": ticker,
                "trading_days": 0,
                "data_sufficient": False,
                "rejection_reasons": f"Error: {str(e)}",
            })
    
    df_indicators = pd.DataFrame(results)
    logger.info(f"Computed indicators for {len(df_indicators)} tickers")
    
    return df_indicators


# =============================================================================
# Gatekeeping Filter
# =============================================================================

def apply_gatekeeper(
    df_indicators: pd.DataFrame,
    use_standard_one_year_return: bool = False,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Applies gatekeeping filters to identify momentum stocks.
    
    A stock passes the gatekeeper only if ALL four conditions are met:
    
    A. Trend Alignment: current_price >= EMA100 >= EMA200
    B. Proximity to Highs: current_price >= 0.75 * 52w_high
    C. Price Consistency: up_days_pct_6m > 40%
    D. Minimum Yearly Performance: one_year_return >= 6.5%
    
    Parameters
    ----------
    df_indicators : pd.DataFrame
        DataFrame from compute_indicators() with all required metrics.
    use_standard_one_year_return : bool, optional
        If True, uses the standard 1-year return formula for gate D.
        If False (default), uses the unconventional formula as specified.
        RECOMMENDATION: Set to True for mathematically correct screening.
    
    Returns
    -------
    Tuple[pd.DataFrame, pd.DataFrame]
        (shortlist_df, rejected_df) - Stocks passing/failing the gatekeeper.
        Both DataFrames include 'gate_pass' and 'rejection_reasons' columns.
    
    Notes
    -----
    The unconventional formula `current_price / (price_1yr_ago - 1) * 100`
    is unusual and likely unintended. It's recommended to use the standard
    formula by setting `use_standard_one_year_return=True`.
    """
    logger.info("Applying gatekeeper filters...")
    
    df = df_indicators.copy()
    
    # Initialize gate columns
    df["gate_A_trend"] = False
    df["gate_B_proximity"] = False
    df["gate_C_consistency"] = False
    df["gate_D_performance"] = False
    df["gate_pass"] = False
    
    # Only process rows with sufficient data
    valid_mask = df["data_sufficient"] == True
    
    if valid_mask.sum() == 0:
        logger.warning("No tickers have sufficient data for gatekeeper analysis")
        df["rejection_reasons"] = df.apply(
            lambda r: r.get("rejection_reasons", "") or "Insufficient data",
            axis=1
        )
        return df[df["gate_pass"]], df[~df["gate_pass"]]
    
    # Gate A: Trend Alignment
    # Condition: current_price >= EMA100 AND EMA100 >= EMA200
    df.loc[valid_mask, "gate_A_trend"] = (
        (df.loc[valid_mask, "current_price"] >= df.loc[valid_mask, "ema100"]) &
        (df.loc[valid_mask, "ema100"] >= df.loc[valid_mask, "ema200"])
    )
    
    # Gate B: Proximity to Highs
    # Condition: current_price >= 0.75 * 52w_high (already computed as within_25_pct_high)
    df.loc[valid_mask, "gate_B_proximity"] = df.loc[valid_mask, "within_25_pct_high"].astype(bool)
    
    # Gate C: Price Consistency
    # Condition: up_days_pct_6m > 40
    df.loc[valid_mask, "gate_C_consistency"] = (
        df.loc[valid_mask, "up_days_pct_6m"] > UP_DAYS_PCT_THRESHOLD
    )
    
    # Gate D: Minimum Yearly Performance
    # Uses either unconventional or standard formula based on parameter
    if use_standard_one_year_return:
        return_col = "one_year_return_standard"
        logger.info("Using STANDARD one-year return formula for Gate D (recommended)")
    else:
        return_col = "one_year_return_unconventional"
        logger.info(
            "Using UNCONVENTIONAL one-year return formula for Gate D "
            "(set use_standard_one_year_return=True for standard formula)"
        )
    
    df.loc[valid_mask, "gate_D_performance"] = (
        df.loc[valid_mask, return_col] >= ONE_YEAR_RETURN_THRESHOLD
    )
    
    # Overall gate pass: ALL conditions must be True
    df.loc[valid_mask, "gate_pass"] = (
        df.loc[valid_mask, "gate_A_trend"] &
        df.loc[valid_mask, "gate_B_proximity"] &
        df.loc[valid_mask, "gate_C_consistency"] &
        df.loc[valid_mask, "gate_D_performance"]
    )
    
    # Build rejection reasons
    def build_rejection_reasons(row):
        if not row.get("data_sufficient", False):
            return row.get("rejection_reasons", "") or "Insufficient data"
        
        reasons = []
        if not row["gate_A_trend"]:
            reasons.append("Failed Trend Alignment (price < EMA100 or EMA100 < EMA200)")
        if not row["gate_B_proximity"]:
            reasons.append("Failed Proximity to High (price < 75% of 52w high)")
        if not row["gate_C_consistency"]:
            reasons.append(f"Failed Consistency (up_days={row.get('up_days_pct_6m', 0):.1f}% <= 40%)")
        if not row["gate_D_performance"]:
            val = row.get(return_col, 0)
            reasons.append(f"Failed Performance ({return_col}={val:.2f}% < 6.5%)")
        
        return "; ".join(reasons) if reasons else ""
    
    df["rejection_reasons"] = df.apply(build_rejection_reasons, axis=1)
    
    # Split into shortlist and rejected
    shortlist_df = df[df["gate_pass"]].copy()
    rejected_df = df[~df["gate_pass"]].copy()
    
    # Log summary
    logger.info(f"Gatekeeper results: {len(shortlist_df)} passed, {len(rejected_df)} rejected")
    
    # Log rejection reason counts
    if len(rejected_df) > 0:
        logger.info("Rejection reasons breakdown:")
        for col, desc in [
            ("gate_A_trend", "Trend Alignment"),
            ("gate_B_proximity", "Proximity to High"),
            ("gate_C_consistency", "Price Consistency"),
            ("gate_D_performance", "Yearly Performance"),
        ]:
            failed = (~rejected_df[col]).sum()
            logger.info(f"  - Failed {desc}: {failed}")
    
    return shortlist_df, rejected_df


# =============================================================================
# Ranking and Selection
# =============================================================================

def rank_and_select(shortlist_df: pd.DataFrame, top_n: int = 45) -> pd.DataFrame:
    """
    Ranks shortlisted stocks by momentum and selects top N.
    
    Ranking methodology:
    1. Rank by 6-month return (best = rank 1)
    2. Rank by 12-month return (best = rank 1)
    3. Final_Rank = Rank_6M + Rank_12M (9M is ignored per spec)
    4. Sort by Final_Rank ascending
    5. Tie-breaker: higher return_12m, then higher return_6m
    
    Parameters
    ----------
    shortlist_df : pd.DataFrame
        DataFrame of stocks that passed the gatekeeper.
    top_n : int, optional
        Number of top stocks to return. Default 45.
    
    Returns
    -------
    pd.DataFrame
        Top N stocks with ranking columns added:
        - rank_6m, rank_9m, rank_12m: Individual period ranks
        - final_rank: Combined ranking score
    """
    if len(shortlist_df) == 0:
        logger.warning("No stocks in shortlist to rank")
        return shortlist_df
    
    logger.info(f"Ranking {len(shortlist_df)} shortlisted stocks...")
    
    df = shortlist_df.copy()
    
    # Rank by returns (higher return = better = lower rank number)
    # Using method='min' so ties get the same rank
    df["rank_6m"] = df["return_6m"].rank(method="min", ascending=False)
    df["rank_9m"] = df["return_9m"].rank(method="min", ascending=False)
    df["rank_12m"] = df["return_12m"].rank(method="min", ascending=False)
    
    # Final rank = Rank_6M + Rank_12M + (0 * Rank_9M)
    # Note: 9M is explicitly ignored as per specification
    df["final_rank"] = df["rank_6m"] + df["rank_12m"] + (0 * df["rank_9m"])
    
    # Sort by final_rank ascending
    # Tie-breaker: higher return_12m, then higher return_6m
    df = df.sort_values(
        by=["final_rank", "return_12m", "return_6m"],
        ascending=[True, False, False]
    )
    
    # Select top N
    result = df.head(top_n).copy()
    
    # Reset index for clean output
    result = result.reset_index(drop=True)
    
    logger.info(f"Selected top {len(result)} stocks")
    
    return result


# =============================================================================
# Results Saving
# =============================================================================

def save_results(
    df: pd.DataFrame,
    filename: str,
    output_dir: Optional[str] = None,
) -> Path:
    """
    Saves DataFrame to CSV file.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to save.
    filename : str
        Base filename (without path).
    output_dir : str, optional
        Output directory. Default is current directory.
    
    Returns
    -------
    Path
        Path to saved file.
    """
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
    else:
        output_path = Path(".")
    
    filepath = output_path / filename
    df.to_csv(filepath, index=False)
    logger.info(f"Saved results to {filepath}")
    
    return filepath


# =============================================================================
# Main Screener Function
# =============================================================================

def run_screener(
    index_name: str,
    top_n: int = 45,
    history_years: int = 2,
    use_standard_one_year_return: bool = False,
    save_csv: bool = True,
    output_dir: Optional[str] = None,
    show_progress: bool = True,
) -> pd.DataFrame:
    """
    Runs the momentum stock screener for an Indian stock index.
    
    This function orchestrates the entire screening process:
    1. Gets ticker list for the specified index
    2. Fetches historical price data
    3. Computes technical indicators
    4. Applies gatekeeping filters
    5. Ranks and selects top momentum stocks
    6. Saves results to CSV
    
    Parameters
    ----------
    index_name : str
        Index name (e.g., 'nifty_50', 'nifty_it', 'nifty_bank', etc.).
    top_n : int, optional
        Number of top stocks to return. Default 45.
    history_years : int, optional
        Years of history to fetch. Default 2.
    use_standard_one_year_return : bool, optional
        If True, uses standard 1-year return formula for Gate D.
        If False (default), uses the unconventional formula from spec.
        RECOMMENDATION: Set to True for mathematically correct results.
    save_csv : bool, optional
        Whether to save results to CSV. Default True.
    output_dir : str, optional
        Directory for output files. Default is current directory.
    show_progress : bool, optional
        Whether to show progress bars. Default True.
    
    Returns
    -------
    pd.DataFrame
        Top N momentum stocks with all metrics and rankings.
    
    Notes
    -----
    The unconventional one-year return formula (`price / (price_1yr - 1) * 100`)
    is unusual and may produce unexpected results. It's recommended to set
    `use_standard_one_year_return=True` for standard percentage return calculation.
    
    Saves two CSV files when save_csv=True:
    - screener_all_{index}_{date}.csv: All tickers with metrics and rejection reasons
    - screener_top_{index}_{date}.csv: Top N selected stocks
    
    Examples
    --------
    >>> results = run_screener('nifty_50', top_n=10)
    >>> print(results[['ticker', 'current_price', 'final_rank']].head())
    """
    start_time = datetime.now()
    date_str = start_time.strftime("%Y%m%d")
    
    logger.info("=" * 60)
    logger.info(f"MOMENTUM STOCK SCREENER - {index_name.upper()}")
    logger.info("=" * 60)
    logger.info(f"Parameters: top_n={top_n}, history={history_years}y, "
                f"standard_return={use_standard_one_year_return}")
    
    # Step 1: Get ticker list
    tickers = get_ticker_list(index_name)
    total_tickers = len(tickers)
    
    # Step 2: Fetch price history
    period = f"{history_years}y"
    price_data = fetch_price_history(tickers, period=period, show_progress=show_progress)
    fetched_tickers = price_data.index.get_level_values("Ticker").nunique()
    
    # Step 3: Compute indicators
    df_indicators = compute_indicators(price_data)
    
    # Step 4: Apply gatekeeper
    shortlist_df, rejected_df = apply_gatekeeper(
        df_indicators,
        use_standard_one_year_return=use_standard_one_year_return
    )
    
    # Step 5: Rank and select
    result_df = rank_and_select(shortlist_df, top_n=top_n)
    
    # Combine all results for full report
    all_results = pd.concat([shortlist_df, rejected_df], ignore_index=True)
    all_results = all_results.sort_values("ticker")
    
    # Step 6: Save results
    if save_csv:
        # Save all tickers with metrics
        all_filename = f"screener_all_{index_name}_{date_str}.csv"
        save_results(all_results, all_filename, output_dir)
        
        # Save top N
        top_filename = f"screener_top_{index_name}_{date_str}.csv"
        save_results(result_df, top_filename, output_dir)
    
    # Print summary
    elapsed = (datetime.now() - start_time).total_seconds()
    
    logger.info("=" * 60)
    logger.info("SCREENING SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total tickers in index: {total_tickers}")
    logger.info(f"Successfully fetched: {fetched_tickers}")
    logger.info(f"Passed gatekeeper: {len(shortlist_df)}")
    logger.info(f"Top {top_n} selected: {len(result_df)}")
    logger.info(f"Rejected: {len(rejected_df)}")
    logger.info(f"Time elapsed: {elapsed:.1f} seconds")
    logger.info("=" * 60)
    
    # Print rejection breakdown
    if len(rejected_df) > 0:
        logger.info("\nRejection Reasons Breakdown:")
        insufficient_data = (~rejected_df["data_sufficient"]).sum()
        logger.info(f"  - Insufficient data: {insufficient_data}")
        
        valid_rejected = rejected_df[rejected_df["data_sufficient"]]
        if len(valid_rejected) > 0:
            for gate, desc in [
                ("gate_A_trend", "Trend Alignment"),
                ("gate_B_proximity", "Proximity to High"),
                ("gate_C_consistency", "Price Consistency"),
                ("gate_D_performance", "Yearly Performance"),
            ]:
                failed = (~valid_rejected[gate]).sum()
                logger.info(f"  - Failed {desc}: {failed}")
    
    return result_df


# =============================================================================
# CLI Interface
# =============================================================================

def main():
    """Command-line interface for the momentum stock screener."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Momentum Stock Screener for Indian Stocks (NSE)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python screener.py nifty_50
  python screener.py nifty_it --top-n 10
  python screener.py nifty_bank --use-standard-return
  python screener.py nifty_50 --output-dir ./results

Available Indices:
  nifty_50, nifty_next_50, nifty_100, nifty_it, nifty_bank,
  nifty_pharma, nifty_auto, nifty_fmcg, nifty_metal, nifty_psu_bank,
  nifty_realty, nifty_energy, nifty_infra, nifty_midcap_50, nifty_midcap_100
        """
    )
    
    parser.add_argument(
        "index_name",
        type=str,
        help="Name of the stock index (e.g., nifty_50, nifty_it)"
    )
    
    parser.add_argument(
        "--top-n", "-n",
        type=int,
        default=45,
        help="Number of top stocks to select (default: 45)"
    )
    
    parser.add_argument(
        "--history-years", "-y",
        type=int,
        default=2,
        help="Years of price history to fetch (default: 2)"
    )
    
    parser.add_argument(
        "--use-standard-return", "-s",
        action="store_true",
        default=False,
        help="Use standard 1-year return formula instead of unconventional (recommended)"
    )
    
    parser.add_argument(
        "--no-save",
        action="store_true",
        default=False,
        help="Don't save results to CSV files"
    )
    
    parser.add_argument(
        "--output-dir", "-o",
        type=str,
        default=None,
        help="Directory for output files (default: current directory)"
    )
    
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        default=False,
        help="Reduce logging output"
    )
    
    args = parser.parse_args()
    
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)
    
    try:
        results = run_screener(
            index_name=args.index_name,
            top_n=args.top_n,
            history_years=args.history_years,
            use_standard_one_year_return=args.use_standard_return,
            save_csv=not args.no_save,
            output_dir=args.output_dir,
            show_progress=not args.quiet,
        )
        
        # Print top results
        if len(results) > 0:
            print("\n" + "=" * 80)
            print(f"TOP {len(results)} MOMENTUM STOCKS")
            print("=" * 80)
            
            display_cols = [
                "ticker", "current_price", "return_6m", "return_12m", "final_rank"
            ]
            display_df = results[display_cols].copy()
            display_df["current_price"] = display_df["current_price"].round(2)
            display_df["return_6m"] = display_df["return_6m"].round(2)
            display_df["return_12m"] = display_df["return_12m"].round(2)
            
            print(display_df.to_string(index=False))
        else:
            print("\nNo stocks passed the screening criteria.")
    
    except ValueError as e:
        logger.error(f"Error: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())


