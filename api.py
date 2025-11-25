"""
FastAPI Backend for Momentum Stock Screener

Provides REST API endpoints for the stock screening functionality.
Run with: uvicorn api:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor

from screener import (
    get_ticker_list,
    fetch_price_history,
    compute_indicators,
    apply_gatekeeper,
    rank_and_select,
)

# =============================================================================
# FastAPI App
# =============================================================================

app = FastAPI(
    title="Momentum Stock Screener API",
    description="API for screening Indian momentum stocks using technical analysis",
    version="1.0.0",
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Thread pool for running blocking operations
executor = ThreadPoolExecutor(max_workers=4)

# =============================================================================
# Models
# =============================================================================

class ScreenerRequest(BaseModel):
    index_name: str = Field(..., description="Index name (e.g., nifty_50, nifty_it)")
    top_n: int = Field(default=20, ge=1, le=100, description="Number of top stocks to return")
    use_standard_return: bool = Field(default=True, description="Use standard return formula")


class StockResult(BaseModel):
    ticker: str
    current_price: Optional[float]
    ema100: Optional[float]
    ema200: Optional[float]
    high_52w: Optional[float]
    within_25_pct_high: Optional[bool]
    up_days_pct_6m: Optional[float]
    one_year_return_standard: Optional[float]
    one_year_return_unconventional: Optional[float]
    return_6m: Optional[float]
    return_9m: Optional[float]
    return_12m: Optional[float]
    rank_6m: Optional[float]
    rank_12m: Optional[float]
    final_rank: Optional[float]
    gate_pass: Optional[bool]
    gate_A_trend: Optional[bool]
    gate_B_proximity: Optional[bool]
    gate_C_consistency: Optional[bool]
    gate_D_performance: Optional[bool]
    rejection_reasons: Optional[str]
    data_sufficient: Optional[bool]


class ScreenerResponse(BaseModel):
    success: bool
    index_name: str
    timestamp: str
    summary: Dict[str, Any]
    top_stocks: List[Dict[str, Any]]
    all_results: List[Dict[str, Any]]
    rejected: List[Dict[str, Any]]


class IndexInfo(BaseModel):
    key: str
    name: str
    description: str
    stock_count: int


# =============================================================================
# Available Indices
# =============================================================================

INDICES = {
    "nifty_50": {"name": "Nifty 50", "description": "Top 50 companies by market cap"},
    "nifty_next_50": {"name": "Nifty Next 50", "description": "Next 50 companies after Nifty 50"},
    "nifty_100": {"name": "Nifty 100", "description": "Top 100 companies"},
    "nifty_it": {"name": "Nifty IT", "description": "Information Technology sector"},
    "nifty_bank": {"name": "Nifty Bank", "description": "Banking sector"},
    "nifty_pharma": {"name": "Nifty Pharma", "description": "Pharmaceutical sector"},
    "nifty_auto": {"name": "Nifty Auto", "description": "Automobile sector"},
    "nifty_fmcg": {"name": "Nifty FMCG", "description": "Fast Moving Consumer Goods"},
    "nifty_metal": {"name": "Nifty Metal", "description": "Metal & Mining sector"},
    "nifty_psu_bank": {"name": "Nifty PSU Bank", "description": "Public Sector Banks"},
    "nifty_realty": {"name": "Nifty Realty", "description": "Real Estate sector"},
    "nifty_energy": {"name": "Nifty Energy", "description": "Energy sector"},
    "nifty_infra": {"name": "Nifty Infra", "description": "Infrastructure sector"},
    "nifty_midcap_50": {"name": "Nifty Midcap 50", "description": "Top 50 midcap companies"},
    "nifty_midcap_100": {"name": "Nifty Midcap 100", "description": "Top 100 midcap companies"},
}


# =============================================================================
# Helper Functions
# =============================================================================

def run_screening_sync(index_name: str, top_n: int, use_standard_return: bool) -> dict:
    """Run the screening process synchronously."""
    # Get tickers
    tickers = get_ticker_list(index_name)
    
    # Fetch data
    price_data = fetch_price_history(tickers, period="2y", show_progress=False)
    
    # Compute indicators
    df_indicators = compute_indicators(price_data)
    
    # Apply gatekeeper
    shortlist, rejected = apply_gatekeeper(df_indicators, use_standard_return)
    
    # Rank and select
    if len(shortlist) > 0:
        ranked = rank_and_select(shortlist, top_n=top_n)
    else:
        ranked = shortlist
    
    # Combine all results
    all_results = df_indicators.copy()
    
    return {
        "top_stocks": ranked,
        "all_results": all_results,
        "rejected": rejected,
        "total_tickers": len(tickers),
    }


def clean_dataframe_for_json(df) -> List[Dict[str, Any]]:
    """Convert DataFrame to JSON-serializable list of dicts."""
    if df is None or len(df) == 0:
        return []
    
    # Replace NaN with None
    df = df.replace({float('nan'): None, float('inf'): None, float('-inf'): None})
    
    # Convert to records
    records = df.to_dict(orient='records')
    
    # Clean up each record
    cleaned = []
    for record in records:
        clean_record = {}
        for key, value in record.items():
            # Handle numpy types
            if hasattr(value, 'item'):
                value = value.item()
            # Handle NaN
            if isinstance(value, float) and (value != value):  # NaN check
                value = None
            clean_record[key] = value
        cleaned.append(clean_record)
    
    return cleaned


# =============================================================================
# API Endpoints
# =============================================================================

@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "Momentum Stock Screener API",
        "version": "1.0.0",
        "endpoints": {
            "GET /indices": "List available indices",
            "POST /screen": "Run stock screener",
            "GET /health": "Health check",
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/indices", response_model=List[IndexInfo])
async def list_indices():
    """List all available indices with their stock counts."""
    result = []
    for key, info in INDICES.items():
        try:
            tickers = get_ticker_list(key)
            count = len(tickers)
        except:
            count = 0
        
        result.append(IndexInfo(
            key=key,
            name=info["name"],
            description=info["description"],
            stock_count=count,
        ))
    
    return result


@app.post("/screen", response_model=ScreenerResponse)
async def run_screener(request: ScreenerRequest):
    """
    Run the momentum stock screener.
    
    This endpoint fetches price data, computes indicators, applies filters,
    and returns ranked momentum stocks.
    """
    # Validate index
    if request.index_name not in INDICES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid index: {request.index_name}. Available: {list(INDICES.keys())}"
        )
    
    try:
        # Run screening in thread pool to not block
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            executor,
            run_screening_sync,
            request.index_name,
            request.top_n,
            request.use_standard_return,
        )
        
        # Prepare response
        top_stocks = clean_dataframe_for_json(result["top_stocks"])
        all_results = clean_dataframe_for_json(result["all_results"])
        rejected = clean_dataframe_for_json(result["rejected"])
        
        # Summary stats
        summary = {
            "total_analyzed": len(all_results),
            "passed_filters": len(top_stocks),
            "rejected": len(rejected),
            "pass_rate": round(len(top_stocks) / len(all_results) * 100, 1) if all_results else 0,
        }
        
        return ScreenerResponse(
            success=True,
            index_name=request.index_name,
            timestamp=datetime.now().isoformat(),
            summary=summary,
            top_stocks=top_stocks,
            all_results=all_results,
            rejected=rejected,
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tickers/{index_name}")
async def get_tickers(index_name: str):
    """Get list of tickers for an index."""
    if index_name not in INDICES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid index: {index_name}"
        )
    
    try:
        tickers = get_ticker_list(index_name)
        return {
            "index": index_name,
            "count": len(tickers),
            "tickers": tickers,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Run with: uvicorn api:app --reload --port 8000
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

