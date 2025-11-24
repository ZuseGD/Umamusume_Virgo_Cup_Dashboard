import streamlit as st
import plotly.express as px
from utils import style_fig, PLOT_CONFIG, dynamic_height

def show_view(df, team_df):
    st.header("🐴 Individual Uma Performance")
    st.warning("⚠️ **NOTE:** Win Rates are based on **TEAM Performance** when this Uma is present. It does NOT track individual race wins.")
    
    # UMA INSPECTOR
    st.subheader("🔍 Uma Inspector")
    all_umas = sorted(df['Clean_Uma'].unique())
    target_uma = st.selectbox("Select Uma:", [""] + all_umas)

    if target_uma:
        uma_data = df[df['Clean_Uma'] == target_uma]
        avg_wr = uma_data['Calculated_WinRate'].mean()
        unique_players = uma_data['Clean_IGN'].nunique()
        
        c1, c2 = st.columns(2)
        c1.metric("Win Rate", f"{avg_wr:.1f}%")
        c2.metric("Unique Users", int(unique_players))
        
        strat_stats = uma_data.groupby('Clean_Style')['Calculated_WinRate'].agg(['mean', 'count'])
        fig_drill = px.bar(strat_stats, x='mean', y=strat_stats.index, orientation='h', title=f"Strategy Breakdown for {target_uma}", template='plotly_dark', height=400)
        st.plotly_chart(style_fig(fig_drill, height=400), use_container_width=True, config=PLOT_CONFIG)

    st.markdown("---")
    
    # TIER LIST
    st.subheader("📊 Uma Tier List")
    uma_stats = df.groupby('Clean_Uma').agg({'Calculated_WinRate': 'mean', 'Clean_Races': 'count'}).reset_index()
    uma_stats = uma_stats[uma_stats['Clean_Races'] >= 10]
    top_umas = uma_stats.sort_values('Calculated_WinRate', ascending=False).head(15)
    # --- ADD THIS TRUNCATION LOGIC ---
    top_umas['Short_Name'] = top_umas['Clean_Uma'].apply(
        lambda x: x[:18] + ".." if len(x) > 18 else x
    )
    # Calculate Height
    n_items = len(top_umas)
    chart_height = dynamic_height(n_items, min_height=200, per_item=45)
    
    fig_uma = px.bar(
        top_umas.sort_values('Calculated_WinRate', ascending=False).head(15), 
        x='Calculated_WinRate', 
        y='Short_Name', 
        orientation='h', 
        color='Calculated_WinRate', 
        color_continuous_scale='Viridis', 
        text='Clean_Races', 
        template='plotly_dark', 
        hover_name='Clean_Uma',
        height=chart_height
    )
    fig_uma.update_layout(yaxis={'categoryorder':'total ascending'}, xaxis_title="Avg Win Rate (%)", yaxis_title="Character")
    fig_uma.update_traces(texttemplate='WR: %{x:.1f}% | Runs: %{text}', textposition='inside')
    st.plotly_chart(style_fig(fig_uma, height=chart_height), use_container_width=True, config=PLOT_CONFIG)