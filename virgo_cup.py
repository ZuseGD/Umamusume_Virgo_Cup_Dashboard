# ---
# jupyter:
#   jupytext:
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
# --- REUSABLE HELPER FUNCTIONS ---
def find_column(df, keywords):
    """
    Searches for a column name that matches a list of keywords.
    Returns the actual column name or None.
    This isolates the logic so if you rename 'Money Spent' to 'Total Cost', 
    the app still works as long as 'cost' is in the keywords.
    """
    clean_cols = df.columns.str.lower().str.replace(' ', '').str.replace('_', '')
    for i, col in enumerate(clean_cols):
        for key in keywords:
            if key in col:
                return df.columns[i]
    return None

def clean_currency(series):
    """
    Reusable function to turn '$1,000', '1,000', or '1000' into float 1000.0
    """
    return (series.astype(str)
            .str.replace('$', '', regex=False)
            .str.replace(',', '', regex=False)
            .str.replace(' ', '', regex=False)
            .apply(pd.to_numeric, errors='coerce')
            .fillna(0))

def clean_percentage(series):
    """
    Reusable function to turn '50%', '0.5', or '50' into float 50.0
    """
    s = series.astype(str).str.replace('%', '', regex=False)
    return pd.to_numeric(s, errors='coerce').fillna(0)

def parse_uma_details(series):
    """
    Extracts the main Uma name from complex strings.
    Example: 'Oguri Cap (Christmas) - Leader' -> 'Oguri Cap (Christmas)'
    """
    return series.astype(str).apply(lambda x: x.split('-')[0].split('(')[0].strip())


# %%
# --- MAIN DATA PIPELINE ---

@st.cache_data(ttl=60)  # OPTIMIZATION: Cache data for 60 seconds to handle constant updates
def load_and_process_data():
    try:
        df = pd.read_csv(SHEET_URL)
        
        # --- 1. ISOLATE COLUMNS (Concept Mapping) ---
        # We map "Concepts" (like Money) to "Actual Columns" dynamically
        col_map = {
            'win_rate': find_column(df, ['winrate', 'win%', 'wr', 'rate']),
            'money': find_column(df, ['money', 'spent', 'cost', 'whale']),
            'runs': find_column(df, ['runs', 'attempts', 'count', 'total']),
            'group': find_column(df, ['group', 'bracket', 'league']),
            'ace_uma': find_column(df, ['r1d1', 'uma1', 'ace', 'character']),
        }

        # --- 2. APPLY TRANSFORMATIONS ---
        
        # Process Win Rate
        if col_map['win_rate']:
            df['Clean_WinRate'] = clean_percentage(df[col_map['win_rate']])
        else:
            df['Clean_WinRate'] = 0.0

        # Process Money
        if col_map['money']:
            df['Clean_Money'] = clean_currency(df[col_map['money']])
        else:
            df['Clean_Money'] = 0.0

        # Process Runs (Ensure numeric)
        if col_map['runs']:
            df['Clean_Runs'] = pd.to_numeric(df[col_map['runs']], errors='coerce').fillna(0)
        else:
            df['Clean_Runs'] = 0

        # Process Ace Uma Name
        if col_map['ace_uma']:
            df['Clean_AceName'] = parse_uma_details(df[col_map['ace_uma']])
        else:
            df['Clean_AceName'] = "Unknown"
            
        # Normalize Group Name
        if col_map['group']:
            df['Clean_Group'] = df[col_map['group']].fillna("Unknown")
        else:
            df['Clean_Group'] = "Unknown"

        return df, col_map

    except Exception as e:
        st.error(f"Data Pipeline Error: {e}")
        return pd.DataFrame(), {}



# %%
# --- LOAD DATA ---
df, cols_found = load_and_process_data()

# --- SIDEBAR FILTERS ---
st.sidebar.header("🏆 Virgo Cup Controls")

if not df.empty:
    # Dynamic Group Filter
    available_groups = list(df['Clean_Group'].unique())
    selected_groups = st.sidebar.multiselect("Filter by Group", available_groups, default=available_groups)
    
    # Apply Filter
    if selected_groups:
        filtered_df = df[df['Clean_Group'].isin(selected_groups)]
    else:
        filtered_df = df

    # Refresh Button
    if st.sidebar.button("🔄 Refresh Live Data"):
        st.cache_data.clear()
        st.rerun()

# %%
# --- DASHBOARD UI ---
st.title("🏆 Umamusume CM5 Virgo Cup Analytics")

if df.empty:
    st.warning("Waiting for data connection... ensure your Google Sheet is published as CSV.")
else:
    # KPIS
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Total Runs", int(filtered_df['Clean_Runs'].sum()))
    kpi2.metric("Avg Win Rate", f"{filtered_df['Clean_WinRate'].mean():.1f}%")
    kpi3.metric("Trainers Tracked", len(filtered_df))

    st.divider()

    # CHARTS
    tab1, tab2 = st.tabs(["📈 Performance Analytics", "💾 Raw Data"])

    with tab1:
        c1, c2 = st.columns(2)
        
        with c1:
            st.subheader("💸 Investment vs. Performance")
            fig1, ax1 = plt.subplots(figsize=(8, 5))
            
            # Scatter plot showing Money vs Win Rate
            sns.scatterplot(
                data=filtered_df,
                x='Clean_Money',
                y='Clean_WinRate',
                hue='Clean_Group',
                size='Clean_Runs',
                sizes=(50, 300),
                alpha=0.7,
                palette='viridis',
                ax=ax1
            )
            ax1.set_xlabel("Money Spent ($)")
            ax1.set_ylabel("Win Rate (%)")
            ax1.grid(True, linestyle='--', alpha=0.3)
            st.pyplot(fig1)

        with c2:
            st.subheader("🐎 Meta Report: Top Aces")
            # Custom Aggregation for Bar Chart
            uma_perf = filtered_df.groupby('Clean_AceName').agg({
                'Clean_WinRate': 'mean',
                'Clean_Runs': 'count'
            }).reset_index()
            
            # Filter out low sample size (arbitrary < 1 entry) & Top 8
            uma_perf = uma_perf[uma_perf['Clean_Runs'] > 0].sort_values('Clean_WinRate', ascending=False).head(8)
            
            fig2, ax2 = plt.subplots(figsize=(8, 5))
            sns.barplot(
                data=uma_perf,
                y='Clean_AceName',
                x='Clean_WinRate',
                palette='magma',
                ax=ax2
            )
            ax2.set_xlabel("Avg Win Rate (%)")
            ax2.set_ylabel("")
            st.pyplot(fig2)

    with tab2:
        st.markdown("### Debugging & Raw View")
        st.info("This view shows how the app 'mapped' your headers to its logic.")
        st.write(f"**Column Mapping:** {cols_found}")
        st.dataframe(filtered_df)
