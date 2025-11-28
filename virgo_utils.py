import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import os
import re
import html

# --- CONFIGURATION ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTR8Pa4QQVSNwepSe9dYnro3ZaVEpYQmBdZUzumuLL-U2IR3nKVh-_GbZeJHT2x9aCqnp7P-0hPm5Zd/pub?gid=221070242&single=true&output=csv"

PLOT_CONFIG = {
    'scrollZoom': False, 
    'displayModeBar': True,
    'displaylogo': False,
    'modeBarButtonsToRemove': ['sendDataToCloud', 'lasso2d', 'select2d', 'zoom2d', 'pan2d']
}

DESCRIPTIONS = {} 

ORIGINAL_UMAS = [
    "Maruzensky", "Taiki Shuttle", "Oguri Cap", "El Condor Pasa", "Grass Wonder",
    "Silence Suzuka", "Gold Ship", "Vodka", "Daiwa Scarlet", "Mejiro Ryan",
    "Rice Shower", "Winning Ticket", "Haru Urara", "Matikanefukukitaru",
    "Nice Nature", "King Halo", "Agnes Tachyon", "Super Creek", "Mayaano Top Gun",
    "Mihono Bourbon", "Tokai Teio", "Symboli Rudolf", "Air Groove", "Seiun Sky",
    "Biwa Hayahide", "Narita Brian", "Hishi Amazon", "Fuji Kiseki", "Curren Chan",
    "Smart Falcon", "Narita Taishin", "Kawakami Princess", "Gold City", "Sakura Bakushin O"
]

VARIANT_MAP = {
    "Summer": "Summer", "Hot Summer": "Summer",
    "Valentine": "Valentine", "Christmas": "Christmas", "Holiday": "Christmas",
    "Hopp'n Happy Heart": "Summer", "Carnival": "Festival",
    "Wedding": "Wedding", "Bouquet": "Wedding",
    "Saintly Jade Cleric": "Fantasy", "Kukulkan": "Fantasy",
    "Chiffon-Wrapped Mummy": "Halloween", "New Year": "New Year",
    "Vampire Makeover!": "Halloween", "Festival": "Festival",
    "Quercus Civilis": "Wedding", "End of the Skies": "Anime", "Beyond the Horizon": "Anime",
    "Lucky Tidings": "Full Armor", "Princess": "Princess"
}

def smart_match_name(raw_name, valid_csv_names):
    if pd.isna(raw_name): return "Unknown"
    raw_name = str(raw_name)
    base_match = re.search(r'\]\s*(.*)', raw_name)
    title_match = re.search(r'\[(.*?)\]', raw_name)
    base_name = base_match.group(1).strip() if base_match else raw_name.strip()
    title_text = title_match.group(1) if title_match else ""

    variant_suffix = None
    for keyword, suffix in VARIANT_MAP.items():
        if keyword.lower() in title_text.lower():
            variant_suffix = suffix
            break
    
    candidates = []
    if variant_suffix:
        candidates.append(f"{base_name} ({variant_suffix})")
        candidates.append(f"{variant_suffix} {base_name}")
    candidates.append(base_name)
    
    for cand in candidates:
        match = next((valid for valid in valid_csv_names if valid.lower() == cand.lower()), None)
        if match: return match
            
    if base_name in ORIGINAL_UMAS: return base_name
    return base_name 

def sanitize_text(text):
    if pd.isna(text): return text
    return html.escape(str(text))

def find_column(df, keywords, case_sensitive=False):
    if df.empty: return None
    cols = df.columns.tolist()
    for col in cols:
        for key in keywords:
            if case_sensitive:
                if key in col: return col
            else:
                if key.lower() in col.lower(): return col
    
    clean_cols = df.columns.str.lower().str.replace(r'[^a-z0-9]', '', regex=True)
    for i, col in enumerate(clean_cols):
        for key in keywords:
            clean_key = key.lower().replace(' ', '').replace('?', '')
            if clean_key in col: return df.columns[i]
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

def parse_uma_details(series):
    return series.astype(str).apply(lambda x: x.split(' - ')[0].strip().title())

def calculate_score(wins, races):
    if races == 0: return 0
    wr = (wins / races) * 100
    return wr * np.sqrt(races)

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
    return fig

# --- UPDATED LOAD FINALS DATA ---
@st.cache_data(ttl=3600)
def load_finals_data(csv_path, parquet_path, main_ocr_df=None):
    if not csv_path or not os.path.exists(csv_path):
        return pd.DataFrame(), pd.DataFrame()

    try:
        raw_df = pd.read_csv(csv_path)
        
        # Metadata
        col_spent = find_column(raw_df, ['spent', 'money', 'eur/usd', 'howmuchhaveyouspent'])
        col_runs = find_column(raw_df, ['career runs', 'runs per day', 'howmanycareer'])
        col_kitasan = find_column(raw_df, ['kitasan', 'speed: kitasan'])
        col_fine = find_column(raw_df, ['fine motion', 'wit: fine'])
        
        # Specific Winner Column
        col_winner_name = find_column(raw_df, ['which uma won the finals lobby', 'lobby winner', 'whichumawonthefinalslobby'])

        opp_cols = []
        for i in range(1, 4):
            c = find_column(raw_df, [f"opponent's team - uma {i}", f"opponent team - uma {i}", f"opponent team uma {i}"])
            opp_cols.append(c)

        processed_rows = []
        
        for _, row in raw_df.iterrows():
            ign = str(row.get('Player in-game name (IGN)', 'Unknown')).strip()
            result = str(row.get('Finals race result', 'Unknown'))
            team_won = 1 if '1st' in str(result).lower() else 0
            
            spending = row.get(col_spent, 'Unknown') if col_spent else 'Unknown'
            runs_per_day = row.get(col_runs, 'Unknown') if col_runs else 'Unknown'
            card_kitasan = row.get(col_kitasan, 'Unknown') if col_kitasan else 'Unknown'
            card_fine = row.get(col_fine, 'Unknown') if col_fine else 'Unknown'
            
            # Parse Specific Lobby Winner
            lobby_winner = "Unknown"
            if col_winner_name:
                val = row.get(col_winner_name)
                if pd.notna(val):
                     # Clean format like "Oguri Cap - Strategy"
                     lobby_winner = str(val).split(' - ')[0].strip().title()

            match_opponents = []
            for c in opp_cols:
                if c:
                    val = row.get(c)
                    if pd.notna(val) and str(val).strip() != "":
                        match_opponents.append(parse_uma_details(pd.Series([val]))[0])
            
            for i in range(1, 4):
                uma_name = row.get(f'Own Team - Uma {i}')
                style = row.get(f'Own team - Uma {i} - Running Style')
                role = row.get(f'Own team - Uma {i} - Role', 'Unknown')
                
                if pd.notna(uma_name) and str(uma_name).strip() != "":
                    clean_name = parse_uma_details(pd.Series([uma_name]))[0]
                    
                    # Determine Specific Winner
                    # Team must have won AND name must match lobby winner (fuzzy match)
                    is_specific_winner = 0
                    if team_won == 1:
                        # Check if clean_name matches lobby_winner (ignoring case/partial)
                        c_low = clean_name.lower()
                        w_low = lobby_winner.lower()
                        if c_low == w_low or w_low in c_low or c_low in w_low:
                             is_specific_winner = 1

                    processed_rows.append({
                        'Match_IGN': ign.lower(),
                        'Display_IGN': ign,
                        'Clean_Uma': clean_name,
                        'Clean_Style': style,
                        'Clean_Role': role,
                        'Result': result,
                        'Spending_Text': spending,
                        'Runs_Text': runs_per_day,
                        'Card_Kitasan': card_kitasan,
                        'Card_Fine': card_fine,
                        'Opponents': match_opponents,
                        'Is_Winner': team_won,                 # Team Status
                        'Is_Specific_Winner': is_specific_winner # Individual Status
                    })
        
        finals_matches = pd.DataFrame(processed_rows)
        if not finals_matches.empty:
            finals_matches['Sort_Money'] = clean_currency_numeric(finals_matches['Spending_Text'])

    except Exception as e:
        st.error(f"Error parsing Finals CSV: {e}")
        return pd.DataFrame(), pd.DataFrame()

    try:
        merged_results = []
        valid_names = finals_matches['Clean_Uma'].unique().tolist() if not finals_matches.empty else []

        finals_pq_df = pd.DataFrame()
        if parquet_path and os.path.exists(parquet_path):
            finals_pq_df = pd.read_parquet(parquet_path)
            if 'ign' in finals_pq_df.columns:
                finals_pq_df['Match_IGN'] = finals_pq_df['ign'].astype(str).str.lower().str.strip()
            if 'name' in finals_pq_df.columns:
                finals_pq_df['Match_Uma'] = finals_pq_df['name'].apply(lambda x: smart_match_name(x, valid_names))

        if not finals_matches.empty and not finals_pq_df.empty:
            finals_matches['Match_Uma'] = finals_matches['Clean_Uma']
            merged_1 = pd.merge(finals_pq_df, finals_matches, on=['Match_IGN', 'Match_Uma'], how='inner')
            merged_results.append(merged_1)
        
        if main_ocr_df is not None and not main_ocr_df.empty and not finals_matches.empty:
            if 'Match_IGN' not in main_ocr_df.columns and 'ign' in main_ocr_df.columns:
                main_ocr_df['Match_IGN'] = main_ocr_df['ign'].astype(str).str.lower().str.strip()
            if 'Match_Uma' not in main_ocr_df.columns and 'name' in main_ocr_df.columns:
                main_ocr_df['Match_Uma'] = main_ocr_df['name'].apply(lambda x: smart_match_name(x, valid_names))
                
            found_keys = set()
            if merged_results:
                for df in merged_results:
                    for _, r in df.iterrows():
                        found_keys.add((r['Match_IGN'], r['Match_Uma']))
            
            finals_matches['match_key'] = list(zip(finals_matches['Match_IGN'], finals_matches['Match_Uma']))
            missing_matches = finals_matches[~finals_matches['match_key'].isin(found_keys)].drop(columns=['match_key'])
            
            if not missing_matches.empty:
                merged_2 = pd.merge(main_ocr_df, missing_matches, on=['Match_IGN', 'Match_Uma'], how='inner')
                merged_results.append(merged_2)

        final_merged_df = pd.concat(merged_results, ignore_index=True) if merged_results else pd.DataFrame()
        return finals_matches, final_merged_df
        
    except Exception as e:
        st.error(f"Error merging Finals Parquet: {e}")
        return finals_matches, pd.DataFrame()

@st.cache_data(ttl=3600)
def load_data(sheet_url):
    try:
        df = pd.read_csv(sheet_url)
        string_cols = df.select_dtypes(include=['object']).columns
        for col in string_cols: df[col] = df[col].apply(sanitize_text)
        
        col_ign = find_column(df, ['ign', 'player'])
        col_uma = find_column(df, ['uma'])
        col_wins = find_column(df, ['wins', 'victory'])
        col_races = find_column(df, ['races', 'played'])
        
        if col_uma: df['Clean_Uma'] = parse_uma_details(df[col_uma])
        else: df['Clean_Uma'] = "Unknown"
        
        if col_races: df['Clean_Races'] = pd.to_numeric(df[col_races], errors='coerce').fillna(1)
        else: df['Clean_Races'] = 1
            
        if col_wins: df['Clean_Wins'] = pd.to_numeric(df[col_wins], errors='coerce').fillna(0)
        else: df['Clean_Wins'] = 0
        
        return df, pd.DataFrame()
    except:
        return pd.DataFrame(), pd.DataFrame()

@st.cache_data(ttl=300) 
def load_ocr_data(parquet_file):
    try:
        if not os.path.exists(parquet_file): return pd.DataFrame()
        df = pd.read_parquet(parquet_file)
        stat_cols = ['Speed', 'Stamina', 'Power', 'Guts', 'Wit']
        for col in stat_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        return df
    except:
        return pd.DataFrame()