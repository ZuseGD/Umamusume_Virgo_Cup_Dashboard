import streamlit as st
import plotly.express as px
import pandas as pd
from utils import style_fig, PLOT_CONFIG, calculate_score, show_description

def show_view(df, team_df):
    # --- UPDATE NOTICE ---
    with st.expander("✨ What's New (Nov 24 Update)", expanded=True):
        st.markdown("""
        - 📸 **New Feature:** Added [OCR Data Analysis](#) tab (Parquet Data).
        - 👑 **Leaderboard Fixed:** Now ranks by Total Volume + Win Rate properly.
        - 📱 **Mobile Friendly:** Charts now resize dynamically for phone screens.
        - 💠 **Tier List:** Added "Popularity vs. Performance" Quadrant Chart.
        """)

    
    st.header("Global Overview")
    
    # Metrics
    total_runs = team_df['Clean_Races'].sum()
    avg_wr = team_df['Calculated_WinRate'].mean()
    active_trainers = team_df['Clean_IGN'].nunique()
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Races", int(total_runs))
    m2.metric("Avg Win Rate", f"{avg_wr:.1f}%")
    m3.metric("Trainers", int(active_trainers))
    
    st.markdown("---")

    # TRAINER INSPECTOR
    st.subheader("🧑‍🏫 Trainer Inspector")
    all_trainers = sorted(team_df['Clean_IGN'].unique()) 
    target_trainer = st.selectbox("Search Trainer Stats:", [""] + all_trainers)
    
    if target_trainer:
        t_data = team_df[team_df['Clean_IGN'] == target_trainer]
        if not t_data.empty:
            t_runs = t_data['Clean_Races'].sum()
            t_wins = t_data['Clean_Wins'].sum()
            t_wr = (t_wins / t_runs * 100) if t_runs > 0 else 0.0
            
            fav_team = t_data['Team_Comp'].mode()[0] if not t_data.empty else "N/A"
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Win Rate", f"{t_wr:.1f}%")
            c2.metric("Runs", int(t_runs))
            c3.info(f"**Main Team:** {fav_team}")
    
    st.markdown("---")

    st.markdown("### 📊 Global Context")
    g1, g2 = st.columns(2)
    
    with g1:
        # 1. Win Rate Distribution
        fig_dist = px.histogram(
            team_df, 
            x="Calculated_WinRate", 
            nbins=20, 
            title="Distribution of Player Win Rates",
            template='plotly_dark',
            labels={'Calculated_WinRate': 'Win Rate %'}
        )
        fig_dist.update_layout(bargap=0.1, yaxis_title="Player Count")
        st.plotly_chart(style_fig(fig_dist, height=400), width="stretch", config=PLOT_CONFIG)
        show_description("dist_wr")
        
    with g2:
        # 2. Group Difficulty
        group_stats = team_df.groupby('Clean_Group')['Calculated_WinRate'].mean().reset_index()
        fig_group = px.bar(
            group_stats, 
            x='Clean_Group', 
            y='Calculated_WinRate',
            title="Average Win Rate by Group",
            template='plotly_dark',
            color='Calculated_WinRate',
            color_continuous_scale='Redor'
        )
        fig_group.update_layout(showlegend=False, yaxis_title="Avg Win Rate (%)", xaxis_title=None)
        st.plotly_chart(style_fig(fig_group, height=400), width="stretch", config=PLOT_CONFIG)
        show_description("group_diff")

    # LEADERBOARD
    st.subheader("👑 Top Performers")
    
    named_teams = team_df[team_df['Display_IGN'] != "Anonymous Trainer"].copy()
    
    # 1. AGGREGATE BY TRAINER ONLY (Fixes the split-team issue)
    leaderboard = named_teams.groupby('Display_IGN').agg({
        'Clean_Wins': 'sum', 
        'Clean_Races': 'sum',
        # Find their most frequent team to display as a label
        'Team_Comp': lambda x: x.mode()[0] if not x.mode().empty else "Various"
    }).reset_index()
    
    leaderboard['Global_WinRate'] = (leaderboard['Clean_Wins'] / leaderboard['Clean_Races']) * 100
    leaderboard['Score'] = leaderboard.apply(lambda x: calculate_score(x['Clean_Wins'], x['Clean_Races']), axis=1)
    leaderboard = leaderboard[leaderboard['Clean_Races'] >= 15]
    
    top_leaders = leaderboard.sort_values('Score', ascending=False).head(10)
    # Sort for chart display (lowest at bottom)
    top_leaders = top_leaders.sort_values('Score', ascending=True)
    
    # 2. CHART GENERATION
    fig_leader = px.bar(
        top_leaders, 
        x='Score', 
        y='Display_IGN', 
        orientation='h', 
        color='Global_WinRate',
        text='Clean_Wins', 
        template='plotly_dark', 
        color_continuous_scale='Turbo', 
        height=700,
        # Pass the Main Team to the hover tooltip
        hover_data={'Team_Comp': True, 'Display_IGN': False} 
    )
    
    fig_leader.update_traces(
        texttemplate='Wins: %{text} | WR: %{marker.color:.1f}%', 
        textposition='inside',
        hovertemplate='<b>%{y}</b><br>Main Team: %{customdata[0]}<br>Score: %{x:.1f}<extra></extra>'
    )
    
    fig_leader.update_layout(xaxis_title="Performance Score", yaxis_title=None)
    st.plotly_chart(style_fig(fig_leader, height=700), width="stretch", config=PLOT_CONFIG)
    show_description("leaderboard")

    # MONEY
    st.subheader("💰 Spending vs. Win Rate")
    team_df_sorted = team_df.sort_values('Sort_Money')
    fig_money = px.box(
        team_df_sorted, x='Original_Spent', y='Calculated_WinRate', color='Original_Spent',
        points="all", template='plotly_dark', color_discrete_sequence=px.colors.qualitative.Bold, height=600
    )
    fig_money.update_layout(showlegend=False, yaxis_title="Win Rate (%)", xaxis_title="Spending Tier")
    st.plotly_chart(style_fig(fig_money, height=600), width="stretch", config=PLOT_CONFIG)
    show_description("money")