import streamlit as st
import plotly.express as px
import pandas as pd
import os
import base64
from virgo_utils import style_fig, PLOT_CONFIG, calculate_score, show_description

def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except:
        return None

def show_view(df, team_df, current_config):
    
    # --- CSS: Styling ---
    st.markdown("""
    <style>
        div[data-testid="stLinkButton"] { height: 100%; min-height: 50px; }
        div[data-testid="stLinkButton"] > a { height: 100%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 1.1rem; }
    </style>
    """, unsafe_allow_html=True)

    # --- TOP LAYOUT ---
    col_header, col_btn = st.columns([1, 1], gap="medium")

    with col_header:
        with st.expander("✨ What's New: Bug Fixes and Logic Updates", expanded=True):
            st.markdown("""
            ### 🔄 Unified Character Variants (Normalization)
- **Feature:** Implemented a `normalize_name` system to merge identical characters with slightly different variant names.
- **Impact:** Names like *"Uma (Anime Collab)"* are now correctly grouped with *"Uma (Anime)"*. This prevents statistics from splitting into two separate entries, ensuring more accurate Win Rates and Pick Rates in the **Meta Matrix** and **Oshi Awards**.

### 🕵️ Expanded Champion Pool (Opponent Recovery)
- **The Problem:** Previously, "Skill Lift" and "Champion Stats" only analyzed the submitting player's team. If an opponent won the lobby, their data was often ignored even if it existed in the logs.
- **The Solution:** The dashboard now cross-references confirmed **Lobby Winners** against the raw `finals.parquet` file.
- **Impact:** It successfully "recovers" winning opponent data by filtering for the winner's name and excluding known losers (verified via stats/skills signatures). This significantly increases the sample size for meta analysis (e.g., capturing missing Opponent King Halo winners).

### 🧩 Smart Style Backfilling
- **Feature:** Added logic to "patch" missing style data for opponents.

## Bug Fixes

- **🐛 Fixed Parquet Loading Error:** Resolved a `KeyError: 'Match_Uma'` crash that occurred when loading raw parquet files that used different column schemas (e.g., `name` vs `Match_Uma`).
- **🛡️ Robust Column Generation:** Added a fail-safe to automatically generate `Match_Uma` using `smart_match_name` if the column is missing from the source file.

## Technical Changes

- **New Function:** `normalize_name(name)` added to `views/finals.py`.
- **Dependencies:** Now imports `VARIANT_MAP` and `smart_match_name` from `virgo_utils`.
- **Logic Update:** The "True Winners" calculation now applies normalization before counting, ensuring the "Individual Lobby Winners" chart is accurate.
            """)

    with col_btn:
        form_url = current_config.get('form_url')
        banner_path = "images/survey_banner.png"
        if form_url:
            if os.path.exists(banner_path):
                img_b64 = get_base64_image(banner_path)
                if img_b64:
                    st.markdown(f'<div style="display:flex;justify-content:flex-end;"><a href="{form_url}" target="_blank"><img src="data:image/png;base64,{img_b64}" class="survey-img-btn" style="width:100%;max-width:350px;border-radius:12px;border:2px solid #333;"></a></div>', unsafe_allow_html=True)
            else:
                st.link_button(label="📝 Submit Run Data", url=form_url, type="primary", width='stretch')
        else:
            st.info(current_config.get('status_msg'))
            
    st.link_button(label="☕ Support the Project", url='https://paypal.me/JgamersZuse', type="secondary", width='stretch')
    
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

    # --- GLOBAL CONTEXT & TRENDS (Consolidated from Resources) ---
    st.subheader("📈 Meta Trends & Health")
    
    t1, t2 = st.columns(2)
    
    with t1:
        # 1. Win Rate Trend
        if 'Round' in df.columns and 'Day' in df.columns:
            trend_df = team_df.groupby(['Round', 'Day']).agg({'Calculated_WinRate': 'mean'}).reset_index()
            trend_df['Session'] = trend_df['Round'] + " " + trend_df['Day']
            
            fig_trend = px.line(
                trend_df, x='Session', y='Calculated_WinRate', 
                title="Global Win Rate Trend (Difficulty)",
                markers=True, template='plotly_dark', text='Calculated_WinRate'
            )
            fig_trend.update_traces(textposition="top center", texttemplate='%{text:.1f}%')
            st.plotly_chart(style_fig(fig_trend, height=400), width='stretch', config=PLOT_CONFIG)
        else:
            st.info("No timeline data available.")

    with t2:
        # 2. Luck vs Grind
        grind_df = team_df[team_df['Clean_Races'] >= 5]
        fig_luck = px.scatter(
            grind_df, x='Clean_Races', y='Calculated_WinRate',
            color='Calculated_WinRate',
            title="Luck vs. Grind (Does playing more lower your WR?)",
            template='plotly_dark',
            labels={'Clean_Races': 'Races Played', 'Calculated_WinRate': 'Win Rate %'},
            color_continuous_scale='Twilight',
            trendline="ols"
        )
        st.plotly_chart(style_fig(fig_luck, height=400), width="stretch", config=PLOT_CONFIG)

    st.markdown("---")

    # --- DISTRIBUTIONS ---
    g1, g2 = st.columns(2)
    with g1:
        fig_dist = px.histogram(team_df, x="Calculated_WinRate", nbins=20, title="Win Rate Distribution", labels={'Calculated_WinRate': 'Win Rate %'})
        fig_dist.update_layout(bargap=0.1)
        st.plotly_chart(style_fig(fig_dist, height=350), width="stretch", config=PLOT_CONFIG)
    with g2:
        group_stats = team_df.groupby('Clean_Group')['Calculated_WinRate'].mean().reset_index()
        fig_group = px.bar(group_stats, x='Clean_Group', y='Calculated_WinRate', title="Difficulty by Group", color='Calculated_WinRate', color_continuous_scale='Redor')
        st.plotly_chart(style_fig(fig_group, height=350), width="stretch", config=PLOT_CONFIG)

    # --- LEADERBOARD ---
    st.subheader("👑 Top Performers")
    unique_sessions = df.drop_duplicates(subset=['Display_IGN', 'Round', 'Day'])
    stats_source = unique_sessions[unique_sessions['Display_IGN'] != "Anonymous Trainer"]
    
    leaderboard = stats_source.groupby('Display_IGN').agg({'Clean_Wins': 'sum', 'Clean_Races': 'sum'}).reset_index()
    leaderboard = leaderboard[(leaderboard['Clean_Races'] >= 15) & (leaderboard['Clean_Races'] <= 81)]
    leaderboard['Global_WinRate'] = (leaderboard['Clean_Wins'] / leaderboard['Clean_Races']) * 100
    leaderboard['Score'] = leaderboard.apply(lambda x: calculate_score(x['Clean_Wins'], x['Clean_Races']), axis=1)
    
    main_teams = team_df.groupby('Display_IGN')['Team_Comp'].agg(lambda x: x.mode()[0] if not x.mode().empty else "Various").reset_index()
    leaderboard = pd.merge(leaderboard, main_teams, on='Display_IGN', how='left').sort_values('Score', ascending=False).head(10).sort_values('Score', ascending=True)
    
    fig_leader = px.bar(
        leaderboard, x='Score', y='Display_IGN', orientation='h', 
        color='Global_WinRate', text='Clean_Wins', color_continuous_scale='Turbo',
        hover_data={'Team_Comp': True}
    )
    fig_leader.update_traces(texttemplate='Wins: %{text} | WR: %{marker.color:.1f}%', textposition='inside')
    st.plotly_chart(style_fig(fig_leader, height=600), width="stretch", config=PLOT_CONFIG)

    # --- MONEY ---
    st.subheader("💰 Spending Impact")
    team_df_sorted = team_df.sort_values('Sort_Money')
    fig_money = px.box(team_df_sorted, x='Original_Spent', y='Calculated_WinRate', color='Original_Spent')
    st.plotly_chart(style_fig(fig_money, height=500), width="stretch", config=PLOT_CONFIG)