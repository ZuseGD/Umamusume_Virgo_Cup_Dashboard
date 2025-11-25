import streamlit as st
import plotly.express as px
from utils import style_fig, PLOT_CONFIG, dynamic_height, show_description

def show_view(df, team_df):
    st.header("🐴 Individual Uma Performance")
    st.warning("⚠️ **NOTE:** Win Rates are based on **TEAM Performance** when this Uma is present. It does NOT track individual race wins.")
    
    # Calculate Total Entries for Percentage Maths
    total_entries = len(df)

    # --- 1. UMA INSPECTOR ---
    st.subheader("🔎 Uma Inspector")
    all_umas = sorted(df['Clean_Uma'].unique())
    target_uma = st.selectbox("Select Uma:", [""] + all_umas)

    if target_uma:
        uma_data = df[df['Clean_Uma'] == target_uma]
        avg_wr = uma_data['Calculated_WinRate'].mean()
        unique_players = uma_data['Clean_IGN'].nunique()
        
        # Calculate Global Pick Rate for this specific Uma
        uma_pick_rate = (len(uma_data) / total_entries) * 100
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Win Rate", f"{avg_wr:.1f}%")
        c2.metric("Pick Rate", f"{uma_pick_rate:.1f}%")
        c3.metric("Unique Users", int(unique_players))
        
        # Prepare Strategy Data
        strat_stats = uma_data.groupby('Clean_Style')['Calculated_WinRate'].agg(['mean', 'count']).reset_index()
        strat_stats.columns = ['Strategy', 'Win_Rate', 'Entries']
        
        # Calculate Strategy Distribution % (e.g., 80% of Oguris are Christmas)
        strat_stats['Style_Pick_Rate'] = (strat_stats['Entries'] / len(uma_data)) * 100

        # Chart: Strategy Breakdown
        fig_drill = px.bar(
            strat_stats, 
            x='Win_Rate', 
            y='Strategy', 
            orientation='h', 
            title=f"Strategy Breakdown for {target_uma}", 
            template='plotly_dark', 
            height=400,
            # Pass new Pick Rate to hover
            hover_data={'Entries': True, 'Win_Rate': ':.1f', 'Style_Pick_Rate': ':.1f', 'Strategy': False}
        )
        
        fig_drill.update_traces(
            texttemplate='%{x:.1f}%', 
            textposition='inside',
            # Tooltip: Strategy -> Win Rate -> Pick Rate -> Count
            hovertemplate='<b>%{y}</b><br>Win Rate: %{x:.1f}%<br>Usage: %{customdata[1]:.1f}%<br>Entries: %{customdata[0]}<extra></extra>'
        )
        
        fig_drill.update_layout(xaxis_title="Win Rate (%)", yaxis_title=None)
        st.plotly_chart(style_fig(fig_drill, height=400), width="stretch", config=PLOT_CONFIG)
        show_description("drilldown")

    st.markdown("---")
    
    # --- 2. TIER LIST SECTION ---
    st.subheader("📊 Uma Tier List")
    
    # Aggregate Stats
    uma_stats = df.groupby('Clean_Uma').agg({
        'Calculated_WinRate': 'mean', 
        'Clean_Races': 'count'
    }).reset_index()
    
    # Calculate Global Pick Rate
    uma_stats['Pick_Rate'] = (uma_stats['Clean_Races'] / total_entries) * 100
    
    # Filter: Hide very low sample size (less than 10 entries)
    uma_stats = uma_stats[uma_stats['Clean_Races'] >= 10]
    
    # Prepare Top 15 for Bar Chart
    top_umas = uma_stats.sort_values('Calculated_WinRate', ascending=False).head(15).copy()
    top_umas['Short_Name'] = top_umas['Clean_Uma'].apply(
        lambda x: x[:18] + ".." if len(x) > 18 else x
    )

    # Dynamic Height Calculation
    n_items = len(top_umas)
    chart_height = dynamic_height(n_items, min_height=600, per_item=45)

    # SCATTER PLOT (Quadrants)
    st.markdown("#### 💠 Popularity vs. Performance (Quadrants)")
    fig_scatter = px.scatter(
        uma_stats, 
        x='Pick_Rate',              # <--- UPDATED: Now uses Pick Rate %
        y='Calculated_WinRate',
        size='Clean_Races',         # Keep size as count to visualize volume weight
        color='Calculated_WinRate',
        color_continuous_scale='Viridis',
        title="Uma Tier List: Pick Rate vs Performance",
        template='plotly_dark',
        hover_name='Clean_Uma',
        labels={'Pick_Rate': 'Pick Rate (%)', 'Calculated_WinRate': 'Win Rate (%)'},
        height=600
    )
    
    # Add Average Reference Lines
    avg_wr = uma_stats['Calculated_WinRate'].mean()
    avg_pick = uma_stats['Pick_Rate'].mean()
    
    fig_scatter.add_hline(y=avg_wr, line_dash="dot", annotation_text="Avg WR", annotation_position="bottom left")
    fig_scatter.add_vline(x=avg_pick, line_dash="dot", annotation_text="Avg Pick Rate", annotation_position="top right")
    
    st.plotly_chart(style_fig(fig_scatter, height=600), width="stretch", config=PLOT_CONFIG)
    show_description("scatter_tier")
    
    # BAR CHART (Rankings)
    st.markdown("#### 🏆 Detailed Rankings")

    fig_uma = px.bar(
        top_umas,
        x='Calculated_WinRate', 
        y='Short_Name',            
        orientation='h', 
        color='Calculated_WinRate', 
        color_continuous_scale='Viridis', 
        text='Pick_Rate',          # <--- UPDATED: Text shows Pick Rate %
        template='plotly_dark', 
        # Pass extra data for tooltip
        hover_data={'Clean_Uma': True, 'Short_Name': False, 'Clean_Races': True},
        height=chart_height
    )
    
    fig_uma.update_layout(
        yaxis={'categoryorder':'total ascending'}, 
        xaxis_title="Avg Win Rate (%)", 
        yaxis_title="Character"
    )
    
    # Customize Text and Tooltip
    fig_uma.update_traces(
        texttemplate='WR: %{x:.1f}% | Pick: %{text:.1f}%', 
        textposition='inside',
        hovertemplate='<b>%{customdata[0]}</b><br>Win Rate: %{x:.1f}%<br>Pick Rate: %{text:.1f}%<br>Entries: %{customdata[2]}<extra></extra>'
    )
    
    st.plotly_chart(style_fig(fig_uma, height=chart_height), width="stretch", config=PLOT_CONFIG)
    show_description("uma_bar")