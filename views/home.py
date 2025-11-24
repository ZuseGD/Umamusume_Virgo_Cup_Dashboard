import streamlit as st
import plotly.express as px
import pandas as pd
from utils import load_data, style_fig, PLOT_CONFIG, calculate_score, footer_html

st.set_page_config(
    page_title="Virgo Cup CM5",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Load Data
df, team_df = load_data()

st.title("🏆 Virgo Cup Global Overview")

if not df.empty:
    # --- SIDEBAR FILTER ---
    st.sidebar.header("⚙️ Filters")
    groups = list(df['Clean_Group'].unique())
    selected = st.sidebar.multiselect("Filter Group", groups, default=groups)
    
    if selected:
        team_df = team_df[team_df['Clean_Group'].isin(selected)]

    # --- TOP METRICS ---
    total_runs = team_df['Clean_Races'].sum()
    avg_wr = team_df['Calculated_WinRate'].mean()
    active_trainers = team_df['Clean_IGN'].nunique()
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Data Points", int(total_runs), help="Total individual races recorded")
    m2.metric("Global Avg Win Rate", f"{avg_wr:.1f}%", help="Average across all submissions")
    m3.metric("Active Trainers", int(active_trainers))
    
    st.markdown("---")

    # --- LEADERBOARD & INSPECTOR ---
    st.subheader("👑 Top Performers")
    
    # Trainer Inspector
    all_trainers = sorted(team_df['Clean_IGN'].unique()) 
    target_trainer = st.selectbox("🧑‍🏫 Search Trainer Stats:", [""] + all_trainers)
    
    if target_trainer:
        t_data = team_df[team_df['Clean_IGN'] == target_trainer]
        if not t_data.empty:
            t_wr = t_data['Calculated_WinRate'].mean()
            t_runs = t_data['Clean_Races'].sum()
            fav_team = t_data['Team_Comp'].mode()[0] if not t_data.empty else "N/A"
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Trainer Win Rate", f"{t_wr:.1f}%")
            c2.metric("Total Runs", int(t_runs))
            c3.info(f"**Fav Team:** {fav_team}")
        else:
            st.warning("No data found for this trainer.")
    
    # Leaderboard Chart
    named_teams = team_df[team_df['Display_IGN'] != "Anonymous Trainer"].copy()
    leaderboard = named_teams.groupby(['Display_IGN', 'Team_Comp']).agg({'Clean_Wins': 'sum', 'Clean_Races': 'sum'}).reset_index()
    leaderboard['Global_WinRate'] = (leaderboard['Clean_Wins'] / leaderboard['Clean_Races']) * 100
    leaderboard['Score'] = leaderboard.apply(lambda x: calculate_score(x['Clean_Wins'], x['Clean_Races']), axis=1)
    leaderboard = leaderboard[leaderboard['Clean_Races'] >= 15]
    
    top_leaders = leaderboard.sort_values('Score', ascending=False).head(10)
    top_leaders = top_leaders.sort_values('Score', ascending=True)
    top_leaders['Label'] = top_leaders['Display_IGN'] + " (" + top_leaders['Team_Comp'] + ")"
    
    fig_leader = px.bar(
        top_leaders, x='Score', y='Label', orientation='h', color='Global_WinRate',
        text='Clean_Wins', template='plotly_dark', color_continuous_scale='Turbo', height=600
    )
    fig_leader.update_traces(texttemplate='Wins: %{text} | WR: %{marker.color:.1f}%', textposition='inside')
    fig_leader.update_layout(xaxis_title="Performance Score", yaxis_title=None)
    st.plotly_chart(style_fig(fig_leader, height=600), width='stretch', config=PLOT_CONFIG)

    st.markdown("---")

    # --- SPENDING ---
    st.subheader("💰 Spending vs. Win Rate")
    team_df_sorted = team_df.sort_values('Sort_Money')
    fig_money = px.box(
        team_df_sorted, x='Original_Spent', y='Calculated_WinRate', color='Original_Spent',
        points="all", template='plotly_dark', color_discrete_sequence=px.colors.qualitative.Bold, height=600
    )
    fig_money.update_layout(showlegend=False, yaxis_title="Win Rate (%)", xaxis_title="Spending Tier")
    st.plotly_chart(style_fig(fig_money, height=600), width='stretch', config=PLOT_CONFIG)

st.markdown(footer_html, unsafe_allow_html=True)