"""
Unit tests for the Momentum Stock Screener.

Run with: pytest test_screener.py -v
"""

import numpy as np
import pandas as pd
import pytest
from datetime import datetime, timedelta

from screener import (
    get_ticker_list,
    compute_indicators,
    apply_gatekeeper,
    rank_and_select,
    TRADING_DAYS_6M,
    TRADING_DAYS_9M,
    TRADING_DAYS_12M,
    MIN_TRADING_DAYS_REQUIRED,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def sample_price_data():
    """
    Creates a synthetic price history DataFrame for testing.
    
    Generates data for 3 tickers with known characteristics:
    - STRONG.NS: Uptrending, passes all gates
    - WEAK.NS: Downtrending, fails gates
    - PARTIAL.NS: Mixed signals
    """
    np.random.seed(42)
    
    # Generate 400 trading days
    n_days = 400
    dates = pd.date_range(end=datetime.now(), periods=n_days, freq="B")
    
    data_records = []
    
    # STRONG.NS - Uptrending stock that should pass all gates
    # Price increases from 100 to ~180 over the period
    base_price = 100
    trend = np.linspace(0, 80, n_days)
    noise = np.random.normal(0, 2, n_days)
    prices_strong = base_price + trend + noise
    
    for i, date in enumerate(dates):
        price = max(prices_strong[i], 10)  # Ensure positive
        data_records.append({
            "Date": date,
            "Ticker": "STRONG.NS",
            "Open": price * 0.99,
            "High": price * 1.02,
            "Low": price * 0.98,
            "Close": price,
            "Adj Close": price,
            "Volume": 1000000,
        })
    
    # WEAK.NS - Downtrending stock that should fail gates
    # Price decreases from 100 to ~50
    base_price = 100
    trend = np.linspace(0, -50, n_days)
    noise = np.random.normal(0, 2, n_days)
    prices_weak = base_price + trend + noise
    
    for i, date in enumerate(dates):
        price = max(prices_weak[i], 10)
        data_records.append({
            "Date": date,
            "Ticker": "WEAK.NS",
            "Open": price * 1.01,
            "High": price * 1.02,
            "Low": price * 0.98,
            "Close": price,
            "Adj Close": price,
            "Volume": 500000,
        })
    
    # PARTIAL.NS - Sideways stock with some volatility
    base_price = 100
    noise = np.random.normal(0, 5, n_days)
    prices_partial = base_price + noise
    
    for i, date in enumerate(dates):
        price = max(prices_partial[i], 10)
        data_records.append({
            "Date": date,
            "Ticker": "PARTIAL.NS",
            "Open": price,
            "High": price * 1.01,
            "Low": price * 0.99,
            "Close": price,
            "Adj Close": price,
            "Volume": 750000,
        })
    
    df = pd.DataFrame(data_records)
    df = df.set_index(["Date", "Ticker"])
    df = df.sort_index()
    
    return df


@pytest.fixture
def sample_indicators():
    """Creates a sample indicators DataFrame for testing apply_gatekeeper."""
    return pd.DataFrame([
        {
            "ticker": "PASS.NS",
            "current_price": 180,
            "ema100": 160,
            "ema200": 140,
            "52w_high": 185,
            "within_25_pct_high": True,
            "up_days_pct_6m": 55.0,
            "one_year_return_unconventional": 200.0,  # price / (price_1yr - 1) * 100
            "one_year_return_standard": 80.0,  # (price / price_1yr - 1) * 100
            "return_6m": 40.0,
            "return_9m": 55.0,
            "return_12m": 80.0,
            "price_6m_ago": 128.57,
            "price_9m_ago": 116.13,
            "price_12m_ago": 100.0,
            "trading_days": 400,
            "data_sufficient": True,
            "rejection_reasons": "",
        },
        {
            "ticker": "FAIL_TREND.NS",
            "current_price": 100,
            "ema100": 110,  # EMA100 > current_price - fails
            "ema200": 105,
            "52w_high": 120,
            "within_25_pct_high": True,
            "up_days_pct_6m": 50.0,
            "one_year_return_unconventional": 10.0,
            "one_year_return_standard": 10.0,
            "return_6m": 5.0,
            "return_9m": 7.0,
            "return_12m": 10.0,
            "price_6m_ago": 95.24,
            "price_9m_ago": 93.46,
            "price_12m_ago": 90.91,
            "trading_days": 400,
            "data_sufficient": True,
            "rejection_reasons": "",
        },
        {
            "ticker": "FAIL_PROXIMITY.NS",
            "current_price": 70,
            "ema100": 65,
            "ema200": 60,
            "52w_high": 100,  # 70 < 75 (75% of 100) - fails
            "within_25_pct_high": False,
            "up_days_pct_6m": 50.0,
            "one_year_return_unconventional": 10.0,
            "one_year_return_standard": 10.0,
            "return_6m": 5.0,
            "return_9m": 7.0,
            "return_12m": 10.0,
            "price_6m_ago": 66.67,
            "price_9m_ago": 65.42,
            "price_12m_ago": 63.64,
            "trading_days": 400,
            "data_sufficient": True,
            "rejection_reasons": "",
        },
        {
            "ticker": "FAIL_CONSISTENCY.NS",
            "current_price": 150,
            "ema100": 140,
            "ema200": 130,
            "52w_high": 155,
            "within_25_pct_high": True,
            "up_days_pct_6m": 35.0,  # < 40% - fails
            "one_year_return_unconventional": 10.0,
            "one_year_return_standard": 10.0,
            "return_6m": 5.0,
            "return_9m": 7.0,
            "return_12m": 10.0,
            "price_6m_ago": 142.86,
            "price_9m_ago": 140.19,
            "price_12m_ago": 136.36,
            "trading_days": 400,
            "data_sufficient": True,
            "rejection_reasons": "",
        },
        {
            "ticker": "FAIL_PERFORMANCE.NS",
            "current_price": 102,
            "ema100": 100,
            "ema200": 98,
            "52w_high": 105,
            "within_25_pct_high": True,
            "up_days_pct_6m": 50.0,
            "one_year_return_unconventional": 5.0,  # < 6.5% - fails
            "one_year_return_standard": 2.0,
            "return_6m": 1.0,
            "return_9m": 1.5,
            "return_12m": 2.0,
            "price_6m_ago": 100.99,
            "price_9m_ago": 100.49,
            "price_12m_ago": 100.0,
            "trading_days": 400,
            "data_sufficient": True,
            "rejection_reasons": "",
        },
        {
            "ticker": "INSUFFICIENT.NS",
            "current_price": 100,
            "trading_days": 200,  # < 300 - insufficient data
            "data_sufficient": False,
            "rejection_reasons": "Insufficient data (< 300 trading days)",
        },
    ])


@pytest.fixture
def sample_shortlist():
    """Creates a sample shortlist for testing ranking."""
    return pd.DataFrame([
        {
            "ticker": "BEST.NS",
            "current_price": 200,
            "return_6m": 50.0,
            "return_9m": 70.0,
            "return_12m": 100.0,
            "gate_pass": True,
        },
        {
            "ticker": "SECOND.NS",
            "current_price": 180,
            "return_6m": 40.0,
            "return_9m": 55.0,
            "return_12m": 80.0,
            "gate_pass": True,
        },
        {
            "ticker": "THIRD.NS",
            "current_price": 150,
            "return_6m": 30.0,
            "return_9m": 40.0,
            "return_12m": 60.0,
            "gate_pass": True,
        },
        {
            "ticker": "FOURTH.NS",
            "current_price": 120,
            "return_6m": 20.0,
            "return_9m": 25.0,
            "return_12m": 40.0,
            "gate_pass": True,
        },
    ])


# =============================================================================
# Tests for get_ticker_list
# =============================================================================

class TestGetTickerList:
    """Tests for the get_ticker_list function."""
    
    def test_nifty_50_returns_50_tickers(self):
        """Nifty 50 should return exactly 50 tickers."""
        tickers = get_ticker_list("nifty_50")
        assert len(tickers) == 50
    
    def test_tickers_have_ns_suffix(self):
        """All tickers should have .NS suffix for NSE."""
        tickers = get_ticker_list("nifty_50")
        assert all(t.endswith(".NS") for t in tickers)
    
    def test_case_insensitive(self):
        """Index name should be case insensitive."""
        tickers1 = get_ticker_list("nifty_50")
        tickers2 = get_ticker_list("NIFTY_50")
        tickers3 = get_ticker_list("Nifty_50")
        assert tickers1 == tickers2 == tickers3
    
    def test_invalid_index_raises_error(self):
        """Invalid index name should raise ValueError."""
        with pytest.raises(ValueError, match="Unknown index"):
            get_ticker_list("invalid_index")
    
    def test_all_indices_available(self):
        """Test that all documented indices are available."""
        indices = [
            "nifty_50", "nifty_next_50", "nifty_100",
            "nifty_it", "nifty_bank", "nifty_pharma",
            "nifty_auto", "nifty_fmcg", "nifty_metal",
            "nifty_psu_bank", "nifty_realty", "nifty_energy",
            "nifty_infra", "nifty_midcap_50", "nifty_midcap_100",
        ]
        for index in indices:
            tickers = get_ticker_list(index)
            assert len(tickers) > 0, f"Index {index} returned no tickers"


# =============================================================================
# Tests for compute_indicators
# =============================================================================

class TestComputeIndicators:
    """Tests for the compute_indicators function."""
    
    def test_returns_correct_columns(self, sample_price_data):
        """Should return DataFrame with all required columns."""
        result = compute_indicators(sample_price_data)
        
        required_cols = [
            "ticker", "current_price", "ema100", "ema200",
            "52w_high", "within_25_pct_high", "up_days_pct_6m",
            "one_year_return_unconventional", "one_year_return_standard",
            "return_6m", "return_9m", "return_12m",
            "trading_days", "data_sufficient",
        ]
        
        for col in required_cols:
            assert col in result.columns, f"Missing column: {col}"
    
    def test_returns_one_row_per_ticker(self, sample_price_data):
        """Should return one row per ticker."""
        result = compute_indicators(sample_price_data)
        tickers = sample_price_data.index.get_level_values("Ticker").unique()
        
        assert len(result) == len(tickers)
    
    def test_strong_stock_indicators(self, sample_price_data):
        """Strong uptrending stock should have positive returns and EMA alignment."""
        result = compute_indicators(sample_price_data)
        strong = result[result["ticker"] == "STRONG.NS"].iloc[0]
        
        # Should have positive returns
        assert strong["return_6m"] > 0
        assert strong["return_12m"] > 0
        
        # Should have EMA alignment (price > EMA100 > EMA200 for uptrend)
        assert strong["current_price"] > strong["ema200"]
        assert strong["ema100"] > strong["ema200"]
        
        # Should have sufficient data
        assert strong["data_sufficient"] == True
    
    def test_weak_stock_indicators(self, sample_price_data):
        """Weak downtrending stock should have negative returns."""
        result = compute_indicators(sample_price_data)
        weak = result[result["ticker"] == "WEAK.NS"].iloc[0]
        
        # Should have negative 12-month return (price dropped)
        assert weak["return_12m"] < 0
        
        # Should have sufficient data
        assert weak["data_sufficient"] == True
    
    def test_insufficient_data_handling(self):
        """Should handle stocks with insufficient data."""
        # Create data with only 100 days
        dates = pd.date_range(end=datetime.now(), periods=100, freq="B")
        data_records = []
        
        for date in dates:
            data_records.append({
                "Date": date,
                "Ticker": "SHORT.NS",
                "Open": 100,
                "High": 102,
                "Low": 98,
                "Close": 100,
                "Adj Close": 100,
                "Volume": 1000,
            })
        
        df = pd.DataFrame(data_records)
        df = df.set_index(["Date", "Ticker"])
        
        result = compute_indicators(df)
        
        assert result.iloc[0]["data_sufficient"] == False
        assert "Insufficient data" in result.iloc[0]["rejection_reasons"]
    
    def test_ema_calculation(self, sample_price_data):
        """EMA values should be calculated correctly."""
        result = compute_indicators(sample_price_data)
        
        for _, row in result.iterrows():
            if row["data_sufficient"]:
                # EMA100 and EMA200 should be positive
                assert row["ema100"] > 0
                assert row["ema200"] > 0
                
                # Both EMAs should be within reasonable range of current price
                assert 0.3 < row["ema100"] / row["current_price"] < 3.0
                assert 0.3 < row["ema200"] / row["current_price"] < 3.0


# =============================================================================
# Tests for apply_gatekeeper
# =============================================================================

class TestApplyGatekeeper:
    """Tests for the apply_gatekeeper function."""
    
    def test_returns_shortlist_and_rejected(self, sample_indicators):
        """Should return tuple of (shortlist_df, rejected_df)."""
        shortlist, rejected = apply_gatekeeper(sample_indicators)
        
        assert isinstance(shortlist, pd.DataFrame)
        assert isinstance(rejected, pd.DataFrame)
    
    def test_all_gates_must_pass(self, sample_indicators):
        """Only stocks passing ALL gates should be in shortlist."""
        shortlist, rejected = apply_gatekeeper(sample_indicators)
        
        # Only PASS.NS should pass all gates
        assert len(shortlist) == 1
        assert shortlist.iloc[0]["ticker"] == "PASS.NS"
    
    def test_gate_a_trend_alignment(self, sample_indicators):
        """Gate A: price >= EMA100 AND EMA100 >= EMA200."""
        shortlist, rejected = apply_gatekeeper(sample_indicators)
        
        # FAIL_TREND.NS fails because price < EMA100
        fail_trend = rejected[rejected["ticker"] == "FAIL_TREND.NS"].iloc[0]
        assert fail_trend["gate_A_trend"] == False
        assert "Trend Alignment" in fail_trend["rejection_reasons"]
    
    def test_gate_b_proximity_to_high(self, sample_indicators):
        """Gate B: price >= 0.75 * 52w_high."""
        shortlist, rejected = apply_gatekeeper(sample_indicators)
        
        # FAIL_PROXIMITY.NS fails because price < 75% of 52w high
        fail_proximity = rejected[rejected["ticker"] == "FAIL_PROXIMITY.NS"].iloc[0]
        assert fail_proximity["gate_B_proximity"] == False
        assert "Proximity to High" in fail_proximity["rejection_reasons"]
    
    def test_gate_c_consistency(self, sample_indicators):
        """Gate C: up_days_pct_6m > 40%."""
        shortlist, rejected = apply_gatekeeper(sample_indicators)
        
        # FAIL_CONSISTENCY.NS fails because up_days < 40%
        fail_consistency = rejected[rejected["ticker"] == "FAIL_CONSISTENCY.NS"].iloc[0]
        assert fail_consistency["gate_C_consistency"] == False
        assert "Consistency" in fail_consistency["rejection_reasons"]
    
    def test_gate_d_performance_unconventional(self, sample_indicators):
        """Gate D: one_year_return_unconventional >= 6.5 (default)."""
        shortlist, rejected = apply_gatekeeper(
            sample_indicators, use_standard_one_year_return=False
        )
        
        # FAIL_PERFORMANCE.NS fails because return < 6.5%
        fail_perf = rejected[rejected["ticker"] == "FAIL_PERFORMANCE.NS"].iloc[0]
        assert fail_perf["gate_D_performance"] == False
        assert "Performance" in fail_perf["rejection_reasons"]
    
    def test_gate_d_performance_standard(self, sample_indicators):
        """Gate D with standard return formula."""
        shortlist, rejected = apply_gatekeeper(
            sample_indicators, use_standard_one_year_return=True
        )
        
        # PASS.NS should still pass with standard formula (80% > 6.5%)
        passing = shortlist[shortlist["ticker"] == "PASS.NS"]
        assert len(passing) == 1
    
    def test_insufficient_data_rejected(self, sample_indicators):
        """Stocks with insufficient data should be rejected."""
        shortlist, rejected = apply_gatekeeper(sample_indicators)
        
        # INSUFFICIENT.NS should be in rejected
        insufficient = rejected[rejected["ticker"] == "INSUFFICIENT.NS"]
        assert len(insufficient) == 1
        assert insufficient.iloc[0]["data_sufficient"] == False
    
    def test_rejection_reasons_populated(self, sample_indicators):
        """All rejected stocks should have rejection reasons."""
        shortlist, rejected = apply_gatekeeper(sample_indicators)
        
        for _, row in rejected.iterrows():
            assert len(row["rejection_reasons"]) > 0
    
    def test_gate_pass_column(self, sample_indicators):
        """gate_pass column should be correctly set."""
        shortlist, rejected = apply_gatekeeper(sample_indicators)
        
        assert all(shortlist["gate_pass"] == True)
        assert all(rejected["gate_pass"] == False)


# =============================================================================
# Tests for rank_and_select
# =============================================================================

class TestRankAndSelect:
    """Tests for the rank_and_select function."""
    
    def test_returns_correct_number(self, sample_shortlist):
        """Should return at most top_n stocks."""
        result = rank_and_select(sample_shortlist, top_n=2)
        assert len(result) == 2
    
    def test_returns_all_if_less_than_top_n(self, sample_shortlist):
        """Should return all stocks if fewer than top_n."""
        result = rank_and_select(sample_shortlist, top_n=10)
        assert len(result) == len(sample_shortlist)
    
    def test_ranking_columns_added(self, sample_shortlist):
        """Should add ranking columns."""
        result = rank_and_select(sample_shortlist, top_n=4)
        
        assert "rank_6m" in result.columns
        assert "rank_9m" in result.columns
        assert "rank_12m" in result.columns
        assert "final_rank" in result.columns
    
    def test_best_stock_ranked_first(self, sample_shortlist):
        """Stock with best returns should be ranked first."""
        result = rank_and_select(sample_shortlist, top_n=4)
        
        # BEST.NS has highest returns, should be first
        assert result.iloc[0]["ticker"] == "BEST.NS"
        assert result.iloc[0]["final_rank"] == result["final_rank"].min()
    
    def test_final_rank_formula(self, sample_shortlist):
        """Final rank should be rank_6m + rank_12m (9m ignored)."""
        result = rank_and_select(sample_shortlist, top_n=4)
        
        for _, row in result.iterrows():
            expected_final_rank = row["rank_6m"] + row["rank_12m"]
            assert row["final_rank"] == expected_final_rank
    
    def test_sorted_by_final_rank(self, sample_shortlist):
        """Results should be sorted by final_rank ascending."""
        result = rank_and_select(sample_shortlist, top_n=4)
        
        ranks = result["final_rank"].tolist()
        assert ranks == sorted(ranks)
    
    def test_empty_shortlist(self):
        """Should handle empty shortlist gracefully."""
        empty_df = pd.DataFrame()
        result = rank_and_select(empty_df, top_n=10)
        
        assert len(result) == 0


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests for the full pipeline."""
    
    def test_full_pipeline(self, sample_price_data):
        """Test the full pipeline from price data to ranked results."""
        # Compute indicators
        indicators = compute_indicators(sample_price_data)
        
        assert len(indicators) == 3  # 3 tickers
        
        # Apply gatekeeper
        shortlist, rejected = apply_gatekeeper(indicators)
        
        # All should have data
        assert all(indicators["data_sufficient"] == True)
        
        # Total should match
        assert len(shortlist) + len(rejected) == len(indicators)
        
        # If any pass, rank them
        if len(shortlist) > 0:
            result = rank_and_select(shortlist, top_n=10)
            assert len(result) <= len(shortlist)
            assert "final_rank" in result.columns


# =============================================================================
# Edge Case Tests
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""
    
    def test_price_at_exactly_75_percent_of_high(self):
        """Price exactly at 75% of 52w high should pass Gate B."""
        df = pd.DataFrame([{
            "ticker": "BOUNDARY.NS",
            "current_price": 75,
            "ema100": 70,
            "ema200": 65,
            "52w_high": 100,  # 75 = 0.75 * 100 exactly
            "within_25_pct_high": True,
            "up_days_pct_6m": 50.0,
            "one_year_return_unconventional": 10.0,
            "one_year_return_standard": 10.0,
            "return_6m": 10.0,
            "return_9m": 12.0,
            "return_12m": 15.0,
            "price_6m_ago": 68.18,
            "price_9m_ago": 66.96,
            "price_12m_ago": 65.22,
            "trading_days": 400,
            "data_sufficient": True,
            "rejection_reasons": "",
        }])
        
        shortlist, rejected = apply_gatekeeper(df)
        
        assert len(shortlist) == 1
        assert shortlist.iloc[0]["gate_B_proximity"] == True
    
    def test_up_days_at_exactly_40_percent(self):
        """Up days at exactly 40% should fail Gate C (need > 40)."""
        df = pd.DataFrame([{
            "ticker": "BOUNDARY.NS",
            "current_price": 100,
            "ema100": 95,
            "ema200": 90,
            "52w_high": 105,
            "within_25_pct_high": True,
            "up_days_pct_6m": 40.0,  # Exactly 40%, needs > 40
            "one_year_return_unconventional": 10.0,
            "one_year_return_standard": 10.0,
            "return_6m": 10.0,
            "return_9m": 12.0,
            "return_12m": 15.0,
            "price_6m_ago": 90.91,
            "price_9m_ago": 89.29,
            "price_12m_ago": 86.96,
            "trading_days": 400,
            "data_sufficient": True,
            "rejection_reasons": "",
        }])
        
        shortlist, rejected = apply_gatekeeper(df)
        
        assert len(rejected) == 1
        assert rejected.iloc[0]["gate_C_consistency"] == False
    
    def test_return_at_exactly_6_5_percent(self):
        """Return at exactly 6.5% should pass Gate D."""
        df = pd.DataFrame([{
            "ticker": "BOUNDARY.NS",
            "current_price": 100,
            "ema100": 95,
            "ema200": 90,
            "52w_high": 105,
            "within_25_pct_high": True,
            "up_days_pct_6m": 50.0,
            "one_year_return_unconventional": 6.5,  # Exactly 6.5%
            "one_year_return_standard": 6.5,
            "return_6m": 3.0,
            "return_9m": 5.0,
            "return_12m": 6.5,
            "price_6m_ago": 97.09,
            "price_9m_ago": 95.24,
            "price_12m_ago": 93.90,
            "trading_days": 400,
            "data_sufficient": True,
            "rejection_reasons": "",
        }])
        
        shortlist, rejected = apply_gatekeeper(df)
        
        assert len(shortlist) == 1
        assert shortlist.iloc[0]["gate_D_performance"] == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


