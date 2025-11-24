import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from PIL import Image
import os

# --- CONFIGURATION ---
# Live Exploded CSV
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTR8Pa4QQVSNwepSe9dYnro3ZaVEpYQmBdZUzumuLL-U2IR3nKVh-_GbZeJHT2x9aCqnp7P-0hPm5Zd/pub?gid=221070242&single=true&output=csv"

# Chart Configuration (Locks Zoom)
PLOT_CONFIG = {
    'scrollZoom': False, 
    'displayModeBar': True,
    'displaylogo': False,
    'modeBarButtonsToRemove': ['sendDataToCloud', 'lasso2d', 'select2d', 'zoom2d', 'pan2d', 'autoScale2d', 'resetScale2d']
}

# Footer HTML
footer_html = """
<style>
.footer {
    position: fixed; left: 0; bottom: 0; width: 100%;
    background-color: #0E1117; color: #888; text-align: center;
    padding: 10px; font-size: 12px; border-top: 1px solid #333;
    z-index: 100; display: flex; justify-content: center; gap: 20px;
}
.footer a { color: #00CC96; text-decoration: none; font-weight: bold; }
.footer a:hover { text-decoration: underline; color: #FAFAFA; }
</style>
<div class="footer">
    <span>Made by <b>Zuse</b> 🚀</span>
    <span>👾 Discord: <b>@zusethegoose</b></span>
    <span><a href="https://github.com/ZuseGD" target="_blank">💻 GitHub</a></span>
    <span><a href="https://paypal.me/paypal.me/JgamersZuse" target="_blank">☕ Support</a></span>
</div>
"""

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
    # Extracts number from "4 Attempts - 20 Races"
    def parse_races(text):
        text = str(text).lower()
        import re
        match = re.search(r'(\d+)\s*races', text)
        if match: return int(match.group(1))
        if text.isdigit(): return int(text)
        return 1 
    return series.apply(parse_races)

def parse_uma_details(series):
    return series.astype(str).apply(lambda x: x.split(' - ')[0].strip().title())

def calculate_score(wins, races):
    # Weighted Score: WinRate * log(Volume)
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

def style_fig(fig, height=600):
    fig.update_layout(
        font=dict(size=14), 
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=10, r=10, t=40, b=10),
        autosize=True,
        height=height,
        yaxis=dict(automargin=True),
        xaxis=dict(automargin=True)
    )
    # Lock axes to prevent infinite scrolling
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig

# --- DATA LOADING ---
@st.cache_data(ttl=600)
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
        
        # Team Reconstruction
        team_df = df.groupby(['Clean_IGN', 'Display_IGN', 'Clean_Group', 'Round', 'Day', 'Original_Spent', 'Sort_Money']).agg({
            'Clean_Uma': lambda x: sorted(list(x)), 
            'Clean_Style': lambda x: list(x),       
            'Calculated_WinRate': 'mean',           
            'Clean_Races': 'mean',
            'Clean_Wins': 'mean'
        }).reset_index()
        
        team_df['Score'] = team_df.apply(lambda x: calculate_score(x['Clean_Wins'], x['Clean_Races']), axis=1)
        team_df['Uma_Count'] = team_df['Clean_Uma'].apply(len)
        team_df = team_df[team_df['Uma_Count'] == 3]
        team_df['Team_Comp'] = team_df['Clean_Uma'].apply(lambda x: ", ".join(x))
        
        return df, team_df
    except Exception as e:
        st.error(f"Data Error: {e}")
        return pd.DataFrame(), pd.DataFrame()