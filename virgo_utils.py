import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import os
import re
import html
from typing import Tuple, List, Optional

# --- CONFIGURATION ---

PLOT_CONFIG = {
    'scrollZoom': False, 
    'displayModeBar': True,
    'displaylogo': False,
    'modeBarButtonsToRemove': ['sendDataToCloud', 'lasso2d', 'select2d', 'zoom2d', 'pan2d']
}

DESCRIPTIONS = {
    "bias": """
    **⚠️ Survivorship Bias Warning:**
    - This data is self-reported by the community.
    - Players who perform well (high win rates) are **more likely** to submit data than those who lose.
    - As the event progresses (Round 2), casual players may stop playing/reporting, artificially inflating the average skill level of the remaining pool.
    - *Take "Average Win Rates" as a benchmark for competitive players, not the entire player base.*
    """,
    "leaderboard": """
    **Ranking Logic:** Trainers are ranked by **Performance Score** (Win Rate × Log Volume).
    - This ensures high-volume winners rank above players with 1/1 wins.
    - *Note: Only Top 10 are named; others are anonymized.*
    """,
    "money": """
    **Spending vs Win Rate:**
    - Box Plot showing the distribution of win rates per spending tier.
    - *Box:* Middle 50% of players. *Line:* Median.
    """,
    "teams": """
    **Meta Teams:**
    - Unique 3-Uma combinations used in a single session.
    - Only teams with >7 entries shown.
    """,
    "umas": """
    **⚠️ IMPORTANT DISCLAIMER:**
    - Win Rate is based on the **TEAM'S** performance when this Uma was present.
    - We cannot track individual race wins from this dataset.
    """,
    # --- HOME ---
    "dist_wr": """
    **Win Rate Distribution:**
    - **What it shows:** A histogram of all players' win rates.
    - **Interpretation:** Most players fall in the middle (Bell Curve). If you are on the far right, you are in the top percentile.
    """,
    "group_diff": """
    **Group Difficulty:**
    - **Metric:** Average Win Rate of all players within a specific CM Group.
    - **Goal:** To see which bracket was the most competitive. Lower average win rates usually indicate a harder group (players beating each other up).
    """,
    # --- TEAMS ---
    "teams_meta": """
    **Meta Teams:**
    - **Definition:** Specific combinations of 3 Umas used in a single session.
    - **Filter:** Only teams seen at least 8 times are displayed.
    - **Metric:** Average win rate of that specific trio.
    """,
    "teams_bubble": """
    **Team Meta Quadrants:**
    - **X-Axis (Popularity):** How many times this specific team trio was used.
    - **Y-Axis (Performance):** The average win rate of this team.
    - **Bubble Size:** Larger bubbles = More popular.
    - **Goal:** To separate the "Standard Meta" from "Niche Counter-Meta" teams.
    """,
    "evolution": """
    **Meta Evolution:**
    - **What it shows:** How the popularity of the Top 5 teams changed across Rounds/Days.
    - **Goal:** Detect shifts in the meta (e.g., Did 'Team A' fall off in Round 2?).
    """,
    "style": """
    **Running Style:**
    - **Metric:** Win rate by strategy (Runaway/Oonige, Front, etc.).
    - **Goal:** Identifies the dominant running style for this specific track.
    """,
    "runaway": """
    **Runaway Impact:**
    - **Hypothesis:** "You need a Runaway (Oonige) to control the pace."
    - **Metric:** Compares win rates of teams *with* at least one Runaway vs teams *without* one.
    """,
    # --- UMAS ---
    "scatter_tier": """
    **Tier List Quadrants:**
    - **Top Right (Meta):** High Usage, High Win Rate. The standard picks.
    - **Top Left (Sleepers):** Low Usage, High Win Rate. Strong but underused.
    - **Bottom Right (Overrated):** High Usage, Low Win Rate. Popular but struggling.
    - **Bottom Left (Off-Meta):** Low Usage, Low Win Rate.
    """,
    "uma_bar": """
    **Standard Tier List:**
    - **Metric:** The Win Rate of *teams* containing this Uma.
    - **Note:** Includes only characters with >10 logged races.
    """,
    "drilldown": """
    **Strategy Breakdown:**
    - **Goal:** For the selected Uma, which running style performs best?
    - **Data:** Win rate filtered by the specific strategies used on this character.
    """,
    # --- RESOURCES ---
    "cards": """
    **Support Card Impact:**
    - **Metric:** Win rate of players who own specific cards (e.g., SSR vs Non-SSR).
    - **Goal:** Measures the "P2W" impact of having top-tier meta cards.
    """,
    "luck_grind": """
    **Luck vs. Grind:**
    - **X-Axis:** Total Races Played. **Y-Axis:** Win Rate.
    - **Trend:** Often, extremely high win rates drop as players play more matches. This chart tests if "Grinding" normalizes your score.
    """,
    # --- OCR ---
    "ocr_dist": """
    **Stat Distribution:**
    - **Source:** Data scanned directly from user screenshots.
    - **Goal:** Shows the spread of raw stats (Speed, Power, etc.) to identify the average build quality.
    """,
    "ocr_score": """
    **Score Efficiency:**
    - **What it shows:** Relationship between a single stat (e.g., Speed) and the overall evaluation score (UG, SS, etc.).
    """
}

# 1. LIST OF ORIGINAL UMAS (Base Names)
ORIGINAL_UMAS = [
    "Maruzensky", "Taiki Shuttle", "Oguri Cap", "El Condor Pasa", "Grass Wonder",
    "Silence Suzuka", "Gold Ship", "Vodka", "Daiwa Scarlet", "Mejiro Ryan",
    "Rice Shower", "Winning Ticket", "Haru Urara", "Matikanefukukitaru",
    "Nice Nature", "King Halo", "Agnes Tachyon", "Super Creek", "Mayaano Top Gun",
    "Mihono Bourbon", "Tokai Teio", "Symboli Rudolf", "Air Groove", "Seiun Sky",
    "Biwa Hayahide", "Narita Brian", "Hishi Amazon", "Fuji Kiseki", "Curren Chan",
    "Smart Falcon", "Narita Taishin", "Kawakami Princess", "Gold City", "Sakura Bakushin O"
]

# 2. VARIANT KEYWORDS
VARIANT_MAP = {
    "Summer": "Summer", "Hot Summer": "Summer",
    "Valentine": "Valentine", "Christmas": "Christmas", "Holiday": "Christmas",
    "Hopp'n Happy Heart": "Summer", "Carnival": "Festival",
    "Wedding": "Wedding", "Bouquet": "Wedding",
    "Saintly Jade Cleric": "Fantasy", "Kukulkan": "Fantasy",
    "Chiffon-Wrapped Mummy": "Halloween", "New Year": "New Year",
    "Vampire Makeover!": "Halloween", "Festival": "Festival",
    "Quercus Civilis": "Wedding", "End of the Skies": "Anime", "Beyond the Horizon": "Anime",
    "Anime Collab": "Anime", "Cyberpunk": "Cyberpunk",
    "Lucky Tidings": "Full Armor", "Princess": "Princess"
}


def smart_match_name(raw_name, valid_csv_names):
    """
    Tries to find the best match in the CSV list (Variant > Base > Fallback).
    """
    if pd.isna(raw_name): return "Unknown"
    raw_name = str(raw_name)

    # 1. Extract Base Name & Title
    base_match = re.search(r'\]\s*(.*)', raw_name)
    title_match = re.search(r'\[(.*?)\]', raw_name)
    
    base_name = base_match.group(1).strip() if base_match else raw_name.strip()
    title_text = title_match.group(1) if title_match else ""

    # 2. Detect Variant Suffix
    variant_suffix = None
    for keyword, suffix in VARIANT_MAP.items():
        if keyword.lower() in title_text.lower():
            variant_suffix = suffix
            break
    
    # 3. Construct Potential Names
    candidates = []
    if variant_suffix:
        candidates.append(f"{base_name} ({variant_suffix})")
        candidates.append(f"{variant_suffix} {base_name}")
    candidates.append(base_name)
    
    # 4. Check against Valid CSV Names
    for cand in candidates:
        match = next((valid for valid in valid_csv_names if valid.lower() == cand.lower()), None)
        if match: return match
            
    # 5. Fallback
    if base_name in ORIGINAL_UMAS: return base_name
    return base_name 

def sanitize_text(text):
    """Escapes HTML characters in a string to prevent injection attacks."""
    if pd.isna(text):
        return text
    return html.escape(str(text))

def show_description(key):
    """Displays an expander with the description if the key exists."""
    if key in DESCRIPTIONS:
        with st.expander("ℹ️ How is this calculated?", expanded=False):
            st.markdown(DESCRIPTIONS[key])

def find_column(df: pd.DataFrame, keywords: List[str], case_sensitive: bool = False) -> Optional[str]:
    """Helper to find a column name fuzzy-matching a list of keywords."""
    if df.empty: return None
    cols = df.columns.tolist()
    
    # 1. Exact/Case-insensitive match
    for col in cols:
        for key in keywords:
            if case_sensitive:
                if col == key: return col
            elif col.lower() == key.lower(): return col
            
    # 2. Fuzzy match (ignore spaces/underscores)
    clean_cols = df.columns.str.lower().str.replace(r'[\s_\-]', '', regex=True)
    for i, col in enumerate(clean_cols):
        for key in keywords:
            if key.lower() in col: return df.columns[i]
    return None

def _explode_raw_form_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Detects if the dataframe is in raw 'Wide' format (Day 1 - Team 1 - Uma 1...)
    and transforms it into the 'Long' format (One row per Uma) expected by the dashboard.
    """
    
    # 1. Detection: Check for specific raw column pattern
    is_raw_format = any('Day 1 - Team Comp 1 - Uma 1 - Name' in col for col in df.columns)
    
    if not is_raw_format:
        return df

    # 2. Identify Core Metadata Columns (Common for all rows)
    ign_col = find_column(df, ['ign', 'player'])
    group_col = find_column(df, ['cmgroup', 'bracket', 'league', 'selection'])
    money_col = find_column(df, ['spent', 'eur/usd', 'money'])
    
    # 3. Iteration & Transformation
    processed_dfs = []
    
    # We iterate through Days (1-4) and Teams (1-2)
    for day in range(1, 5):
        for team_idx in range(1, 3):
            # Dynamic Column prefixes based on Google Form schema
            prefix = f"Day {day} - Team Comp {team_idx}"
            
            # Find the Wins/Races columns for this specific Team/Day combo
            # These column names vary slightly in the form ("Number of wins", "No. of wins", etc.)
            cols_in_df = df.columns
            wins_col = next((c for c in cols_in_df if prefix in c and 'wins' in c.lower()), None)
            races_col = next((c for c in cols_in_df if prefix in c and ('races' in c.lower() or 'attempts' in c.lower())), None)
            
            # If we can't find win/race data, this Day/Team probably doesn't exist in the form
            if not wins_col or not races_col:
                continue

            # Now get the 3 Umas for this team
            for uma_idx in range(1, 4):
                name_col = f"{prefix} - Uma {uma_idx} - Name"
                style_col = f"{prefix} - Uma {uma_idx} - Running Style"
                
                if name_col not in df.columns: 
                    continue
                
                # Extract subset
                subset = df[[ign_col, group_col, money_col, name_col, style_col, wins_col, races_col]].copy()
                
                # Rename to standard internal names
                subset.columns = ['ign', 'group', 'money', 'uma', 'style', 'wins', 'races']
                
                # Add Day/Round context
                subset['Day'] = f"Day {day}"
                subset['Round'] = f"Round {1 if day <= 2 else 2}" # We will normalize this later in _clean_raw_data
                
                # Filter out empty rows (where user didn't enter a team for this day)
                subset = subset[subset['uma'].notna() & (subset['uma'] != '')]
                
                if not subset.empty:
                    processed_dfs.append(subset)

    if not processed_dfs:
        return df # Fallback
        
    return pd.concat(processed_dfs, ignore_index=True)

def _clean_raw_data(df: pd.DataFrame) -> pd.DataFrame:
    """Internal function to sanitize and normalize the raw dataframe."""
    
    # 1. Sanitize Strings
    string_cols = df.select_dtypes(include=['object']).columns
    for col in string_cols: 
        df[col] = df[col].apply(sanitize_text)

    # 2. Map Columns (Updated for multi-dataset support)
    col_map = {
        'ign': find_column(df, ['ign', 'player']),
        'group': find_column(df, ['cmgroup', 'bracket', 'league', 'selection', 'group']),
        'money': find_column(df, ['spent', 'eur/usd', 'money']),
        'uma': find_column(df, ['uma']),
        'style': find_column(df, ['style', 'running']),
        'wins': find_column(df, ['wins', 'victory']),
        'races': find_column(df, ['races', 'played', 'attempts']),
        'Round': find_column(df, ['Round'], case_sensitive=True), 
        'Day': find_column(df, ['Day'], case_sensitive=True),
    }

    # 3. Apply Mappings & Defaults
    defaults = {
        'money': ('Original_Spent', "Unknown"),
        'group': ('Clean_Group', "Unknown"),
        'ign': ('Clean_IGN', "Anonymous"),
        'style': ('Clean_Style', "Unknown"),
        'Round': ('Round', "Unknown"),
        'Day': ('Day', "Unknown"),
        'uma': ('Clean_Uma', "Unknown")
    }

    for key, (target_col, default_val) in defaults.items():
        source_col = col_map.get(key)
        if source_col:
            df[target_col] = df[source_col].fillna(default_val)
        else:
            df[target_col] = default_val

    # --- 4. DATA NORMALIZATION & MAPPING ---
    
    # A. Normalize Group Names (Libra/Virgo Standardization)
    group_map = {
        'Graded (No Uma Restrictions)': 'Graded (No Limit)',
        'Graded': 'Graded (No Limit)',
        'Open (No Uma Restrictions)': 'Open (B and below)',
        'Open': 'Open (B and below)'
    }
    df['Clean_Group'] = df['Clean_Group'].replace(group_map)

    # B. Normalize Round/Day (Libra Fix: Days 1-4 -> R1/R2)
    if not df.empty and 'Day' in df.columns:
        # Convert Day to string first to handle both "1" (int) and "Day 1" (str)
        day_str = df['Day'].astype(str)
        
        # Check if we need to apply the mapping (if we see "Day 3" or "Day 4" or just "3"/"4")
        # OR if Round is "CM"
        is_libra_format = day_str.str.contains(r'[34]').any() or (df['Round'].astype(str).str.contains('CM').any())

        if is_libra_format:
            # Map Day 1/2 -> R1, Day 3/4 -> R2
            # Note: We match partial strings to catch "Day 1" and "1"
            
            # R1 D1
            mask_r1d1 = day_str.str.contains(r'1', regex=True)
            df.loc[mask_r1d1, 'Round'] = "R1"
            df.loc[mask_r1d1, 'Day'] = "D1"

            # R1 D2
            mask_r1d2 = day_str.str.contains(r'2', regex=True)
            df.loc[mask_r1d2, 'Round'] = "R1"
            df.loc[mask_r1d2, 'Day'] = "D2"

            # R2 D1 (Day 3)
            mask_r2d1 = day_str.str.contains(r'3', regex=True)
            df.loc[mask_r2d1, 'Round'] = "R2"
            df.loc[mask_r2d1, 'Day'] = "D1"

            # R2 D2 (Day 4)
            mask_r2d2 = day_str.str.contains(r'4', regex=True)
            df.loc[mask_r2d2, 'Round'] = "R2"
            df.loc[mask_r2d2, 'Day'] = "D2"

    # C. General Round/Day Cleanup (Fallback)
    round_map = {
        'Round 1': 'R1', 'Round 2': 'R2', 'Round 3': 'R3', 'Finals': 'Finals', 'CM': 'R1'
    }
    day_map = {
        'Day 1': 'D1', 'Day 2': 'D2', '1': 'D1', '2': 'D2'
    }
    
    df['Round'] = df['Round'].replace(round_map)
    df['Day'] = df['Day'].astype(str).replace(day_map)

    # --- 5. TYPE ENFORCEMENT ---
    df['Round'] = df['Round'].astype(str)
    df['Day'] = df['Day'].astype(str)

    # Special handling for numerics
    if col_map['money']:
        df['Sort_Money'] = clean_currency_numeric(df[col_map['money']])
    else:
        df['Sort_Money'] = 0.0

    if col_map['uma']:
        df['Clean_Uma'] = parse_uma_details(df[col_map['uma']])

    # 4. Parse Stats
    if col_map['races']:
        df['Clean_Races'] = extract_races_count(df[col_map['races']])
    else:
        df['Clean_Races'] = 1
        
    if col_map['wins']:
        df['Clean_Wins'] = pd.to_numeric(df[col_map['wins']], errors='coerce').fillna(0)
    else:
        df['Clean_Wins'] = 0

    # Sanity check: Wins cannot exceed Races
    df = df[df['Clean_Wins'] <= df['Clean_Races']].copy()

    # Calculate Win Rate
    df['Calculated_WinRate'] = (df['Clean_Wins'] / df['Clean_Races']) * 100
    df.loc[df['Calculated_WinRate'] > 100, 'Calculated_WinRate'] = 100

    return df

def _process_teams(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregates individual uma rows into team rows."""
    
    # Filter out Runaway Suzuka for fairness (specific business logic)
    filter_mask = (
        df['Clean_Style'].str.contains('Runaway|Oonige|Great Escape', case=False, na=False) & 
        (df['Clean_Uma'] != 'Silence Suzuka')
    )
    df_filtered = df[~filter_mask]

    team_df = df_filtered.groupby(['Clean_IGN', 'Display_IGN', 'Clean_Group', 'Round', 'Day', 'Original_Spent', 'Sort_Money']).agg({
        'Clean_Uma': lambda x: sorted(list(x)), 
        'Clean_Style': lambda x: list(x),       
        'Calculated_WinRate': 'mean',    
        'Clean_Races': 'max',            
        'Clean_Wins': 'max'              
    }).reset_index()
    
    team_df['Score'] = team_df.apply(lambda x: calculate_score(x['Clean_Wins'], x['Clean_Races']), axis=1)
    
    # Ensure valid teams only (3 members)
    team_df = team_df[team_df['Clean_Uma'].apply(len) == 3]
    team_df['Team_Comp'] = team_df['Clean_Uma'].apply(lambda x: ", ".join(x))
    
    return team_df

@st.cache_data(ttl=3600)
def load_data(sheet_url: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Main entry point for data loading.
    Orchestrates fetching, cleaning, and team building.
    """
    try:
        # Load raw
        df = pd.read_csv(sheet_url)
        
        # NEW: Check for and Handle Raw Wide Format
        df = _explode_raw_form_data(df)
        
        # Clean
        df = _clean_raw_data(df)

        # Deduplicate (Long Format: 1 row per Uma per Session)
        # Sorting by Races ensures we keep the entry with the most data if duplicates exist
        df = df.sort_values(by=['Clean_Races', 'Clean_Wins'], ascending=[False, False])
        df = df.drop_duplicates(subset=['Clean_IGN', 'Round', 'Day', 'Clean_Uma'], keep='first')

        # Anonymize
        df = anonymize_players(df)
        
        # Build Teams
        team_df = _process_teams(df)
        
        return df, team_df

    except Exception as e:
        # In production, log this error properly!
        print(f"Error in load_data: {e}") 
        st.error(f"Data Error: {e}")
        return pd.DataFrame(), pd.DataFrame()

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
    return wr * np.sqrt(races)

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
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig

def dynamic_height(n_items, min_height=400, per_item=40):
    """Calculates chart height based on number of bars"""
    calc_height = n_items * per_item
    return max(min_height, calc_height)

# --- SHARED FILTER WIDGET ---
def render_filters(df):
    # Create a consistent filter bar at the top of the page
    with st.expander("⚙️ **Global Filters** (Round / Day / Group)", expanded=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            groups = list(df['Clean_Group'].unique())
            sel_group = st.multiselect("CM Group", groups, default=groups)
        with c2:
            rounds = sorted(list(df['Round'].unique()))
            sel_round = st.multiselect("Round", rounds, default=rounds)
        with c3:
            days = sorted(list(df['Day'].unique()))
            sel_day = st.multiselect("Day", days, default=days)
            
    # Apply Logic
    if sel_group: df = df[df['Clean_Group'].isin(sel_group)]
    if sel_round: df = df[df['Round'].isin(sel_round)]
    if sel_day: df = df[df['Day'].isin(sel_day)]
    
    return df


@st.cache_data(ttl=300) # Cache for 5 minutes
def load_ocr_data(parquet_file):
    try:
        if not os.path.exists(parquet_file):
            return pd.DataFrame()
            
        df = pd.read_parquet(parquet_file)

        # --- 🛡️ SECURITY: SANITIZE INPUTS ---
        string_cols = df.select_dtypes(include=['object']).columns
        for col in string_cols:
            df[col] = df[col].apply(sanitize_text)
        
        # --- 1. CLEANING MISSING VALUES ---
        # Remove empty names
        df.dropna(subset=['name'], inplace=True)
        
        # Fill stats with median
        stat_cols = ['Speed', 'Stamina', 'Power', 'Guts', 'Wit', 'score']
        for col in stat_cols:
            if col in df.columns:
                # Force numeric first to turn "12OO" into NaN
                df[col] = pd.to_numeric(df[col], errors='coerce')
                df[col] = df[col].fillna(df[col].median())
                df[col] = df[col].astype(int)

        # Fill text with 'Unknown'
        text_cols = ['rank', 'skills', 'Turf', 'Dirt', 'Sprint', 'Mile', 'Medium', 'Long'] 
        for col in text_cols:
            if col in df.columns:
                df[col] = df[col].fillna('Unknown')
                
        # --- 2. OUTLIER CAPPING ---
        # Cap stats at 2000 (adjust based on game scenario)
        for col in stat_cols:
             if col in df.columns:
                df[col] = df[col].clip(upper=2000)

        return df
    except Exception as e:
        st.error(f"Error loading Parquet: {e}")
        return pd.DataFrame()

# --- LOAD FINALS DATA (UPDATED FOR ROBUST MERGING) ---
@st.cache_data(ttl=3600)
def load_finals_data(csv_path, parquet_path, main_ocr_df=None):
    if not csv_path or not os.path.exists(csv_path):
        return pd.DataFrame(), pd.DataFrame()

    try:
        raw_df = pd.read_csv(csv_path)
        
        col_spent = find_column(raw_df, ['spent', 'money', 'eur/usd', 'how much have you spent'])
        col_runs = find_column(raw_df, ['career runs', 'runs per day', 'how many career runs']) 
        col_kitasan = find_column(raw_df, ['kitasan', 'speed: kitasan'])
        col_fine = find_column(raw_df, ['fine motion', 'wit: fine'])
        
        opp_cols = []
        for i in range(1, 4):
            c = find_column(raw_df, [f"opponent's team - uma {i}", f"opponent team - uma {i}", f"opponent team uma {i}"])
            opp_cols.append(c)

        processed_rows = []
        
        for _, row in raw_df.iterrows():
            ign = str(row.get('Player in-game name (IGN)', 'Unknown')).strip()
            result = str(row.get('Finals race result', 'Unknown'))
            is_win = 1 if result == '1st' else 0
            
            spending = row.get(col_spent, 'Unknown') if col_spent else 'Unknown'
            runs_per_day = row.get(col_runs, 'Unknown') if col_runs else 'Unknown'
            card_kitasan = row.get(col_kitasan, 'Unknown') if col_kitasan else 'Unknown'
            card_fine = row.get(col_fine, 'Unknown') if col_fine else 'Unknown'
            
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
                    clean_uma_name = parse_uma_details(pd.Series([uma_name]))[0]
                    
                    processed_rows.append({
                        'Match_IGN': ign.lower(),
                        'Normalized_IGN': re.sub(r'[^a-z0-9]', '', ign.lower()), # Add key for fuzzy matching
                        'Display_IGN': ign,
                        'Clean_Uma': clean_uma_name,
                        'Clean_Style': style,
                        'Clean_Role': role,
                        'Result': result,
                        'Spending_Text': spending,
                        'Runs_Text': runs_per_day,
                        'Card_Kitasan': card_kitasan,
                        'Card_Fine': card_fine,
                        'Opponents': match_opponents,
                        'Calculated_WinRate': is_win * 100, 
                        'Is_Winner': is_win
                    })
        
        finals_matches = pd.DataFrame(processed_rows)

        if not finals_matches.empty:
            finals_matches['Sort_Money'] = clean_currency_numeric(finals_matches['Spending_Text'])
        

    except Exception as e:
        st.error(f"Error parsing Finals CSV: {e}")
        return pd.DataFrame(), pd.DataFrame()

    try:
        # Combine multiple sources for OCR
        ocr_sources = []
        valid_names = finals_matches['Clean_Uma'].unique().tolist() if not finals_matches.empty else []

        # 1. Finals specific Parquet
        if parquet_path and os.path.exists(parquet_path):
            fpq = pd.read_parquet(parquet_path)
            if 'ign' in fpq.columns:
                fpq['Match_IGN'] = fpq['ign'].astype(str).str.lower().str.strip()
                fpq['Normalized_IGN'] = fpq['Match_IGN'].apply(lambda x: re.sub(r'[^a-z0-9]', '', str(x)))
            if 'name' in fpq.columns:
                fpq['Match_Uma'] = fpq['name'].apply(lambda x: smart_match_name(x, valid_names))
            ocr_sources.append(fpq)

        # 2. Main OCR (Prelims) as fallback
        if main_ocr_df is not None and not main_ocr_df.empty:
            if 'Match_IGN' not in main_ocr_df.columns and 'ign' in main_ocr_df.columns:
                main_ocr_df['Match_IGN'] = main_ocr_df['ign'].astype(str).str.lower().str.strip()
                main_ocr_df['Normalized_IGN'] = main_ocr_df['Match_IGN'].apply(lambda x: re.sub(r'[^a-z0-9]', '', str(x)))
            if 'Match_Uma' not in main_ocr_df.columns and 'name' in main_ocr_df.columns:
                main_ocr_df['Match_Uma'] = main_ocr_df['name'].apply(lambda x: smart_match_name(x, valid_names))
            ocr_sources.append(main_ocr_df)

        final_merged_df = pd.DataFrame()
        
        if not finals_matches.empty and ocr_sources:
            # Consolidated OCR
            all_ocr = pd.concat(ocr_sources, ignore_index=True).drop_duplicates(subset=['Match_IGN', 'Match_Uma'])
            
            # Prep matches for merge
            finals_matches['Match_Uma'] = finals_matches['Clean_Uma']
            
            # STRATEGY 1: Strict Merge (Best quality)
            strict_merge = pd.merge(all_ocr, finals_matches, on=['Match_IGN', 'Match_Uma'], how='inner')
            
            # Find leftovers
            matched_keys = set(zip(strict_merge['Match_IGN'], strict_merge['Match_Uma']))
            leftover_matches = finals_matches[~finals_matches.set_index(['Match_IGN', 'Match_Uma']).index.isin(matched_keys)].copy()
            
            # STRATEGY 2: Fuzzy IGN Merge (Normalized alphanumeric)
            if not leftover_matches.empty:
                # Filter OCR to only those NOT already matched to prevent duplicates
                leftover_ocr = all_ocr[~all_ocr.set_index(['Match_IGN', 'Match_Uma']).index.isin(matched_keys)].copy()
                
                fuzzy_merge = pd.merge(
                    leftover_ocr, 
                    leftover_matches, 
                    on=['Normalized_IGN', 'Match_Uma'], 
                    how='inner', 
                    suffixes=('_ocr', '')
                )
                # Cleanup duplicate cols if any
                if 'Match_IGN_ocr' in fuzzy_merge.columns:
                    fuzzy_merge = fuzzy_merge.drop(columns=['Match_IGN_ocr'])
                
                final_merged_df = pd.concat([strict_merge, fuzzy_merge], ignore_index=True)
            else:
                final_merged_df = strict_merge

        return finals_matches, final_merged_df
        
    except Exception as e:
        st.error(f"Error merging Finals Parquet: {e}")
        return finals_matches, pd.DataFrame()
# Common Footer
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