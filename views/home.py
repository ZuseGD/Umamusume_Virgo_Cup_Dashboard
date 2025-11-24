import streamlit as st
import plotly.express as px
import pandas as pd
from utils import style_fig, PLOT_CONFIG, calculate_score

def show_view(df, team_df):
    st.header("Global Overview")
    
   # --- GLOBAL FILTERS (Visible on every page) ---
        # We use an expander so it is accessible but doesn't clutter the view
    with st.expander("⚙️ Global Filters (Round, Day, Group)", expanded=False):
        f1, f2, f3 = st.columns(3)
        
        # 1. Group Filter
        with f1:
            # Get unique groups, sorted
            groups = sorted(list(df['Clean_Group'].unique()))
            selected_group = st.multiselect("Filter Group", groups, default=groups)
            
        # 2. Round Filter
        with f2:
            # Get unique rounds (e.g., Round 1, Round 2)
            rounds = sorted(list(df['Round'].unique()))
            selected_round = st.multiselect("Filter Round", rounds, default=rounds)
            
        # 3. Day Filter
        with f3:
            # Get unique days (e.g., Day 1, Day 2)
            days = sorted(list(df['Day'].unique()))
            selected_day = st.multiselect("Filter Day", days, default=days)

        # --- APPLY FILTERS TO DATA ---
        # This updates BOTH the individual data (df) and team data (team_df)
        # passing the filtered versions to your views.

    if selected_group:
        df = df[df['Clean_Group'].isin(selected_group)]
        team_df = team_df[team_df['Clean_Group'].isin(selected_group)]

    if selected_round:
        df = df[df['Round'].isin(selected_round)]
        team_df = team_df[team_df['Round'].isin(selected_round)]

    if selected_day:
        df = df[df['Day'].isin(selected_day)]
        team_df = team_df[team_df['Day'].isin(selected_day)]
    
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
            t_wr = t_data['Calculated_WinRate'].mean()
            t_runs = t_data['Clean_Races'].sum()
            fav_team = t_data['Team_Comp'].mode()[0] if not t_data.empty else "N/A"
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Win Rate", f"{t_wr:.1f}%")
            c2.metric("Runs", int(t_runs))
            c3.info(f"**Main Team:** {fav_team}")
    
    st.markdown("---")

    # LEADERBOARD
    st.subheader("👑 Top Performers")
    
    named_teams = team_df[team_df['Display_IGN'] != "Anonymous Trainer"].copy()
    leaderboard = named_teams.groupby('Display_IGN').agg({
        'Clean_Wins': 'sum', 
        'Clean_Races': 'sum',
        'Team_Comp': lambda x: x.mode()[0] if not x.mode().empty else "Various"
    }).reset_index()
    
    leaderboard['Global_WinRate'] = (leaderboard['Clean_Wins'] / leaderboard['Clean_Races']) * 100
    leaderboard['Score'] = leaderboard.apply(lambda x: calculate_score(x['Clean_Wins'], x['Clean_Races']), axis=1)
    leaderboard = leaderboard[leaderboard['Clean_Races'] >= 15]
    
    top_leaders = leaderboard.sort_values('Score', ascending=False).head(10)
    top_leaders = top_leaders.sort_values('Score', ascending=True)
    top_leaders['Label'] = top_leaders['Display_IGN'] + " (" + top_leaders['Team_Comp'] + ")"
    
    fig_leader = px.bar(
        top_leaders, x='Score', y='Label', orientation='h', color='Global_WinRate',
        text='Clean_Wins', template='plotly_dark', color_continuous_scale='Turbo', height=700
    )
    fig_leader.update_traces(texttemplate='Wins: %{text} | WR: %{marker.color:.1f}%', textposition='inside')
    fig_leader.update_layout(xaxis_title="Performance Score", yaxis_title=None)
    st.plotly_chart(style_fig(fig_leader, height=700), use_container_width=True, config=PLOT_CONFIG)

    # MONEY
    st.subheader("💰 Spending vs. Win Rate")
    team_df_sorted = team_df.sort_values('Sort_Money')
    fig_money = px.box(
        team_df_sorted, x='Original_Spent', y='Calculated_WinRate', color='Original_Spent',
        points="all", template='plotly_dark', color_discrete_sequence=px.colors.qualitative.Bold, height=600
    )
    fig_money.update_layout(showlegend=False, yaxis_title="Win Rate (%)", xaxis_title="Spending Tier")
    st.plotly_chart(style_fig(fig_money, height=600), use_container_width=True, config=PLOT_CONFIG)