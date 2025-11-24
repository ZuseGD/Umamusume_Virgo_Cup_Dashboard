import streamlit as st
import plotly.express as px
from utils import style_fig, PLOT_CONFIG

def show_view(df, team_df):
    st.header("🃏 Resource Analysis")
    
    st.subheader("Support Card Impact")
    card_map = {}
    for c in df.columns:
        if "Card Status" in c:
            card_name = c.split('[')[-1].replace(']', '').strip()
            card_map[card_name] = c
            
    if card_map:
        target_name = st.selectbox("Select Card", sorted(list(card_map.keys())))
        col_match = card_map[target_name]
        
        card_stats = df.drop_duplicates(subset=['Clean_IGN', 'Round', 'Day']).groupby(col_match)['Calculated_WinRate'].mean().reset_index()
        fig_card = px.bar(
            card_stats, x=col_match, y='Calculated_WinRate', color='Calculated_WinRate',
            color_continuous_scale='Bluered', template='plotly_dark', title=f"Win Rate by {target_name} Status",
            text='Calculated_WinRate', height=500
        )
        fig_card.update_traces(texttemplate='%{text:.1f}%', textposition='inside')
        fig_card.update_layout(xaxis_title="Limit Break Status")
        st.plotly_chart(style_fig(fig_card, height=500), use_container_width=True, config=PLOT_CONFIG)
    else:
        st.warning("No Card Data found.")

    st.subheader("Meta Trends (Round 1 vs Round 2)")
    if 'Round' in df.columns and 'Day' in df.columns:
        trend_df = team_df.groupby(['Round', 'Day']).agg({'Calculated_WinRate': 'mean', 'Clean_Races': 'count'}).reset_index()
        trend_df['Session'] = trend_df['Round'] + " " + trend_df['Day']
        
        fig_trend = px.line(
            trend_df, x='Session', y='Calculated_WinRate', title="Global Win Rate Trend",
            markers=True, template='plotly_dark', text='Calculated_WinRate', height=500
        )
        fig_trend.update_traces(textposition="top center", texttemplate='%{text:.1f}%')
        st.plotly_chart(style_fig(fig_trend, height=500), use_container_width=True, config=PLOT_CONFIG)