import streamlit as st
import plotly.express as px
from utils import style_fig, PLOT_CONFIG, show_description

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
            
            # 1. AGGREGATE MEAN WR AND PLAYER COUNT
            # We count 'Clean_IGN' to see how many players are in each category
            card_stats = df.drop_duplicates(subset=['Clean_IGN', 'Round', 'Day']).groupby(col_match).agg({
                'Calculated_WinRate': 'mean',
                'Clean_IGN': 'count'
            }).reset_index().rename(columns={'Clean_IGN': 'Player_Count'})
            
            # 2. PLOT WITH HOVER DATA
            fig_card = px.bar(
                card_stats, 
                x=col_match, 
                y='Calculated_WinRate', 
                color='Calculated_WinRate',
                color_continuous_scale='Bluered', 
                template='plotly_dark', 
                title=f"Win Rate by {target_name} Status",
                text='Calculated_WinRate', 
                height=600,
                # Add the new count column to the hover data
                hover_data={'Player_Count': True, 'Calculated_WinRate': ':.1f'} 
            )
            
            # 3. CUSTOMIZE HOVER TOOLTIP
            fig_card.update_traces(
                texttemplate='%{text:.1f}%', 
                textposition='inside',
                # Displays: "LB Status" -> "Win Rate: 55.0%" -> "Count: 120"
                hovertemplate='<b>%{x}</b><br>Win Rate: %{y:.1f}%<br>Count: %{customdata[0]}<extra></extra>'
            )
            
            fig_card.update_layout(xaxis_title="Limit Break Status")
            st.plotly_chart(style_fig(fig_card, height=600), width="stretch", config=PLOT_CONFIG)
            show_description("cards")
    else:
        st.warning("No Card Data found.")

    st.markdown("---")
    st.subheader("🍀 Luck vs. Grind Analysis")
    
    # Filter for players with at least 5 races to remove 1-race wonders
    grind_df = team_df[team_df['Clean_Races'] >= 5]
    
    fig_luck = px.scatter(
        grind_df, 
        x='Clean_Races', 
        y='Calculated_WinRate',
        color='Calculated_WinRate',
        title="Do more races = Lower Win Rate?",
        template='plotly_dark',
        labels={'Clean_Races': 'Total Races Played', 'Calculated_WinRate': 'Win Rate %'},
        trendline="ols" # Requires statsmodels, if not installed remove this line
    )
    st.plotly_chart(style_fig(fig_luck, height=500), width="stretch", config=PLOT_CONFIG)
    show_description("luck_grind")

    st.markdown("---")

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
        show_description("evolution")