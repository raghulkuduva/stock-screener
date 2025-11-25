#!/usr/bin/env python3
"""
Example usage of the Momentum Stock Screener.

This script demonstrates how to use the screener programmatically
and also serves as a quick test to verify everything works.
"""

from screener import (
    get_ticker_list,
    run_screener,
)


def main():
    """Run example screening."""
    
    print("=" * 70)
    print("MOMENTUM STOCK SCREENER - EXAMPLE USAGE")
    print("=" * 70)
    
    # Example 1: Check available tickers
    print("\n1. Available tickers in Nifty 50:")
    tickers = get_ticker_list("nifty_50")
    print(f"   Total: {len(tickers)} tickers")
    print(f"   First 10: {tickers[:10]}")
    
    # Example 2: Run the screener on Nifty IT (smaller index for faster demo)
    print("\n2. Running screener on Nifty IT index...")
    print("   (Using default unconventional return formula)")
    
    results = run_screener(
        index_name="nifty_it",
        top_n=10,
        history_years=2,
        use_standard_one_year_return=False,  # Use unconventional as specified
        save_csv=True,
        show_progress=True,
    )
    
    # Display results
    if len(results) > 0:
        print("\n" + "=" * 70)
        print("TOP 10 MOMENTUM STOCKS FROM NIFTY IT")
        print("=" * 70)
        
        # Format for display
        display_cols = [
            "ticker", "current_price", "return_6m", "return_12m", 
            "final_rank", "gate_pass"
        ]
        
        # Only include columns that exist
        display_cols = [c for c in display_cols if c in results.columns]
        display_df = results[display_cols].copy()
        
        # Round numeric columns
        for col in ["current_price", "return_6m", "return_12m"]:
            if col in display_df.columns:
                display_df[col] = display_df[col].round(2)
        
        print(display_df.to_string(index=False))
        
        # Show detailed view of top 3
        print("\n" + "-" * 70)
        print("DETAILED VIEW OF TOP 3 STOCKS:")
        print("-" * 70)
        
        for i, row in results.head(3).iterrows():
            print(f"\n{i+1}. {row['ticker']}")
            print(f"   Current Price: ₹{row['current_price']:.2f}")
            print(f"   EMA100: ₹{row['ema100']:.2f}")
            print(f"   EMA200: ₹{row['ema200']:.2f}")
            print(f"   52-Week High: ₹{row['52w_high']:.2f}")
            print(f"   6-Month Return: {row['return_6m']:.2f}%")
            print(f"   9-Month Return: {row['return_9m']:.2f}%")
            print(f"   12-Month Return: {row['return_12m']:.2f}%")
            print(f"   1-Year Return (Standard): {row['one_year_return_standard']:.2f}%")
            print(f"   Up Days (6M): {row['up_days_pct_6m']:.1f}%")
            print(f"   Final Rank: {row['final_rank']:.0f}")
    else:
        print("\nNo stocks passed the screening criteria.")
    
    print("\n" + "=" * 70)
    print("CSV files saved in current directory.")
    print("=" * 70)
    
    # Example 3: Using standard return formula (recommended)
    print("\n3. Running with STANDARD return formula (recommended)...")
    
    results_std = run_screener(
        index_name="nifty_it",
        top_n=5,
        use_standard_one_year_return=True,  # Recommended
        save_csv=False,  # Don't save again
        show_progress=False,
    )
    
    if len(results_std) > 0:
        print("\nTop 5 with standard formula:")
        print(results_std[["ticker", "return_12m", "final_rank"]].to_string(index=False))
    
    print("\nDone!")


if __name__ == "__main__":
    main()


