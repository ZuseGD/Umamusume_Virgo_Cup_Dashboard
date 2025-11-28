import streamlit as st
import plotly.express as px
import pandas as pd
import os
import base64
from virgo_utils import style_fig, PLOT_CONFIG, calculate_score, show_description

def get_base64_image(image_path):
    """Helper to convert image to base64 for HTML embedding"""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except:
        return None

def show_view(df, team_df, current_config):
    
    # --- CSS: Make Support Button Fill Vertical Space ---
    st.markdown("""
    <style>
        /* Force the container of the link button to take full height */
        div[data-testid="stLinkButton"] {
            height: 100%;
            min-height: 50px; /* Ensure it has some substance */
        }
        /* Style the actual 'a' tag button to stretch */
        div[data-testid="stLinkButton"] > a {
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 1.1rem;
        }
    </style>
    """, unsafe_allow_html=True)

    

    # --- TOP LAYOUT (Header Left | Button Right) ---
    col_header, col_btn = st.columns([1, 1], gap="medium")

    # --- LEFT SIDE: HEADER & UPDATES ---
    with col_header:
        
        # Update Notice
        with st.expander("✨ What's New: The Finals Update", expanded=True):
            st.markdown("""
        **Patch Notes: Virgo Cup Finals Analysis 🏆**

        We have added a dedicated **Finals** tab to analyze what *actually* won the A-Finals.

        📊 **Meta Overview:**
        - **Meta Score vs. Win Rate:** A new scatter plot identifying the "True Meta" characters that combine high usage with high win rates.
        
        ⚔️ **Team Efficiency:**
        - **Win/Entry Ratio:** Instead of just popularity, see which Team Comps had the highest efficiency in securing 1st place.
        
        ⚡ **Skill Lift (The "Secret Sauce"):**
        - Comparing **Finals Winners** vs. the **Prelims Baseline**.
        - Identifies skills that winners prioritize significantly more than the general population.
        
        🏆 **Champion Stats:**
        - A benchmark comparing the stat spread of **1st Place Winners** vs. Non-Winners.
        """)
        
        

    # --- RIGHT SIDE: SURVEY BUTTON ---
    with col_btn:
        form_url = current_config.get('form_url')
        banner_path = "images/survey_banner.png"

        if form_url:
            if os.path.exists(banner_path):
                img_b64 = get_base64_image(banner_path)
                if img_b64:
                    st.markdown(
                        f"""
                        <div style="display: flex; justify-content: flex-end; height: 100%;">
                            <a href="{form_url}" target="_blank" style="width: 100%;">
                                <img src="data:image/png;base64,{img_b64}" class="survey-img-btn">
                            </a>
                        </div>
                        <style>
                            .survey-img-btn {{
                                width: 100%;
                                max-width: 350px;
                                height: auto;
                                border-radius: 12px;
                                transition: transform 0.2s, box-shadow 0.2s;
                                border: 2px solid #333;
                                margin-bottom: 10px;
                            }}
                            .survey-img-btn:hover {{
                                transform: translateY(-3px);
                                box-shadow: 0 4px 20px rgba(0, 204, 150, 0.4);
                                border-color: #00CC96;
                            }}
                        </style>
                        """,
                        unsafe_allow_html=True
                    )
            else:
                st.link_button(
                    label="📝 Submit Run Data (Google Form)", 
                    url=form_url, 
                    type="primary", 
                    width='stretch'                )
        else:
            st.info(current_config.get('status_msg'))
            
    # Support Button (Now fills vertical space)
    st.link_button(
                label="☕ Support the Project", 
                url='https://paypal.me/JgamersZuse', 
                type="secondary",
                width='stretch'
            )
        
    st.warning("Only the Finals tab includes finals data, every other section is **ONLY THE ROUNDS DATA**")
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
            #template='plotly_dark',
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
            #template='plotly_dark',
            color='Calculated_WinRate',
            color_continuous_scale='Redor'
        )
        fig_group.update_layout(showlegend=False, yaxis_title="Avg Win Rate (%)", xaxis_title=None)
        st.plotly_chart(style_fig(fig_group, height=400), width="stretch", config=PLOT_CONFIG)
        show_description("group_diff")

    # LEADERBOARD
    st.subheader("👑 Top Performers")
    
    # 1. DEDUPLICATE SESSIONS (Fixes the 273 wins issue)
    # We only want to count each "Entry" once, not 3 times (once per Uma)
    # A unique session is defined by: Trainer + Round + Day
    # This prevents the triple-counting bug.
    unique_sessions = df.drop_duplicates(subset=['Display_IGN', 'Round', 'Day'])
    
    # 2. FILTER & AGGREGATE
    stats_source = unique_sessions[unique_sessions['Display_IGN'] != "Anonymous Trainer"]
    
    leaderboard = stats_source.groupby('Display_IGN').agg({
        'Clean_Wins': 'sum', 
        'Clean_Races': 'sum'
    }).reset_index()

    # SORT & FILTER
    # Added filter: Total Races <= 81 to remove anomalies
    leaderboard = leaderboard[
        (leaderboard['Clean_Races'] >= 15) & 
        (leaderboard['Clean_Races'] <= 81)
    ]
    
    # 3. CALCULATE SCORES
    leaderboard['Global_WinRate'] = (leaderboard['Clean_Wins'] / leaderboard['Clean_Races']) * 100
    leaderboard['Score'] = leaderboard.apply(lambda x: calculate_score(x['Clean_Wins'], x['Clean_Races']), axis=1)
    
    # 4. FETCH MAIN TEAM (Look up from team_df)
    # We merge the team name from team_df just for the label
    main_teams = team_df.groupby('Display_IGN')['Team_Comp'].agg(
        lambda x: x.mode()[0] if not x.mode().empty else "Various"
    ).reset_index()
    
    leaderboard = pd.merge(leaderboard, main_teams, on='Display_IGN', how='left')
    leaderboard['Team_Comp'] = leaderboard['Team_Comp'].fillna("Unknown Team")
    
    
    
    top_leaders = leaderboard.sort_values('Score', ascending=False).head(10)
    top_leaders = top_leaders.sort_values('Score', ascending=True) 
    
    # 6. CHART
    fig_leader = px.bar(
        top_leaders, 
        x='Score', 
        y='Display_IGN', 
        orientation='h', 
        color='Global_WinRate',
        text='Clean_Wins', 
        #template='plotly_dark', 
        color_continuous_scale='Turbo', 
        height=700,
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
        points="all", #template='plotly_dark', color_discrete_sequence=px.colors.qualitative.Bold, height=600
    )
    fig_money.update_layout(showlegend=False, yaxis_title="Win Rate (%)", xaxis_title="Spending Tier")
    st.plotly_chart(style_fig(fig_money, height=600), width="stretch", config=PLOT_CONFIG)
    show_description("money")