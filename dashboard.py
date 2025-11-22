
import streamlit as st
import pandas as pd
import plotly.express as px
import re

# --- CONFIGURATION ---
SHEET_URL = "CM Data Collection - Virgo Cup (Responses) - exploded_all.csv"

st.set_page_config(page_title="Virgo Cup CM5 Dashboard", page_icon="🏆", layout="wide")

# --- HELPER FUNCTIONS ---
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
    return (series.astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False).str.replace(' ', '', regex=False).str.replace('USD', '', regex=False).str.replace('EUR', '', regex=False).str.replace('++', '', regex=False).str.replace('F2P', '0', regex=False).str.split('-').str[0].apply(pd.to_numeric, errors='coerce').fillna(0))

def extract_races_count(series):
    def parse_races(text):
        text = str(text).lower()
        match = re.search(r'(\d+)\s*races', text)
        if match: return int(match.group(1))
        if text.isdigit(): return int(text)
        return 1
    return series.apply(parse_races)

def parse_uma_details(series):
    return series.astype(str).apply(lambda x: x.split(' - ')[0].strip())

def anonymize_players(df, metric='Calculated_WinRate', top_n=10):
    player_stats = df.groupby('Clean_IGN').agg({metric: 'mean', 'Clean_Wins': 'sum', 'Clean_Races': 'sum'}).reset_index()
    eligible_pros = player_stats[player_stats['Clean_Races'] >= 20]
    top_players = eligible_pros.sort_values(metric, ascending=False).head(top_n)['Clean_IGN'].tolist()
    df['Display_IGN'] = df['Clean_IGN'].apply(lambda x: x if x in top_players else "Anonymous Trainer")
    return df

# --- LOAD DATA ---
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
        return df
    except Exception as e:
        st.error(f"Data Error: {e}")
        return pd.DataFrame()

# --- APP ---
df = load_data()
st.title("🏆 Virgo Cup CM5 Analytics")

if not df.empty:
    # Reconstruct Teams
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
    
    comp_counts = team_df['Team_Comp'].value_counts()
    valid_comps = comp_counts[comp_counts > 7].index.tolist()
    filtered_team_df = team_df[team_df['Team_Comp'].isin(valid_comps)]

    tab1, tab2, tab3, tab4 = st.tabs(["Money & Meta", "Card Impact", "Leaderboard", "Strategy"])

    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Win Rate by Spending Tier")
            team_df = team_df.sort_values('Sort_Money')
            st.plotly_chart(px.box(team_df, x='Original_Spent', y='Calculated_WinRate', color='Original_Spent', title="Money vs Win Rate", template='plotly_dark'), use_container_width=True)
        with col2:
            st.subheader("Ideal Team Compositions")
            comp_stats = filtered_team_df.groupby('Team_Comp').agg({'Calculated_WinRate': 'mean'}).reset_index()
            st.plotly_chart(px.bar(comp_stats.sort_values('Calculated_WinRate', ascending=False).head(15), x='Calculated_WinRate', y='Team_Comp', orientation='h', color='Calculated_WinRate', color_continuous_scale='Plasma', template='plotly_dark'), use_container_width=True)

    with tab2:
        st.subheader("Support Card Impact")
        targets = ['Fine Motion', 'SSR Riko', 'SR Riko', 'Kitasan']
        target = st.selectbox("Select Card", targets)
        col_match = next((c for c in df.columns if target.lower() in c.lower() and "Card Status" in c), None)
        if col_match:
            card_stats = df.drop_duplicates(subset=['Clean_IGN', 'Round', 'Day']).groupby(col_match)['Calculated_WinRate'].mean().reset_index()
            st.plotly_chart(px.bar(card_stats, x=col_match, y='Calculated_WinRate', color='Calculated_WinRate', color_continuous_scale='Bluered', template='plotly_dark'), use_container_width=True)

    with tab3:
        st.subheader("Cumulative Standout Performers")
        st.caption("Top 10 Trainers (All-Time). Stacked by Round.")
        named_teams = team_df[team_df['Display_IGN'] != "Anonymous Trainer"].copy()
        
        # Get stats stacked by Round
        stacked_data = named_teams.groupby(['Display_IGN', 'Team_Comp', 'Round']).agg({'Clean_Wins': 'sum', 'Clean_Races': 'sum'}).reset_index()
        
        # Calculate Global Stats for Sorting
        global_stats = stacked_data.groupby(['Display_IGN', 'Team_Comp']).agg({'Clean_Wins': 'sum', 'Clean_Races': 'sum'}).reset_index()
        global_stats['Global_WinRate'] = (global_stats['Clean_Wins'] / global_stats['Clean_Races']) * 100
        global_stats = global_stats[global_stats['Clean_Races'] >= 10].sort_values('Global_WinRate', ascending=False).head(10)
        
        top_players = global_stats['Display_IGN'].tolist()
        plot_data = stacked_data[stacked_data['Display_IGN'].isin(top_players)].copy()
        plot_data['Label'] = plot_data['Display_IGN'] + " (" + plot_data['Team_Comp'] + ")"
        
        # Merge for sort order
        plot_data = plot_data.merge(global_stats[['Display_IGN', 'Global_WinRate']], on='Display_IGN')
        plot_data = plot_data.sort_values('Global_WinRate', ascending=True)
        
        st.plotly_chart(px.bar(plot_data, x='Clean_Wins', y='Label', orientation='h', color='Round', title="Top 10 Trainers (Sorted by Win Rate)", labels={'Clean_Wins': 'Total Wins'}, template='plotly_dark'), use_container_width=True)

    with tab4:
        st.subheader("Strategy Analysis")
        col_style, col_run = st.columns(2)
        with col_style:
            style_stats = df.groupby('Clean_Style').agg({'Calculated_WinRate': 'mean', 'Clean_Races': 'count'}).reset_index()
            style_stats = style_stats[style_stats['Clean_Races'] > 20]
            st.plotly_chart(px.bar(style_stats.sort_values('Calculated_WinRate', ascending=False), x='Calculated_WinRate', y='Clean_Style', orientation='h', color='Calculated_WinRate', template='plotly_dark', title="Performance by Running Style"), use_container_width=True)
        
        with col_run:
            team_df['Has_Runner'] = team_df['Clean_Style'].apply(lambda s: any("Runner" in str(x) or "Front" in str(x) for x in s))
            runner_stats = team_df.groupby('Has_Runner')['Calculated_WinRate'].mean().reset_index()
            runner_stats['Strategy'] = runner_stats['Has_Runner'].map({True: 'With Runner', False: 'No Runner'})
            st.plotly_chart(px.bar(runner_stats, x='Strategy', y='Calculated_WinRate', color='Strategy', template='plotly_dark', title="Impact of Runner in Team"), use_container_width=True)
