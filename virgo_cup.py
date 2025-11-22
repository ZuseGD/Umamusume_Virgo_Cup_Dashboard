# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.18.1
#   kernelspec:
#     display_name: moo
#     language: python
#     name: python3
# ---

# %%
# Import modules
import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# %%
# --- CONFIGURATION ---
# REPLACE THIS URL with your "Publish to Web" CSV link
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTR8Pa4QQVSNwepSe9dYnro3ZaVEpYQmBdZUzumuLL-U2IR3nKVh-_GbZeJHT2x9aCqnp7P-0hPm5Zd/pub?output=csv"

# Page Config
st.set_page_config(
    page_title="Virgo Cup CM5 Dashboard",
    page_icon="WK",
    layout="wide"
)


# %%
# --- DATA LOADING & CLEANING ---
@st.cache_data(ttl=60)  # CONSTANTLY UPDATING: Refreshes data from Google every 60 seconds
def load_data():
    try:
        # Load data directly from the live CSV URL
        df = pd.read_csv(SHEET_URL)
        
        # 1. Clean 'Winrate' (Remove % and convert to float)
        if 'winrate' in df.columns.str.lower():
            # Normalize column name
            col_name = [c for c in df.columns if 'winrate' in c.lower()][0]
            df['Win Rate %'] = df[col_name].astype(str).str.replace('%', '').astype(float)
        
        # 2. Clean 'Money Spent' (Remove $ or commas)
        if 'money spent' in df.columns.str.lower():
            col_name = [c for c in df.columns if 'money spent' in c.lower()][0]
            df['Money Spent'] = df[col_name].astype(str).str.replace('$', '').str.replace(',', '')
            df['Money Spent'] = pd.to_numeric(df['Money Spent'], errors='coerce').fillna(0)

        # 3. Parse 'R1D1' to extract main Uma name
        # Assumes format like "Oguri Cap (Leader)" or "Oguri Cap, Leader"
        target_col = [c for c in df.columns if 'R1D1' in c][0] if any('R1D1' in c for c in df.columns) else None
        if target_col:
            # Simple split to get the first part (The Name)
            df['Ace Uma'] = df[target_col].astype(str).apply(lambda x: x.split('(')[0].split(',')[0].strip())
        else:
            df['Ace Uma'] = "Unknown"

        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

# Load the data
df = load_data()

# %%
# --- SIDEBAR CONTROLS ---
st.sidebar.title("🏆 Virgo Cup Controls")
st.sidebar.markdown("Data auto-refreshes every 60s.")

if not df.empty:
    # Interactive Filters
    groups = list(df['CM group'].unique()) if 'CM group' in df.columns else []
    selected_group = st.sidebar.multiselect("Filter by CM Group", groups, default=groups)
    
    if selected_group:
        filtered_df = df[df['CM group'].isin(selected_group)]
    else:
        filtered_df = df

    # Manual Refresh Button
    if st.sidebar.button("Refresh Data Now"):
        st.cache_data.clear()
        st.rerun()

# %%
# --- MAIN DASHBOARD ---
st.title("🏆 Umamusume CM5 Virgo Cup Analytics")

if df.empty:
    st.warning("Waiting for data... Check your Google Sheet URL in the code.")
else:
    # Top Metrics
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Runs Recorded", filtered_df['runs done a day'].sum() if 'runs done a day' in filtered_df.columns else 0)
    c2.metric("Avg Winrate", f"{filtered_df['Win Rate %'].mean():.2f}%")
    c3.metric("Total Participants", len(filtered_df))

    st.markdown("---")

    # ROW 1: MATPLOTLIB & SEABORN GRAPHS
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("💸 Money Spent vs. Win Rate")
        fig1, ax1 = plt.subplots(figsize=(10, 6))
        
        # Using Seaborn as requested
        sns.scatterplot(
            data=filtered_df, 
            x='Money Spent', 
            y='Win Rate %', 
            hue='CM group', 
            style='CM group', 
            s=100, 
            ax=ax1,
            palette='viridis'
        )
        
        ax1.set_title("Does Whaling = Winning?", fontsize=14)
        ax1.grid(True, linestyle='--', alpha=0.7)
        st.pyplot(fig1)

    with col2:
        st.subheader("🐎 Win Rate Distribution by Group")
        fig2, ax2 = plt.subplots(figsize=(10, 6))
        
        sns.boxplot(
            data=filtered_df, 
            x='CM group', 
            y='Win Rate %', 
            palette='coolwarm',
            ax=ax2
        )
        
        ax2.set_title("Performance Spread per Group", fontsize=14)
        st.pyplot(fig2)

    # ROW 2: UMA USAGE
    st.subheader("📊 Most Popular 'Ace' Umas & Their Win Rates")
    
    # Aggregate data for the bar chart
    uma_stats = filtered_df.groupby('Ace Uma')['Win Rate %'].agg(['mean', 'count']).reset_index()
    uma_stats = uma_stats[uma_stats['count'] > 0].sort_values(by='mean', ascending=False)
    
    fig3, ax3 = plt.subplots(figsize=(12, 6))
    
    sns.barplot(
        data=uma_stats.head(10), # Top 10 only
        x='mean',
        y='Ace Uma',
        palette='magma',
        ax=ax3
    )
    
    ax3.set_xlabel("Average Win Rate (%)")
    ax3.set_ylabel("Uma Name")
    ax3.set_title("Top Performing Umas (Avg Win Rate)", fontsize=14)
    st.pyplot(fig3)

    # ROW 3: RAW DATA
    st.markdown("---")
    with st.expander("📂 View Raw Data Table"):
        st.dataframe(filtered_df)
