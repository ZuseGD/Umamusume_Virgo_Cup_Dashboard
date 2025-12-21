import streamlit as st
import plotly.express as px
import pandas as pd
import os
import base64
from uma_utils import style_fig, PLOT_CONFIG, calculate_score, show_description

def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except:
        return None

def show_view(df, team_df, current_config):
    st.set_page_config(page_title="Moomamusume Dashboard", layout="wide")
    
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
        with st.expander("🚀 Dashboard Update: Libra Cup & Finals Analysis Overhaul", expanded=True):
            st.markdown("""
           
**Version 2.0 - The "Analysis" Update**

We've completely reworked how you view Finals data! The old "OCR" and "Finals" tabs have been merged into a single, powerful **Analysis** section. This update brings robust support for the **Libra Cup** data format, smarter filtering, and a brand-new Hall of Records.

---

### ✨ New Features

#### 🏆 Unified Analysis Hub
* **Consolidated View:** Access all Finals insights in one place. No more switching between tabs for OCR builds and Match results.
* **Champion Profiles:** Select any specific Uma from the sidebar to see her personal "Profile":
    * **Radar Chart:** Compare her stats directly against the global average winner (with Speed correctly oriented at the top!).
    * **Winning Decks:** See the top support cards used by winners of that specific character.
    * **Skill Frequency:** View the most common skills equipped on winning runs.

#### 💎 Hall of Records
* **Superlatives:** Automatically detects standout performances:
    * **⚡ Fastest Time:** Who ran the absolute fastest winning race?
    * **📉 Minimalist:** Who won with the *least* amount of skills? (Now shows the exact skill list!)
    * **🐕 Underdog:** Who won with the lowest total stats?
    * **🦄 Niche Picks:** Highlights rare champions and off-meta strategies (e.g., a winning "Runaway" Gold Ship).
* **Custom Cards:** Data is presented in beautiful, dark-mode friendly cards so you don't have to click dropdowns to see the details.

#### 👑 Meta Impact Tier List
* **Interactive Scatter Plot:** Visualizes the entire meta in one chart.
* **Pick Rate vs. Win Rate:** Easily spot the "Meta Kings" (High Pick/High Win), "Sleepers" (Low Pick/High Win), and "Bait" (High Pick/Low Win).

---

            """)

    with col_btn:
        form_url = current_config.get('form_url')
        banner_path = "images/survey_banner.png"
        if form_url:
            # if os.path.exists(banner_path):
                # img_b64 = get_base64_image(banner_path)
                # if img_b64:
                    # st.markdown(f'<div style="display:flex;justify-content:flex-end;"><a href="{form_url}" target="_blank"><img src="data:image/png;base64,{img_b64}" class="survey-img-btn" style="width:100%;max-width:350px;border-radius:12px;border:2px solid #333;"></a></div>', unsafe_allow_html=True)
            # else:
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

    '''
    # --- GLOBAL CONTEXT & TRENDS (Consolidated from Resources) ---
    st.subheader("📈 Meta Trends & Health")

    # --- 1. PREPARE DATA ---
    # Group by Round/Day/Style and count entries
    daily_style = df.groupby(['Round', 'Day', 'Clean_Style']).size().reset_index(name='Count')

    # Create a 'Session' column for the X-Axis (e.g., "Round 1 - Day 1")
    daily_style['Session'] = daily_style['Round'].astype(str) + " - " + daily_style['Day'].astype(str)

    # Calculate Percentage (Meta Share) per Session
    daily_totals = daily_style.groupby('Session')['Count'].transform('sum')
    daily_style['Percentage'] = (daily_style['Count'] / daily_totals) * 100

    # --- 2. PLOT STACKED BAR CHART ---
    fig_stack_style = px.bar(
        daily_style, 
        x='Clean_Style', 
        y='Percentage', 
        color='Session', # <--- This creates the stacks
        title="Daily Strategy Meta Breakdown (Stacked)",
        text='Percentage',
        template='plotly_dark',
        labels={'Clean_Style': 'Strategy Style', 'Percentage': 'Meta Share (%)', 'Session': 'Tournament Session'},
        barmode='group'
    )

    # Format the text to show 1 decimal place
    fig_stack_style.update_traces(texttemplate='%{text:.1f}%', textposition='inside')
    fig_stack_style.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')

    st.plotly_chart(style_fig(fig_stack_style, height=500), width="stretch", config=PLOT_CONFIG)

    # --- 1. FILTER TOP CHARACTERS ---
    # Get the names of the Top 10 most used Umas globally
    top_umas = df['Clean_Uma'].value_counts().head(10).index.tolist()
    filtered_df = df[df['Clean_Uma'].isin(top_umas)]

    # --- 2. PREPARE DATA ---
    daily_uma = filtered_df.groupby(['Round', 'Day', 'Clean_Uma']).size().reset_index(name='Count')
    daily_uma['Session'] = daily_uma['Round'].astype(str) + " - " + daily_uma['Day'].astype(str)

    # --- 3. PLOT STACKED BAR CHART ---
    fig_stack_uma = px.bar(
        daily_uma, 
        x='Session', 
        y='Count', 
        color='Clean_Uma', # <--- Stacks by Character Name
        title="Top 10 Umas: Daily Usage Volume",
        template='plotly_dark',
        barmode='group',
        labels={'Session': 'Tournament Session', 'Count': 'Usage Count', 'Clean_Uma': 'Uma Name'},
        text='Count' # Show the raw count inside the bar
    )

    fig_stack_uma.update_traces(textposition='inside')

    st.plotly_chart(style_fig(fig_stack_uma, height=500), width="stretch", config=PLOT_CONFIG)
    '''
    
    t1, t2 = st.columns(2)
    
    with t1:
        # 1. Win Rate Trend
        if 'Round' in df.columns and 'Day' in df.columns:
            trend_df = team_df.groupby(['Round', 'Day']).agg({'Calculated_WinRate': 'mean'}).reset_index()
            trend_df['Session'] = trend_df['Round'] + " " + trend_df['Day']
            wr_order = ["R1 D1", "R1 D2", "R2 D1", "R2 D2"]

            fig_trend = px.line(
                trend_df, x='Session', y='Calculated_WinRate', 
                category_orders={'Session': wr_order},
                title="Global Win Rate Trend (Difficulty)",
                markers=True, template='plotly_dark', text='Calculated_WinRate',
               
                labels={'Calculated_WinRate': 'Avg Win Rate %', 'Session': 'Tournament Session'}
            )
            
            fig_trend.update_traces(textposition="top center", texttemplate='%{text:.1f}%', hovertemplate='Session: %{x}<br>Avg WR: %{y:.3f}%<extra></extra>')
            
            st.plotly_chart(style_fig(fig_trend, height=400), width='stretch',  config=PLOT_CONFIG)
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
        # UPDATED: Aggregate both Win Rate (Mean) and Races (Sum)
        group_stats = team_df.groupby('Clean_Group').agg({
            'Calculated_WinRate': 'mean', 
            'Clean_Races': 'sum'
        }).reset_index()

        fig_group = px.bar(
            group_stats, 
            x='Clean_Group', 
            y='Calculated_WinRate', 
            title="Difficulty by Group", 
            color='Calculated_WinRate', 
            color_continuous_scale='Redor',
            text='Clean_Races',  # <--- Bind text to Race Count
            labels={'Clean_Races': 'Races Played', 'Calculated_WinRate': 'Win Rate %', 'Clean_Group': 'Group'}
            
        )
        
        # Display the race count inside the bar
        fig_group.update_traces(texttemplate='%{text} Races', hovertemplate='%{text} Races', textposition='inside')
        
        st.plotly_chart(style_fig(fig_group, height=350), width="stretch", config=PLOT_CONFIG)
    # --- LEADERBOARD ---
    st.subheader("👑 Top Performers")
    st.warning("We are aware of an issue where some duplicate igns cause leaderboard inaccuracies. A fix is in progress.")
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
        hover_data={'Team_Comp': True},
        labels={'Score': 'Performance Score', 'Display_IGN': 'Trainer', 'Global_WinRate': 'Win Rate %', 'Clean_Wins': 'Wins'},
    )
    fig_leader.update_traces(texttemplate='Wins: %{text} | WR: %{marker.color:.1f}%', textposition='inside')
    st.plotly_chart(style_fig(fig_leader, height=600), width="stretch", config=PLOT_CONFIG)

    # --- MONEY ---
    st.subheader("💰 Spending Impact")
    team_df_sorted = team_df.sort_values('Sort_Money')

   # Comprehensive Mapping to cover both Virgo and Libra variations
    spending_map = {
        'F2P': 'F2P',
        '0' : 'F2P',
        '$0': 'F2P',
        
        '$1-100' : 'Salmon ($1-$100)',
        '$1-$100': 'Salmon ($1-$100)',
        
        '$101-500': 'Bluefin Tuna ($101-$500)',
        
        '$501-1000': 'Dolphin ($501-$1000)',
        
        '$1000++': 'Whale ($1000+)',
        '$1001-5000': 'Whale ($1000+)',
        '$5000+': 'Whale ($1000+)',
        
        '$10000+++ (Pirkui)': 'Pirkui ($10000+)',
        
        'Rather not say': 'Rather not say'
    }

    team_df_sorted['Original_Spent'] = team_df_sorted['Original_Spent'].map(spending_map)

    # Define the ideal order
    ideal_order = [
        'F2P', 
        'Salmon ($1-$100)', 
        'Bluefin Tuna ($101-$500)', 
        'Dolphin ($501-$1000)', 
        'Whale ($1000+)', 
        'Pirkui ($10000+)', 
        'Rather not say'
    ]
    
    # FILTER: Create dynamic order based on what actually exists in the data
    # This removes empty columns (like Pirkui in Libra) from the plot
    existing_tiers = set(team_df_sorted['Original_Spent'].unique())
    final_order = [tier for tier in ideal_order if tier in existing_tiers]

    fig_money = px.box(team_df_sorted, x='Original_Spent', y='Calculated_WinRate', color='Original_Spent', category_orders={'Original_Spent': final_order}, labels={'Original_Spent': 'Spending Tier', 'Calculated_WinRate': 'Win Rate %'}, title="Win Rate by Spending Tier", template='plotly_dark')
    st.plotly_chart(style_fig(fig_money, height=500), width="stretch", config=PLOT_CONFIG)