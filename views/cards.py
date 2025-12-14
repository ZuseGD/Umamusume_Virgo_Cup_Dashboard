import streamlit as st
import plotly.express as px
import pandas as pd
from virgo_utils import style_fig, PLOT_CONFIG, calculate_score

def show_view(team_df):
    st.header("🎴 Support Card Analysis")
    st.markdown("Analyze how owning specific support cards (and their Limit Break status) correlates with Win Rate.")
    
    # 1. Identify Card Columns dynamically
    # We look for any column in the dataframe that starts with 'card_'
    card_cols = [c for c in team_df.columns if c.startswith('card_')]
    
    if not card_cols:
        st.warning("⚠️ No support card data found. Please check if your CSV contains 'Card status' columns and if virgo_utils.py is updated.")
        return

    # 2. Create a clean mapping for the dropdown (Remove 'card_' prefix)
    card_options = {c: c.replace('card_', '') for c in card_cols}
    
    # 3. Dropdown Selector
    selected_col = st.selectbox(
        "Select Support Card:", 
        options=card_cols,
        format_func=lambda x: card_options[x]
    )
    
    clean_name = card_options[selected_col]

    # --- FIX: MERGE 'UNKNOWN' INTO 'NONE' ---
    # If a user didn't answer, we assume they don't have the card (None)
    # We create a temporary copy so we don't mess up the main dataframe
    plot_df = team_df.copy()
    plot_df[selected_col] = plot_df[selected_col].replace('Unknown', 'None')
    plot_df[selected_col] = plot_df[selected_col].fillna('None')
    # ----------------------------------------

    # --- MAIN CHART: WIN RATE DISTRIBUTION ---
    st.subheader(f"Win Rate by {clean_name} Ownership")
    
    # Logic to sort the X-Axis logically instead of Alphabetically
    # We want: None -> 0LB -> 1LB -> 2LB -> 3LB -> MLB
    ideal_order = ['None', '0LB', '1LB', '2LB', '3LB', 'MLB']
    
    # Filter to only include tiers that actually exist in the data
    existing_values = plot_df[selected_col].dropna().unique()
    final_order = [x for x in ideal_order if x in existing_values]

    
    # Add any weird values that might be in the data (e.g. typos) to the end
    extras = [x for x in existing_values if x not in final_order]
    final_order += extras

    # Create Box Plot
    fig = px.box(
        plot_df, 
        x=selected_col, 
        y='Calculated_WinRate', 
        color=selected_col,
        category_orders={selected_col: final_order}, # Apply our custom sort
        title=f"Win Rate Distribution: {clean_name}",
        labels={selected_col: "Limit Break (LB)", 'Calculated_WinRate': "Win Rate %"},
        template='plotly_dark',
        points="all" # Show individual dots for transparency
    )
    
    st.plotly_chart(style_fig(fig, height=500), width='stretch', config=PLOT_CONFIG)

    # --- STATS TABLE ---
    st.markdown("### 📊 Detailed Statistics")
    st.warning("⚠️ Note on Player Counts and Totals Please be aware that the current metrics reflect cumulative submissions rather than unique players. The processing logic groups data by Day and Timestamp. Consequently, if a player submitted data on multiple days (e.g., updating their score), they are counted as a distinct entry for each submission. This results in a higher total count than the actual number of unique participants.")
    
    # Group by the card status and calculate mean/median WR and count
    stats = plot_df.groupby(selected_col)['Calculated_WinRate'].agg(
        Count='count',
        Avg_WinRate='mean',
        Median_WinRate='median'
    ).reset_index()
    
    # Sort the table by our custom order
    stats[selected_col] = pd.Categorical(stats[selected_col], categories=final_order, ordered=True)
    stats = stats.sort_values(selected_col)
    
    # Format for display
    stats['Count'] = stats['Count'].map('{:,}'.format)
    stats['Avg_WinRate'] = stats['Avg_WinRate'].map('{:.1f}%'.format)
    stats['Median_WinRate'] = stats['Median_WinRate'].map('{:.1f}%'.format)

    stats = stats.rename(columns={
        selected_col: "Limit Break",  # Renames the dynamic column (e.g. 'card_Rice...') to 'Limit Break'
        "Count": "Total Entries",
        "Avg_WinRate": "Average Win Rate",
        "Median_WinRate": "Median Win Rate"
    })
    
    st.dataframe(stats, hide_index=True, width='stretch')