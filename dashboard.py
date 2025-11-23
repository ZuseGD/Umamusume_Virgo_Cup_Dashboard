
import streamlit as st
import pandas as pd
import plotly.express as px
import re
import numpy as np

# --- CONFIGURATION ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTR8Pa4QQVSNwepSe9dYnro3ZaVEpYQmBdZUzumuLL-U2IR3nKVh-_GbZeJHT2x9aCqnp7P-0hPm5Zd/pub?gid=221070242&single=true&output=csv"

st.set_page_config(
    page_title="Virgo Cup CM5 Dashboard", 
    page_icon="🏆", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# --- DESCRIPTIONS & FOOTER ---
descriptions = {
    "leaderboard": """
    **How this is calculated:**
    - **Ranking Logic:** Trainers are ranked by a **Performance Score** which prioritizes Total Wins first, and Win Rate second.
    - **Formula:** `Score = Win Rate * log(Total Races + 1)`.
    - **Why?** A player with 19/20 wins (Score ≈ 289) ranks higher than a player with 1/1 wins (Score ≈ 69), ensuring the leaderboard rewards consistent performance over time.
    - **Filtering:** Trainers with fewer than 15 total races are excluded to ensure the leaderboard reflects consistent performance.
    - **Anonymization:** Only the Top 10 trainers are shown by name; all others are anonymized in the dataset.
    """,
    "money": """
    **How this is calculated:**
    - **Data Source:** Players self-report their total spending tier (e.g., F2P, $1-$100, $1000++).
    - **Metric:** The box plot shows the distribution of 'Win Rate' for all players within each spending tier.
    - **Interpretation:** The box represents the middle 50% of players (IQR). The line inside is the median win rate. Whiskers show the range of typical performance. Outliers are shown as individual points.
    - **Goal:** To visualize if higher spending correlates with higher win rates, or if F2P players remain competitive.
    """,
    "teams": """
    **How this is calculated:**
    - **Team Definition:** A unique combination of 3 Umas used by a single player in a single session (Round + Day).
    - **Filtering:** Only team compositions that appear at least 8 times in the dataset are shown to ensure statistical relevance.
    - **Metric:** The average win rate of all players using that specific trio of Umas.
    - **Goal:** To identify the "Meta" teams that consistently perform well across different trainers.
    """,
    "umas": """
    **How this is calculated:**
    - **Scope:** Evaluates each Uma individually, regardless of their teammates.
    - **Metric:** The average win rate of all teams that included this specific Uma.
    - **Filtering:** Umas with fewer than 10 recorded runs are excluded to prevent skewed data (e.g., 1 win / 1 run = 100%).
    - **Goal:** To produce a "Tier List" of individual character strength in the current meta.
    - **⚠️ Disclaimer:** This assumes the Uma contributed to the team's win rate. Individual race data is not available.
    """,
    "strategy": """
    **How this is calculated:**
    - **Standardization:** Running styles are mapped to 5 categories:
        - **Runaway:** Includes Escape strategies.
        - **Front Runner:** Includes Leader strategies.
        - **Pace Chaser:** Includes Betweener strategies.
        - **Late Surger:** Includes Oikomi strategies.
        - **End Closer:** Standard strategy.
    - **Metric:** The average win rate for Umas using that specific running style.
    - **Goal:** To see which running strategy is dominant on this specific track.
    """,
    "runaway": """
    **How this is calculated:**
    - **Definition:** A team is flagged as "With Runaway" if at least one Uma uses the 'Runaway' strategy. Note: 'Front Runner' is NOT considered a Runaway.
    - **Metric:** Compares the average win rate of teams that include a Runaway vs. teams that do not.
    - **Goal:** To test the hypothesis that having a Runaway is essential for controlling the race pace.
    """,
    "cards": """
    **How this is calculated:**
    - **Data Source:** Players report the status (Limit Break level) of specific key Support Cards (e.g., Kitasan Black).
    - **Metric:** The average win rate of players grouped by the Limit Break status of the selected card (e.g., MLB vs 0LB).
    - **Goal:** To measure the impact of "Meta" support cards on actual race performance.
    """,
    "trends": """
    **How this is calculated:**
    - **Grouping:** Data is aggregated by Round (1 or 2) and Day (1 or 2).
    - **Metric:** The average win rate of the entire player base for that specific session.
    - **Goal:** To observe how the competition difficulty evolves over time (e.g., does win rate drop in Round 2 as casual players are eliminated?).
    """
}

footer_html = """
<style>
.footer {
    position: fixed;
    left: 0;
    bottom: 0;
    width: 100%;
    background-color: #0E1117;
    color: #888;
    text-align: center;
    padding: 15px;
    font-size: 13px;
    border-top: 1px solid #333;
    z-index: 100;
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 20px;
}
.footer a {
    color: #00CC96; /* Accent Color */
    text-decoration: none;
    font-weight: bold;
}
.footer a:hover {
    text-decoration: underline;
    color: #FAFAFA;
}
</style>
<div class="footer">
    <span>Made by <b>Zuse</b> 🚀 | Virgo Cup Analytics</span>
    <span>
        👾 Discord: <b>@zusethegoose</b>
    </span>
    <span>
        <a href="https://github.com/ZuseGD" target="_blank">💻 GitHub</a>
    </span>
    <span>
        <a href="https://paypal.me/paypal.me/JgamersZuse" target="_blank">☕ Support (PayPal)</a>
    </span>
</div>
"""

# --- 1. HELPER FUNCTIONS ---
def find_column(df, keywords, case_sensitive=False):
    if df.empty: return None
    cols = df.columns.tolist()
    for col in cols:
        for key in keywords:
            if case_sensitive:
                if col == key: return col
            else:
                if col.lower() == key.lower(): return col
    clean_cols = df.columns.str.lower().str.replace(' ', '').str.replace('_', '').str.replace('-', '')
    for i, col in enumerate(clean_cols):
        for key in keywords:
            if key.lower() in col: return df.columns[i]
    return None

def clean_currency_numeric(series):
    return (series.astype(str)
            .str.replace('$', '', regex=False)
            .str.replace(',', '', regex=False)
            .str.replace(' ', '', regex=False)
            .str.replace('USD', '', regex=False)
            .str.replace('EUR', '', regex=False)
            .str.replace('++', '', regex=False)
            .str.replace('F2P', '0', regex=False)
            .str.split('-').str[0]
            .apply(pd.to_numeric, errors='coerce')
            .fillna(0))

def extract_races_count(series):
    def parse_races(text):
        text = str(text).lower()
        match = re.search(r'(\d+)\s*races', text)
        if match: return int(match.group(1))
        if text.isdigit(): return int(text)
        return 1 
    return series.apply(parse_races)

def parse_uma_details(series):
    return series.astype(str).apply(lambda x: x.split(' - ')[0].strip().title())

def calculate_score(wins, races):
    if races == 0: return 0
    wr = (wins / races) * 100
    return wr * np.log1p(races)

def anonymize_players(df, metric='Calculated_WinRate', top_n=10):
    player_stats = df.groupby('Clean_IGN').agg({
        metric: 'mean',
        'Clean_Wins': 'sum',
        'Clean_Races': 'sum'
    }).reset_index()
    player_stats['Score'] = player_stats.apply(lambda x: calculate_score(x['Clean_Wins'], x['Clean_Races']), axis=1)
    eligible_pros = player_stats[player_stats['Clean_Races'] >= 20]
    top_players = eligible_pros.sort_values('Score', ascending=False).head(top_n)['Clean_IGN'].tolist()
    df['Display_IGN'] = df['Clean_IGN'].apply(lambda x: x if x in top_players else "Anonymous Trainer")
    return df

# Chart Styler for Mobile/Readability + FIXED PANNING
def style_fig(fig):
    fig.update_layout(
        font=dict(size=14), # Larger text
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
        ),
        margin=dict(l=10, r=10, t=40, b=10),
        autosize=True
    )
    # Prevent panning (getting lost) on both axes
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig

# Common Config
PLOT_CONFIG = {
    'scrollZoom': False, 
    'displayModeBar': True,
    'displaylogo': False,
    'modeBarButtonsToRemove': ['sendDataToCloud', 'lasso2d', 'select2d', 'zoom2d', 'pan2d']
}

# --- 2. DATA LOADING ---
@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        col_map = {
            'ign': find_column(df, ['ign', 'player']),
            'group': find_column(df, ['cmgroup', 'bracket']),
            'money': find_column(df, ['spent', 'eur/usd']),
            'uma': find_column(df, ['uma']),
            'style': find_column(df, ['style', 'running']),
            'wins': find_column(df, ['wins', 'victory']),
            'races_text': find_column(df, ['races', 'attempts']),
            'Round': find_column(df, ['Round'], case_sensitive=True), 
            'Day': find_column(df, ['Day'], case_sensitive=True),
            'runs_per_day': find_column(df, ['runsperday', 'howmanyruns'])
        }

        if col_map['money']: 
            df['Original_Spent'] = df[col_map['money']].fillna("Unknown")
            df['Sort_Money'] = clean_currency_numeric(df[col_map['money']])
        else: 
            df['Original_Spent'] = "Unknown"
            df['Sort_Money'] = 0.0

        if col_map['uma']: df['Clean_Uma'] = parse_uma_details(df[col_map['uma']])
        else: df['Clean_Uma'] = "Unknown"

        if col_map['wins']: df['Clean_Wins'] = pd.to_numeric(df[col_map['wins']], errors='coerce').fillna(0)
        else: df['Clean_Wins'] = 0
        
        if col_map['races_text']: df['Clean_Races'] = extract_races_count(df[col_map['races_text']])
        else: df['Clean_Races'] = 1

        df['Calculated_WinRate'] = (df['Clean_Wins'] / df['Clean_Races']) * 100
        df.loc[df['Calculated_WinRate'] > 100, 'Calculated_WinRate'] = 100

        if col_map['group']: df['Clean_Group'] = df[col_map['group']].fillna("Unknown")
        else: df['Clean_Group'] = "Unknown"
        
        if col_map['ign']: df['Clean_IGN'] = df[col_map['ign']].fillna("Anonymous")
        else: df['Clean_IGN'] = "Anonymous"
        
        if col_map['style']: df['Clean_Style'] = df[col_map['style']].fillna("Unknown")
        else: df['Clean_Style'] = "Unknown"
        
        if col_map['Round']: df['Round'] = df[col_map['Round']].fillna("Unknown")
        else: df['Round'] = "Unknown"
        
        if col_map['Day']: df['Day'] = df[col_map['Day']].fillna("Unknown")
        else: df['Day'] = "Unknown"

        df = anonymize_players(df)
        
        # --- TEAM RECONSTRUCTION ---
        # Group by Session to rebuild Teams
        # Sorting Umas ensures [A, B, C] is same as [C, B, A]
        team_df = df.groupby(['Clean_IGN', 'Display_IGN', 'Clean_Group', 'Round', 'Day', 'Original_Spent', 'Sort_Money']).agg({
            'Clean_Uma': lambda x: sorted(list(x)), 
            'Clean_Style': lambda x: list(x),       
            'Calculated_WinRate': 'mean',           
            'Clean_Races': 'mean',
            'Clean_Wins': 'mean'
        }).reset_index()
        
        # Recalculate Score for Teams
        team_df['Score'] = team_df.apply(lambda x: calculate_score(x['Clean_Wins'], x['Clean_Races']), axis=1)

        team_df['Uma_Count'] = team_df['Clean_Uma'].apply(len)
        team_df = team_df[team_df['Uma_Count'] == 3]
        team_df['Team_Comp'] = team_df['Clean_Uma'].apply(lambda x: ", ".join(x))
        
        return df, team_df
    except Exception as e:
        st.error(f"Data Error: {e}")
        return pd.DataFrame(), pd.DataFrame()

# --- 3. APP LAYOUT ---
try:
    df, team_df = load_data()
except Exception as e:
    st.error(f"Data Load Failed: {e}")
    st.stop()

# --- NAVIGATION ---
page = st.radio("Navigation", ["🌍 Global Overview", "⚔️ Team & Meta", "🐴 Individual Umas", "🃏 Resources"], horizontal=True, label_visibility="collapsed")

if not df.empty:
    # Filter Team Comps
    comp_counts = team_df['Team_Comp'].value_counts()
    valid_comps = comp_counts[comp_counts > 7].index.tolist()
    filtered_team_df = team_df[team_df['Team_Comp'].isin(valid_comps)]

    # --- SIDEBAR ---
    st.sidebar.header("⚙️ Filters & Search")
    
    # GLOBAL FILTER
    groups = list(df['Clean_Group'].unique())
    selected = st.sidebar.multiselect("Filter Group", groups, default=groups)
    
    if selected:
        df = df[df['Clean_Group'].isin(selected)]
        # We must re-filter team_df based on the selected groups
        team_df = team_df[team_df['Clean_Group'].isin(selected)]
        filtered_team_df = team_df[team_df['Team_Comp'].isin(valid_comps)]

    # UMA INSPECTOR (SIDEBAR - Moved back to sidebar as per latest implied request about "removing" stuff from main)
    # Wait, user said "move the inspectors back to individual umas and trainer inspector instead of top performers"
    # So Trainer Inspector goes to HOME page (done), Uma Inspector goes to INDIVIDUAL UMAS page (will do).
    # Sidebar will keep Group Filter only.

    # --- PAGE 1: HOME (Global Overview) ---
    if page == "🌍 Global Overview":
        st.title("🏆 Virgo Cup Global Overview")
        
        # 1. TOP METRICS
        total_runs = team_df['Clean_Races'].sum()
        avg_wr = team_df['Calculated_WinRate'].mean()
        active_trainers = team_df['Clean_IGN'].nunique()
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Data Points", int(total_runs), help="Total individual races recorded")
        m2.metric("Global Avg Win Rate", f"{avg_wr:.1f}%", help="Average across all submissions")
        m3.metric("Active Trainers", int(active_trainers))
        
        st.markdown("---")
        
        # 2. LEADERBOARD
        st.subheader("👑 Top Performers")
        
        named_teams = team_df[team_df['Display_IGN'] != "Anonymous Trainer"].copy()
        leaderboard = named_teams.groupby(['Display_IGN', 'Team_Comp']).agg({'Clean_Wins': 'sum', 'Clean_Races': 'sum'}).reset_index()
        leaderboard['Global_WinRate'] = (leaderboard['Clean_Wins'] / leaderboard['Clean_Races']) * 100
        leaderboard['Score'] = leaderboard.apply(lambda x: calculate_score(x['Clean_Wins'], x['Clean_Races']), axis=1)
        leaderboard = leaderboard[leaderboard['Clean_Races'] >= 15]
        
        top_leaders = leaderboard.sort_values('Score', ascending=False).head(10)
        
        # TRAINER INSPECTOR (HOME PAGE)
        all_trainers = sorted(team_df['Clean_IGN'].unique()) 
        target_trainer = st.selectbox("🧑‍🏫 Find Trainer Stats:", [""] + all_trainers)
    
        if target_trainer:
            t_data = team_df[team_df['Clean_IGN'] == target_trainer]
            if not t_data.empty:
                t_wr = t_data['Calculated_WinRate'].mean()
                t_runs = t_data['Clean_Races'].sum()
                fav_team = t_data['Team_Comp'].mode()[0] if not t_data.empty else "N/A"
                t1, t2, t3 = st.columns(3)
                t1.metric("Trainer Win Rate", f"{t_wr:.1f}%")
                t2.metric("Total Runs", int(t_runs))
                t3.info(f"**Fav Team:** {fav_team}")
            else:
                st.warning("No data found for this trainer in selected group.")

        plot_data = top_leaders.sort_values('Score', ascending=True)
        plot_data['Label'] = plot_data['Display_IGN'] + " (" + plot_data['Team_Comp'] + ")"
        
        fig_leader = px.bar(
            plot_data, x='Score', y='Label', orientation='h', color='Global_WinRate',
            text='Clean_Wins', template='plotly_dark', color_continuous_scale='Turbo', height=600
        )
        fig_leader.update_traces(texttemplate='Wins: %{text} | WR: %{marker.color:.1f}%', textposition='inside')
        fig_leader.update_layout(xaxis_title="Performance Score", yaxis_title=None)
        st.plotly_chart(style_fig(fig_leader), width='stretch', config=PLOT_CONFIG)
        with st.expander("ℹ️ Leaderboard Logic"):
            st.markdown(descriptions["leaderboard"])

        st.markdown("---")

        # 3. SPENDING
        st.subheader("💰 Spending vs. Win Rate")
        team_df_sorted = team_df.sort_values('Sort_Money')
        fig_money = px.box(
            team_df_sorted, x='Original_Spent', y='Calculated_WinRate', color='Original_Spent',
            points="all", template='plotly_dark', color_discrete_sequence=px.colors.qualitative.Bold, height=600
        )
        fig_money.update_layout(showlegend=False, yaxis_title="Win Rate (%)", xaxis_title="Spending Tier")
        st.plotly_chart(style_fig(fig_money), width='stretch', config=PLOT_CONFIG)
        with st.expander("ℹ️ About this chart"):
            st.markdown(descriptions["money"])

    # --- PAGE 2: TEAM & META ---
    elif page == "⚔️ Team & Meta":
        st.title("⚔️ Team Composition & Meta Strategy")
        
        tab_meta1, tab_meta2, tab_meta3 = st.tabs(["Ideal Teams", "Running Style", "Runaway Impact"])
        
        with tab_meta1:
            st.subheader("🏆 Meta Team Compositions")
            if not filtered_team_df.empty:
                comp_stats = filtered_team_df.groupby('Team_Comp').agg({'Calculated_WinRate': 'mean', 'Clean_Races': 'count'}).reset_index().rename(columns={'Clean_Races': 'Usage Count'})
                fig_comps = px.bar(
                    comp_stats.sort_values('Calculated_WinRate', ascending=False).head(15),
                    x='Calculated_WinRate', y='Team_Comp', orientation='h', color='Calculated_WinRate',
                    color_continuous_scale='Plasma', text='Usage Count', title="Top Teams (>7 Entries)", template='plotly_dark', height=700
                )
                fig_comps.update_layout(yaxis={'categoryorder':'total ascending'}, xaxis_title="Avg Win Rate (%)", yaxis_title="Team Composition")
                fig_comps.update_traces(texttemplate='%{text} Entries', textposition='inside')
                st.plotly_chart(style_fig(fig_comps), width='stretch', config=PLOT_CONFIG)
                with st.expander("ℹ️ About this chart"):
                    st.markdown(descriptions["teams"])
            else:
                st.info("Not enough data to show Team Comps (>7 uses required).")

        with tab_meta2:
            st.subheader("🏃 Performance by Running Style")
            def standardize_style(style):
                s = str(style).lower().strip()
                if 'oonige' in s or 'escape' in s or 'runaway' in s: return 'Runaway'
                if 'runner' in s and 'front' not in s: return 'Runaway'
                
                if 'front' in s or 'leader' in s: return 'Front Runner'
                if 'pace' in s or 'betweener' in s: return 'Pace Chaser'
                if 'late' in s: return 'Late Surger'
                if 'end' in s or 'closer' in s: return 'End Closer'
                return 'Unknown'
            
            style_df = df.copy()
            style_df['Standard_Style'] = style_df['Clean_Style'].apply(standardize_style)
            style_stats = style_df.groupby('Standard_Style').agg({'Calculated_WinRate': 'mean', 'Clean_Races': 'count'}).reset_index()
            style_stats = style_stats[(style_stats['Clean_Races'] > 20) & (style_stats['Standard_Style'] != 'Unknown')]
            desired_order = ['Runaway', 'Front Runner', 'Pace Chaser', 'Late Surger', 'End Closer']
            
            fig_style = px.bar(
                style_stats, x='Calculated_WinRate', y='Standard_Style', orientation='h', color='Calculated_WinRate',
                template='plotly_dark', title="Win Rate by Running Style", text='Calculated_WinRate', color_continuous_scale='Viridis', height=500
            )
            fig_style.update_layout(yaxis={'categoryorder':'array', 'categoryarray': desired_order[::-1]}, xaxis_title="Avg Win Rate (%)", yaxis_title=None)
            fig_style.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            st.plotly_chart(style_fig(fig_style), width='stretch', config=PLOT_CONFIG)
            with st.expander("ℹ️ About this chart"):
                st.markdown(descriptions["strategy"])

        with tab_meta3:
            st.subheader("⚠️ Impact of Runaways")
            def check_for_runaway(style_list):
                target_terms = ['Runaway', 'Runner', 'Escape', 'Oonige', 'Great Escape']
                for s in style_list:
                    s_clean = str(s).strip()
                    s_lower = s_clean.lower()
                    if any(t.lower() in s_lower for t in target_terms):
                        if "front" in s_lower: continue 
                        return True
                return False
            
            team_df['Has_Runaway'] = team_df['Clean_Style'].apply(check_for_runaway)
            runner_stats = team_df.groupby('Has_Runaway')['Calculated_WinRate'].mean().reset_index()
            runner_stats['Strategy'] = runner_stats['Has_Runaway'].map({True: 'With Runaway', False: 'No Runaway'})
            
            fig_runner = px.bar(
                runner_stats, x='Strategy', y='Calculated_WinRate', color='Strategy',
                template='plotly_dark', text='Calculated_WinRate',
                color_discrete_sequence=['#00CC96', '#EF553B'], height=500
            )
            fig_runner.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            st.plotly_chart(style_fig(fig_runner), width='stretch', config=PLOT_CONFIG)
            with st.expander("ℹ️ About this chart"):
                st.markdown(descriptions["runaway"])

    # --- PAGE 3: INDIVIDUAL UMAS ---
    elif page == "🐴 Individual Umas":
        st.title("🐴 Individual Uma Performance")
        st.warning("⚠️ **NOTE:** Win Rates are based on **TEAM Performance** when this Uma is present. It does NOT track individual race wins.")
        
        # UMA INSPECTOR (Moved to this page)
        st.subheader("🔍 Uma Inspector")
        all_umas = sorted(df['Clean_Uma'].unique())
        target_uma = st.selectbox("Select Uma:", [""] + all_umas)

        if target_uma:
            uma_data = df[df['Clean_Uma'] == target_uma]
            avg_wr = uma_data['Calculated_WinRate'].mean()
            unique_players = uma_data['Clean_IGN'].nunique()
            strat_stats = uma_data.groupby('Clean_Style')['Calculated_WinRate'].agg(['mean', 'count'])
            valid_strats = strat_stats[strat_stats['count'] > 3]
            if valid_strats.empty: valid_strats = strat_stats
            best_strat = valid_strats['mean'].idxmax() if not valid_strats.empty else "N/A"
            
            st.caption(f"Stats for **{target_uma}**")
            c1, c2 = st.columns(2)
            c1.metric("Win Rate", f"{avg_wr:.1f}%")
            c2.metric("Unique Players", int(unique_players))
            st.metric("Best Strategy", best_strat)
            
            # Drilldown Chart
            fig_drill = px.bar(strat_stats, x='mean', y=strat_stats.index, orientation='h', title=f"Strategy Breakdown for {target_uma}", template='plotly_dark', height=400)
            st.plotly_chart(style_fig(fig_drill), width='stretch', config=PLOT_CONFIG)

        st.markdown("---")
        
        st.subheader("📊 Uma Tier List")
        uma_stats = df.groupby('Clean_Uma').agg({'Calculated_WinRate': 'mean', 'Clean_Races': 'count'}).reset_index()
        uma_stats = uma_stats[uma_stats['Clean_Races'] >= 10]
        
        fig_uma = px.bar(
            uma_stats.sort_values('Calculated_WinRate', ascending=False).head(15), 
            x='Calculated_WinRate', 
            y='Clean_Uma', 
            orientation='h', 
            color='Calculated_WinRate', 
            color_continuous_scale='Viridis', 
            text='Clean_Races', 
            template='plotly_dark', 
            height=700
        )
        fig_uma.update_layout(yaxis={'categoryorder':'total ascending'}, xaxis_title="Avg Win Rate (%)", yaxis_title="Character")
        fig_uma.update_traces(texttemplate='WR: %{x:.1f}% | Runs: %{text}', textposition='inside')
        st.plotly_chart(style_fig(fig_uma), width='stretch', config=PLOT_CONFIG)
        with st.expander("ℹ️ About this chart"):
            st.markdown(descriptions["umas"])

    # --- PAGE 4: RESOURCES ---
    elif page == "🃏 Resources":
        st.title("🃏 Resource Analysis")
        
        st.subheader("Support Card Impact")
        card_map = {}
        for c in df.columns:
            if "Card Status" in c:
                card_name = c.split('[')[-1].replace(']', '').strip()
                card_map[card_name] = c
                
        if card_map:
            target_name = st.selectbox("Select Card", sorted(list(card_map.keys())))
            col_match = card_map[target_name]
            
            # Use FILTERED df here to respect sidebar group selection
            card_stats = df.drop_duplicates(subset=['Clean_IGN', 'Round', 'Day']).groupby(col_match)['Calculated_WinRate'].mean().reset_index()
            fig_card = px.bar(
                card_stats, x=col_match, y='Calculated_WinRate', color='Calculated_WinRate',
                color_continuous_scale='Bluered', template='plotly_dark', title=f"Win Rate by {target_name} Status",
                text='Calculated_WinRate', height=600
            )
            fig_card.update_traces(texttemplate='%{text:.1f}%', textposition='inside')
            fig_card.update_layout(xaxis_title="Limit Break Status")
            st.plotly_chart(style_fig(fig_card), width='stretch', config=PLOT_CONFIG)
            with st.expander("ℹ️ About this chart"):
                st.markdown(descriptions["cards"])
        else:
            st.warning("No Card Data found.")

        st.subheader("Meta Trends (Round 1 vs Round 2)")
        if 'Round' in df.columns and 'Day' in df.columns:
            trend_df = team_df.groupby(['Round', 'Day']).agg({'Calculated_WinRate': 'mean', 'Clean_Races': 'count'}).reset_index()
            trend_df['Session'] = trend_df['Round'] + " " + trend_df['Day']
            
            fig_trend = px.line(
                trend_df, x='Session', y='Calculated_WinRate', title="Global Win Rate Trend",
                markers=True, template='plotly_dark', text='Calculated_WinRate', height=600
            )
            fig_trend.update_traces(textposition="top center", texttemplate='%{text:.1f}%')
            st.plotly_chart(style_fig(fig_trend), width='stretch', config=PLOT_CONFIG)
            with st.expander("ℹ️ About this chart"):
                st.markdown(descriptions["trends"])

# --- FOOTER ---
st.markdown(footer_html, unsafe_allow_html=True)
