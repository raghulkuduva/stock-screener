"""
Momentum Stock Screener - Web Application

A beautiful, modern web interface for screening Indian momentum stocks.
Built with Streamlit.

Run with: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import time

# Import screener functions
from screener import (
    get_ticker_list,
    fetch_price_history,
    compute_indicators,
    apply_gatekeeper,
    rank_and_select,
)

# =============================================================================
# Page Configuration
# =============================================================================

st.set_page_config(
    page_title="Momentum Screener",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
# Custom CSS - Distinctive Dark Theme with Amber Accents
# =============================================================================

st.markdown("""
<style>
    /* Import distinctive font */
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Outfit:wght@300;400;500;600;700&display=swap');
    
    /* Root variables */
    :root {
        --bg-primary: #0a0a0f;
        --bg-secondary: #12121a;
        --bg-card: #1a1a24;
        --bg-hover: #22222e;
        --accent-primary: #f59e0b;
        --accent-secondary: #fbbf24;
        --accent-glow: rgba(245, 158, 11, 0.15);
        --text-primary: #fafafa;
        --text-secondary: #a1a1aa;
        --text-muted: #71717a;
        --success: #22c55e;
        --danger: #ef4444;
        --border: #27272a;
    }
    
    /* Main container */
    .stApp {
        background: linear-gradient(135deg, var(--bg-primary) 0%, #0f0f18 50%, var(--bg-primary) 100%);
        font-family: 'Outfit', sans-serif;
    }
    
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: var(--bg-secondary);
        border-right: 1px solid var(--border);
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: var(--text-primary);
    }
    
    /* Headers */
    h1, h2, h3 {
        font-family: 'Outfit', sans-serif !important;
        font-weight: 600 !important;
        color: var(--text-primary) !important;
    }
    
    h1 {
        background: linear-gradient(135deg, var(--accent-primary) 0%, var(--accent-secondary) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    /* Cards */
    .metric-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        border-color: var(--accent-primary);
        box-shadow: 0 0 20px var(--accent-glow);
    }
    
    .metric-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 2rem;
        font-weight: 700;
        color: var(--accent-primary);
        margin: 0;
    }
    
    .metric-label {
        font-size: 0.875rem;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 0.5rem;
    }
    
    /* Stock cards */
    .stock-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        transition: all 0.3s ease;
    }
    
    .stock-card:hover {
        transform: translateY(-2px);
        border-color: var(--accent-primary);
        box-shadow: 0 8px 30px var(--accent-glow);
    }
    
    .stock-ticker {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.25rem;
        font-weight: 600;
        color: var(--text-primary);
    }
    
    .stock-rank {
        display: inline-block;
        background: linear-gradient(135deg, var(--accent-primary) 0%, var(--accent-secondary) 100%);
        color: var(--bg-primary);
        font-family: 'JetBrains Mono', monospace;
        font-weight: 700;
        font-size: 0.875rem;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
    }
    
    .return-positive {
        color: var(--success);
        font-family: 'JetBrains Mono', monospace;
        font-weight: 500;
    }
    
    .return-negative {
        color: var(--danger);
        font-family: 'JetBrains Mono', monospace;
        font-weight: 500;
    }
    
    /* Tables */
    .dataframe {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.875rem !important;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, var(--accent-primary) 0%, var(--accent-secondary) 100%);
        color: var(--bg-primary);
        border: none;
        border-radius: 8px;
        font-family: 'Outfit', sans-serif;
        font-weight: 600;
        padding: 0.75rem 2rem;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 20px var(--accent-glow);
    }
    
    /* Select boxes */
    .stSelectbox > div > div {
        background: var(--bg-card);
        border-color: var(--border);
        color: var(--text-primary);
    }
    
    /* Sliders */
    .stSlider > div > div > div {
        background: var(--accent-primary);
    }
    
    /* Progress bar */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, var(--accent-primary) 0%, var(--accent-secondary) 100%);
    }
    
    /* Info boxes */
    .info-box {
        background: rgba(245, 158, 11, 0.1);
        border: 1px solid var(--accent-primary);
        border-radius: 8px;
        padding: 1rem;
        color: var(--text-primary);
    }
    
    /* Gate badges */
    .gate-pass {
        display: inline-block;
        background: rgba(34, 197, 94, 0.15);
        color: var(--success);
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 500;
    }
    
    .gate-fail {
        display: inline-block;
        background: rgba(239, 68, 68, 0.15);
        color: var(--danger);
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 500;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: var(--bg-secondary);
        border-radius: 12px;
        padding: 4px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 8px;
        color: var(--text-secondary);
        font-family: 'Outfit', sans-serif;
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--bg-card);
        color: var(--accent-primary);
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: var(--bg-card);
        border-radius: 8px;
    }
    
    /* Code blocks */
    code {
        font-family: 'JetBrains Mono', monospace !important;
        background: var(--bg-card) !important;
        color: var(--accent-primary) !important;
    }
    
    /* Divider */
    hr {
        border-color: var(--border);
    }
    
    /* Animation keyframes */
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    .loading {
        animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# Available Indices
# =============================================================================

INDICES = {
    "nifty_50": "Nifty 50 - Top 50 Companies",
    "nifty_next_50": "Nifty Next 50",
    "nifty_100": "Nifty 100",
    "nifty_it": "Nifty IT - Technology",
    "nifty_bank": "Nifty Bank - Banking",
    "nifty_pharma": "Nifty Pharma - Pharmaceutical",
    "nifty_auto": "Nifty Auto - Automobile",
    "nifty_fmcg": "Nifty FMCG - Consumer Goods",
    "nifty_metal": "Nifty Metal - Mining",
    "nifty_psu_bank": "Nifty PSU Bank",
    "nifty_realty": "Nifty Realty",
    "nifty_energy": "Nifty Energy",
    "nifty_infra": "Nifty Infrastructure",
    "nifty_midcap_50": "Nifty Midcap 50",
    "nifty_midcap_100": "Nifty Midcap 100",
}


# =============================================================================
# Helper Functions
# =============================================================================

def format_currency(value):
    """Format value as Indian Rupees."""
    if pd.isna(value):
        return "—"
    return f"₹{value:,.2f}"


def format_percent(value, include_sign=True):
    """Format value as percentage with color coding."""
    if pd.isna(value):
        return "—"
    sign = "+" if value > 0 and include_sign else ""
    return f"{sign}{value:.2f}%"


def get_return_class(value):
    """Get CSS class for return value."""
    if pd.isna(value):
        return ""
    return "return-positive" if value >= 0 else "return-negative"


@st.cache_data(ttl=3600, show_spinner=False)
def run_screening(index_name: str, use_standard_return: bool):
    """Run the screening process with caching."""
    # Get tickers
    tickers = get_ticker_list(index_name)
    
    # Fetch data
    price_data = fetch_price_history(tickers, period="2y", show_progress=False)
    
    # Compute indicators
    df_indicators = compute_indicators(price_data)
    
    # Apply gatekeeper
    shortlist, rejected = apply_gatekeeper(df_indicators, use_standard_return)
    
    # Combine for full results
    all_results = pd.concat([shortlist, rejected], ignore_index=True)
    
    return all_results, shortlist, rejected


# =============================================================================
# Sidebar
# =============================================================================

with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0;">
        <h1 style="font-size: 1.5rem; margin: 0;">📈 Momentum</h1>
        <p style="color: #a1a1aa; margin: 0.5rem 0 0 0; font-size: 0.875rem;">Stock Screener</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # Index Selection
    st.markdown("### 🎯 Select Index")
    selected_index = st.selectbox(
        "Choose an index",
        options=list(INDICES.keys()),
        format_func=lambda x: INDICES[x],
        label_visibility="collapsed",
    )
    
    # Get ticker count
    try:
        ticker_count = len(get_ticker_list(selected_index))
    except:
        ticker_count = 0
    
    st.caption(f"Contains **{ticker_count}** stocks")
    
    st.divider()
    
    # Parameters
    st.markdown("### ⚙️ Parameters")
    
    top_n = st.slider(
        "Top N Stocks",
        min_value=5,
        max_value=50,
        value=20,
        step=5,
        help="Number of top momentum stocks to display"
    )
    
    use_standard = st.toggle(
        "Use Standard Return Formula",
        value=True,
        help="Recommended: Use standard percentage return calculation"
    )
    
    st.divider()
    
    # Run Button
    run_button = st.button("🚀 Run Screener", use_container_width=True, type="primary")
    
    st.divider()
    
    # Info
    with st.expander("ℹ️ About the Screener"):
        st.markdown("""
        **Gatekeeping Criteria:**
        
        1. **Trend Alignment**
           - Price ≥ EMA100 ≥ EMA200
        
        2. **Price Strength**
           - Within 25% of 52-week high
        
        3. **Consistency**
           - >40% up days in 6 months
        
        4. **Performance**
           - 1-year return ≥ 6.5%
        
        **Ranking:**
        - Final Rank = Rank(6M) + Rank(12M)
        - Lower rank = Better momentum
        """)


# =============================================================================
# Main Content
# =============================================================================

# Header
st.markdown("""
<div style="text-align: center; padding: 2rem 0;">
    <h1 style="font-size: 3rem; margin: 0;">Momentum Stock Screener</h1>
    <p style="color: #a1a1aa; font-size: 1.125rem; margin: 1rem 0 0 0;">
        Identify high-momentum Indian stocks using technical analysis
    </p>
</div>
""", unsafe_allow_html=True)

# Initialize session state
if "results" not in st.session_state:
    st.session_state.results = None
    st.session_state.shortlist = None
    st.session_state.rejected = None
    st.session_state.last_index = None

# Run screening
if run_button:
    with st.status("🔍 Running momentum screener...", expanded=True) as status:
        try:
            st.write("📊 Fetching price data...")
            progress = st.progress(0)
            
            # Simulate progress for UX
            for i in range(20):
                time.sleep(0.02)
                progress.progress(i * 5)
            
            st.write("📈 Computing technical indicators...")
            
            all_results, shortlist, rejected = run_screening(
                selected_index, use_standard
            )
            
            progress.progress(80)
            st.write("🎯 Applying momentum filters...")
            
            # Rank if we have shortlist
            if len(shortlist) > 0:
                ranked = rank_and_select(shortlist, top_n=top_n)
            else:
                ranked = shortlist
            
            progress.progress(100)
            
            # Store results
            st.session_state.results = all_results
            st.session_state.shortlist = ranked
            st.session_state.rejected = rejected
            st.session_state.last_index = selected_index
            
            status.update(label="✅ Screening complete!", state="complete")
            
        except Exception as e:
            status.update(label=f"❌ Error: {str(e)}", state="error")
            st.error(f"An error occurred: {str(e)}")

# Display results
if st.session_state.results is not None:
    results = st.session_state.results
    shortlist = st.session_state.shortlist
    rejected = st.session_state.rejected
    
    st.divider()
    
    # Summary Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <p class="metric-value">{len(results)}</p>
            <p class="metric-label">Total Analyzed</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <p class="metric-value" style="color: #22c55e;">{len(shortlist)}</p>
            <p class="metric-label">Passed Filters</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <p class="metric-value" style="color: #ef4444;">{len(rejected)}</p>
            <p class="metric-label">Rejected</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        pass_rate = (len(shortlist) / len(results) * 100) if len(results) > 0 else 0
        st.markdown(f"""
        <div class="metric-card">
            <p class="metric-value">{pass_rate:.1f}%</p>
            <p class="metric-label">Pass Rate</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["🏆 Top Momentum", "📊 All Results", "❌ Rejected"])
    
    # Tab 1: Top Momentum Stocks
    with tab1:
        if len(shortlist) > 0:
            st.markdown(f"### Top {len(shortlist)} Momentum Stocks")
            
            for idx, row in shortlist.iterrows():
                ticker = row.get("ticker", "N/A").replace(".NS", "")
                price = row.get("current_price", 0)
                rank = row.get("final_rank", 0)
                return_6m = row.get("return_6m", 0)
                return_12m = row.get("return_12m", 0)
                ema100 = row.get("ema100", 0)
                ema200 = row.get("ema200", 0)
                high_52w = row.get("52w_high", 0)
                up_days = row.get("up_days_pct_6m", 0)
                
                with st.container():
                    col1, col2, col3, col4 = st.columns([2, 1.5, 1.5, 1.5])
                    
                    with col1:
                        st.markdown(f"""
                        <div style="display: flex; align-items: center; gap: 1rem;">
                            <span class="stock-rank">#{int(rank)}</span>
                            <div>
                                <p class="stock-ticker" style="margin: 0;">{ticker}</p>
                                <p style="color: #71717a; margin: 0; font-size: 0.875rem;">
                                    {format_currency(price)}
                                </p>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        r6_class = get_return_class(return_6m)
                        st.markdown(f"""
                        <div style="text-align: center;">
                            <p class="{r6_class}" style="margin: 0; font-size: 1.25rem;">
                                {format_percent(return_6m)}
                            </p>
                            <p style="color: #71717a; margin: 0; font-size: 0.75rem;">6M Return</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col3:
                        r12_class = get_return_class(return_12m)
                        st.markdown(f"""
                        <div style="text-align: center;">
                            <p class="{r12_class}" style="margin: 0; font-size: 1.25rem;">
                                {format_percent(return_12m)}
                            </p>
                            <p style="color: #71717a; margin: 0; font-size: 0.75rem;">12M Return</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col4:
                        pct_from_high = ((price / high_52w) - 1) * 100 if high_52w > 0 else 0
                        st.markdown(f"""
                        <div style="text-align: center;">
                            <p style="margin: 0; font-size: 1.25rem; color: #a1a1aa;">
                                {pct_from_high:.1f}%
                            </p>
                            <p style="color: #71717a; margin: 0; font-size: 0.75rem;">From 52W High</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Expandable details
                    with st.expander("View Details"):
                        dcol1, dcol2, dcol3, dcol4 = st.columns(4)
                        dcol1.metric("EMA 100", format_currency(ema100))
                        dcol2.metric("EMA 200", format_currency(ema200))
                        dcol3.metric("52W High", format_currency(high_52w))
                        dcol4.metric("Up Days %", f"{up_days:.1f}%")
                    
                    st.divider()
            
            # Download button
            csv = shortlist.to_csv(index=False)
            st.download_button(
                label="📥 Download Top Stocks CSV",
                data=csv,
                file_name=f"momentum_top_{st.session_state.last_index}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
            )
        else:
            st.warning("No stocks passed all screening criteria.")
            st.info("Try a different index or adjust the parameters.")
    
    # Tab 2: All Results
    with tab2:
        st.markdown("### All Analyzed Stocks")
        
        # Prepare display dataframe
        display_cols = [
            "ticker", "current_price", "return_6m", "return_12m",
            "gate_pass", "gate_A_trend", "gate_B_proximity", 
            "gate_C_consistency", "gate_D_performance"
        ]
        available_cols = [c for c in display_cols if c in results.columns]
        display_df = results[available_cols].copy()
        
        # Format columns
        display_df["ticker"] = display_df["ticker"].str.replace(".NS", "")
        
        if "current_price" in display_df.columns:
            display_df["current_price"] = display_df["current_price"].apply(
                lambda x: f"₹{x:,.2f}" if pd.notna(x) else "—"
            )
        
        for col in ["return_6m", "return_12m"]:
            if col in display_df.columns:
                display_df[col] = display_df[col].apply(
                    lambda x: f"{x:+.2f}%" if pd.notna(x) else "—"
                )
        
        # Rename columns for display
        display_df = display_df.rename(columns={
            "ticker": "Ticker",
            "current_price": "Price",
            "return_6m": "6M Return",
            "return_12m": "12M Return",
            "gate_pass": "Passed",
            "gate_A_trend": "Trend",
            "gate_B_proximity": "Strength",
            "gate_C_consistency": "Consistency",
            "gate_D_performance": "Performance",
        })
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
        )
        
        # Download all
        csv_all = results.to_csv(index=False)
        st.download_button(
            label="📥 Download All Results CSV",
            data=csv_all,
            file_name=f"momentum_all_{st.session_state.last_index}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )
    
    # Tab 3: Rejected Stocks
    with tab3:
        st.markdown("### Rejected Stocks")
        
        if len(rejected) > 0:
            # Rejection reason breakdown
            st.markdown("#### Rejection Breakdown")
            
            col1, col2, col3, col4 = st.columns(4)
            
            valid_rejected = rejected[rejected.get("data_sufficient", True) == True]
            
            with col1:
                count = (~rejected.get("data_sufficient", pd.Series([True]*len(rejected)))).sum()
                st.metric("Insufficient Data", count)
            
            with col2:
                if "gate_A_trend" in valid_rejected.columns:
                    count = (~valid_rejected["gate_A_trend"]).sum()
                else:
                    count = 0
                st.metric("Failed Trend", count)
            
            with col3:
                if "gate_B_proximity" in valid_rejected.columns:
                    count = (~valid_rejected["gate_B_proximity"]).sum()
                else:
                    count = 0
                st.metric("Failed Strength", count)
            
            with col4:
                if "gate_D_performance" in valid_rejected.columns:
                    count = (~valid_rejected["gate_D_performance"]).sum()
                else:
                    count = 0
                st.metric("Failed Performance", count)
            
            st.divider()
            
            # Rejected table
            rejected_display = rejected[["ticker", "rejection_reasons"]].copy()
            rejected_display["ticker"] = rejected_display["ticker"].str.replace(".NS", "")
            rejected_display = rejected_display.rename(columns={
                "ticker": "Ticker",
                "rejection_reasons": "Rejection Reasons"
            })
            
            st.dataframe(
                rejected_display,
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.success("All stocks passed the screening criteria!")

else:
    # Initial state - show instructions
    st.markdown("""
    <div style="text-align: center; padding: 4rem 2rem; max-width: 600px; margin: 0 auto;">
        <div style="font-size: 4rem; margin-bottom: 1rem;">🎯</div>
        <h2 style="color: #fafafa; margin-bottom: 1rem;">Ready to Screen</h2>
        <p style="color: #a1a1aa; font-size: 1.125rem; line-height: 1.75;">
            Select an index from the sidebar and click <strong>Run Screener</strong> 
            to identify high-momentum stocks using our 4-gate filtering system.
        </p>
        
        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem; margin-top: 2rem; text-align: left;">
            <div class="metric-card">
                <p style="color: #f59e0b; margin: 0; font-size: 1.25rem;">📈</p>
                <p style="color: #fafafa; margin: 0.5rem 0 0.25rem 0; font-weight: 500;">Trend Analysis</p>
                <p style="color: #71717a; margin: 0; font-size: 0.875rem;">EMA crossover detection</p>
            </div>
            <div class="metric-card">
                <p style="color: #f59e0b; margin: 0; font-size: 1.25rem;">💪</p>
                <p style="color: #fafafa; margin: 0.5rem 0 0.25rem 0; font-weight: 500;">Price Strength</p>
                <p style="color: #71717a; margin: 0; font-size: 0.875rem;">Near 52-week highs</p>
            </div>
            <div class="metric-card">
                <p style="color: #f59e0b; margin: 0; font-size: 1.25rem;">📊</p>
                <p style="color: #fafafa; margin: 0.5rem 0 0.25rem 0; font-weight: 500;">Consistency</p>
                <p style="color: #71717a; margin: 0; font-size: 0.875rem;">Green day frequency</p>
            </div>
            <div class="metric-card">
                <p style="color: #f59e0b; margin: 0; font-size: 1.25rem;">🚀</p>
                <p style="color: #fafafa; margin: 0.5rem 0 0.25rem 0; font-weight: 500;">Performance</p>
                <p style="color: #71717a; margin: 0; font-size: 0.875rem;">Yearly return filter</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("""
<div style="text-align: center; padding: 2rem 0; margin-top: 2rem; border-top: 1px solid #27272a;">
    <p style="color: #71717a; font-size: 0.875rem; margin: 0;">
        Built with Streamlit • Data from Yahoo Finance • Not financial advice
    </p>
</div>
""", unsafe_allow_html=True)

