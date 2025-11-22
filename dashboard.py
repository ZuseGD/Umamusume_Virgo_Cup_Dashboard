
import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURATION ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTR8Pa4QQVSNwepSe9dYnro3ZaVEpYQmBdZUzumuLL-U2IR3nKVh-_GbZeJHT2x9aCqnp7P-0hPm5Zd/pub?gid=221070242&single=true&output=csv"

st.set_page_config(page_title="Virgo Cup CM5 Dashboard", page_icon="🏆", layout="wide")

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

def anonymize_players(df, metric='Calculated_WinRate', top_n=10):
    player_stats = df.groupby('Clean_IGN').agg({
        metric: 'mean',
        'Clean_Wins': 'sum',
        'Clean_Races': 'sum'
    }).reset_index()
    eligible_pros = player_stats[player_stats['Clean_Races'] >= 20]
    top_players = eligible_pros.sort_values(['Clean_Wins', metric], ascending=[False, False]).head(top_n)['Clean_IGN'].tolist()
    df['Display_IGN'] = df['Clean_IGN'].apply(lambda x: x if x in top_players else "Anonymous Trainer")
    return df

# --- 2. DATA LOADING ---
@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        
        # Map Core Columns
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

        # Clean Basic Data
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

        # Win Rate Calc
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
        team_df = df.groupby(['Clean_IGN', 'Display_IGN', 'Clean_Group', 'Round', 'Day', 'Original_Spent', 'Sort_Money']).agg({
            'Clean_Uma': lambda x: sorted(list(x)), 
            'Clean_Style': lambda x: list(x),       
            'Calculated_WinRate': 'mean',           
            'Clean_Races': 'mean',
            'Clean_Wins': 'mean'
        }).reset_index()

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
    st.error(f"Failed to load data: {e}")
    st.stop()

st.title("🏆 Virgo Cup CM5 Analytics")

if not df.empty:
    # Filter Team Comps
    comp_counts = team_df['Team_Comp'].value_counts()
    valid_comps = comp_counts[comp_counts > 7].index.tolist()
    filtered_team_df = team_df[team_df['Team_Comp'].isin(valid_comps)]

    # Sidebar
    groups = list(df['Clean_Group'].unique())
    selected = st.sidebar.multiselect("Filter Group", groups, default=groups)
    
    if selected:
        # Note: Deep filtering logic can be added here if needed
        pass

    # Tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Money & Meta", "Uma Tier List", "Strategy", "Card Impact", "Leaderboard", "Trends"])

    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Spending vs Win Rate")
            team_df_sorted = team_df.sort_values('Sort_Money')
            fig_money = px.box(
                team_df_sorted, 
                x='Original_Spent', 
                y='Calculated_WinRate', 
                color='Original_Spent', 
                points="all", 
                title="Distribution of Win Rates", 
                template='plotly_dark', 
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            fig_money.update_layout(showlegend=False)
            st.plotly_chart(fig_money, width='stretch')
            
        with c2:
            st.subheader("Ideal Team Compositions")
            if not filtered_team_df.empty:
                comp_stats = filtered_team_df.groupby('Team_Comp').agg({
                    'Calculated_WinRate': 'mean', 
                    'Clean_Races': 'count'
                }).reset_index().rename(columns={'Clean_Races': 'Usage Count'})
                
                fig_comps = px.bar(
                    comp_stats.sort_values('Calculated_WinRate', ascending=False).head(15), 
                    x='Calculated_WinRate', 
                    y='Team_Comp', 
                    orientation='h', 
                    color='Calculated_WinRate', 
                    color_continuous_scale='Plasma', 
                    text='Usage Count', 
                    title="Top Teams (>7 Entries)", 
                    template='plotly_dark'
                )
                fig_comps.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_comps, width='stretch')
            else:
                st.info("Not enough data to show Team Comps (>7 uses required).")

    with tab2:
        st.subheader("Individual Uma Tier List")
        st.caption("Performance of individual Umas regardless of team composition (Min. 10 runs).")
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
            title="Top 15 Umas by Win Rate"
        )
        fig_uma.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_uma, width='stretch')

    with tab3:
        st.subheader("Strategy Analysis")
        c1, c2 = st.columns(2)
        with c1:
            def standardize_style(style):
                s = str(style).lower().strip()
                if 'front' in s or 'leader' in s: return 'Front Runner'
                if 'pace' in s or 'betweener' in s: return 'Pace Chaser'
                if 'late' in s: return 'Late Surger'
                if 'end' in s or 'closer' in s: return 'End Closer'
                if 'run' in s or 'escape' in s or 'oonige' in s: return 'Runaway'
                return 'Unknown'
            
            style_df = df.copy()
            style_df['Standard_Style'] = style_df['Clean_Style'].apply(standardize_style)
            style_stats = style_df.groupby('Standard_Style').agg({'Calculated_WinRate': 'mean', 'Clean_Races': 'count'}).reset_index()
            style_stats = style_stats[(style_stats['Clean_Races'] > 20) & (style_stats['Standard_Style'] != 'Unknown')]
            desired_order = ['Runaway', 'Front Runner', 'Pace Chaser', 'Late Surger', 'End Closer']
            
            fig_style = px.bar(
                style_stats, 
                x='Calculated_WinRate', 
                y='Standard_Style', 
                orientation='h', 
                color='Calculated_WinRate', 
                template='plotly_dark', 
                title="Win Rate by Running Style", 
                text='Calculated_WinRate', 
                color_continuous_scale='Viridis'
            )
            fig_style.update_layout(yaxis={'categoryorder':'array', 'categoryarray': desired_order[::-1]})
            fig_style.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            st.plotly_chart(fig_style, width='stretch')
        
        with c2:
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
            runner_stats['Strategy'] = runner_stats['Has_Runaway'].map({True: 'With Runaway (Nigeru)', False: 'No Runaway'})
            
            fig_runner = px.bar(
                runner_stats, 
                x='Strategy', 
                y='Calculated_WinRate', 
                color='Strategy', 
                template='plotly_dark', 
                title="Impact of having a Runaway (Nigeru)", 
                color_discrete_sequence=['#00CC96', '#EF553B']
            )
            fig_runner.update_traces(texttemplate='%{y:.1f}%', textposition='auto')
            st.plotly_chart(fig_runner, width='stretch')

    with tab4:
        st.subheader("Support Card Impact")
        targets = ['Fine Motion', 'SSR Riko', 'SR Riko', 'Kitasan']
        target = st.selectbox("Select Card", targets)
        col_match = next((c for c in df.columns if target.lower() in c.lower() and "Card Status" in c), None)
        if col_match:
            card_stats = df.drop_duplicates(subset=['Clean_IGN', 'Round', 'Day']).groupby(col_match)['Calculated_WinRate'].mean().reset_index()
            fig_card = px.bar(
                card_stats, 
                x=col_match, 
                y='Calculated_WinRate', 
                color='Calculated_WinRate', 
                color_continuous_scale='Bluered', 
                template='plotly_dark', 
                title=f"Win Rate by {target} Status"
            )
            st.plotly_chart(fig_card, width='stretch')

    with tab5:
        st.subheader("Trainer Leaderboard")
        st.caption("Top 10 Trainers (All-Time). Sorted by Total Wins (Min. 15 Races).")
        named_teams = team_df[team_df['Display_IGN'] != "Anonymous Trainer"].copy()
        leaderboard = named_teams.groupby(['Display_IGN', 'Team_Comp']).agg({'Clean_Wins': 'sum', 'Clean_Races': 'sum'}).reset_index()
        leaderboard['Global_WinRate'] = (leaderboard['Clean_Wins'] / leaderboard['Clean_Races']) * 100
        leaderboard = leaderboard[leaderboard['Clean_Races'] >= 15]
        top_leaders = leaderboard.sort_values(['Clean_Wins', 'Global_WinRate'], ascending=[False, False]).head(10)
        top_leaders['Label'] = top_leaders['Display_IGN'] + " (" + top_leaders['Team_Comp'] + ")"
        
        fig_leader = px.bar(
            top_leaders, 
            x='Global_WinRate', 
            y='Label', 
            orientation='h', 
            color='Global_WinRate', 
            title="Top 10 Trainers", 
            text='Clean_Wins', 
            labels={'Global_WinRate': 'Win Rate (%)', 'Label': '', 'Clean_Wins': 'Total Wins'}, 
            template='plotly_dark', 
            color_continuous_scale='Turbo'
        )
        st.plotly_chart(fig_leader, width='stretch')
        
    with tab6:
        st.subheader("Meta Trends")
        if 'Round' in df.columns and 'Day' in df.columns:
            trend_df = team_df.groupby(['Round', 'Day']).agg({'Calculated_WinRate': 'mean', 'Clean_Races': 'count'}).reset_index()
            trend_df['Session'] = trend_df['Round'] + " " + trend_df['Day']
            
            fig_trend = px.line(
                trend_df, 
                x='Session', 
                y='Calculated_WinRate', 
                title="Average Win Rate by Session (Meta Evolution)", 
                markers=True, 
                template='plotly_dark'
            )
            st.plotly_chart(fig_trend, width='stretch')
