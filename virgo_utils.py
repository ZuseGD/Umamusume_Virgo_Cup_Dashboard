import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import os
import re
import html
import ast
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
    "Smart Falcon", "Narita Taishin", "Kawakami Princess", "Gold City", "Sakura Bakushin O", "T.M. Opera O"
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

# --- NEW: ALIAS MAP FOR KNOWN ERRORS ---
# Use this for names that are actually missing words or are completely different
NAME_ALIASES = {
    "TM Opera": "T.M. Opera O",
    "T.M. Opera": "T.M. Opera O",
    "TM Opera O": "T.M. Opera O",
    "El Condor": "El Condor Pasa",
    "Curren": "Curren Chan",
    "Cafe": "Manhattan Cafe",
    "Rudolf": "Symboli Rudolf",
    "Brian": "Narita Brian",
    "Digitan": "Agnes Digital",
    "Digital": "Agnes Digital",
    "Ardan": "Mejiro Ardan",
    "Rice": "Rice Shower",
    "Chiyono": "Chiyono O",
    "Bakushin": "Sakura Bakushin O",
    "Urara": "Haru Urara",
    "Ticket": "Winning Ticket",
    "Ryan": "Mejiro Ryan",
    "McQueen": "Mejiro McQueen",
    "Spe": "Special Week",
    "Suzuka": "Silence Suzuka",
    "Tachyon": "Agnes Tachyon",
    "Teio": "Tokai Teio",
    "Top Gun": "Mayano Top Gun",
    "Halo": "King Halo",
    "Nature": "Nice Nature",
    "Fuku": "Matikanefukukitaru",
    "Fukukitaru": "Matikanefukukitaru",
    "City": "Gold City",
    "Bright": "Mejiro Bright",
    "Dober": "Mejiro Dober",
    "Palmer": "Mejiro Palmer",
    "Helios": "Daitaku Helios",
    "Strong": "Mr. C.B.",
    "CB": "Mr. C.B.",
    "Ramona": "Mejiro Ramona",
}

#--- NEW: HELPER FOR NORMALIZATION ---
def _normalize_name_string(text):
    """
    Removes punctuation, spaces, and casing for fuzzy comparison.
    Example: "T.M. Opera O" -> "tmoperao"
             "TM Opera O"   -> "tmoperao"
    """
    return re.sub(r'[^a-zA-Z0-9]', '', str(text).lower())

def _normalize_style(style):
    """
    Standardizes running style names to ensure consistency between Short (Late) and Long (Late Surger) forms.
    """
    if pd.isna(style): return "Unknown"
    s = str(style).strip()
    sl = s.lower()
    
    # Mapping Short/Raw -> Standard Long Form
    if sl == "late": return "Late Surger"
    if sl == "pace": return "Pace Chaser"
    if sl == "front": return "Front Runner"
    if sl == "end": return "End Closer"
    if sl in ["runaway", "oonige", "great escape"]: return "Runaway"
    
    return s # Return original if it matches none (e.g. "Late Surger" already)

def _parse_run_time_to_seconds(time_str):
    """Converts 'M:SS.ms' or similar formats to total seconds (float)."""
    if pd.isna(time_str) or str(time_str).strip() == '':
        return None
    try:
        parts = str(time_str).split(':')
        if len(parts) == 2:
            minutes = float(parts[0])
            seconds = float(parts[1])
            return minutes * 60 + seconds
        return float(time_str)
    except:
        return None
    
def _normalize_libra_columns(df):
    """
    Standardizes raw Libra parquet columns to the Dashboard's expected format.
    """
    col_map = {
        'trainee_name': 'Clean_Uma',
        'trainer_name': 'Clean_IGN',
        'placement': 'Result',
        'post': 'Post',
        'time': 'Run_Time_Str',
        'style': 'Clean_Style',
        'skills': 'Skill_List',
        'skill_count': 'Skill_Count',
        'Speed': 'Speed', 'Stamina': 'Stamina', 'Power': 'Power', 
        'Guts': 'Guts', 'Wit': 'Wit', 'wisdom': 'Wit'
    }
    
    df = df.rename(columns=col_map)
    
    # --- Feature Engineering ---
    
    if 'Result' in df.columns:
        df['Result'] = pd.to_numeric(df['Result'], errors='coerce')
        df['Is_Winner'] = df['Result'].apply(lambda x: 1 if x == 1 else 0)
    else:
        df['Is_Winner'] = 0

    if 'Run_Time_Str' in df.columns:
        df['Run_Time'] = df['Run_Time_Str'].apply(_parse_run_time_to_seconds)

    # Apply Style Normalization (Fixes "Late" vs "Late Surger")
    if 'Clean_Style' in df.columns:
        df['Clean_Style'] = df['Clean_Style'].apply(_normalize_style)

    if 'Skill_List' not in df.columns:
        df['Skill_List'] = np.empty((len(df), 0)).tolist()

    def parse_skills(x):
        if pd.isna(x): return []
        if isinstance(x, (np.ndarray, list)): return list(x)
        if isinstance(x, str):
            try:
                if x.startswith('['): return ast.literal_eval(x)
                return [x] 
            except: return []
        return []
    
    df['Skill_List'] = df['Skill_List'].apply(parse_skills)

    if 'Skill_Count' not in df.columns:
        df['Skill_Count'] = df['Skill_List'].apply(len)
    else:
        df['Skill_Count'] = df['Skill_Count'].fillna(df['Skill_List'].apply(len))

    if 'Clean_Uma' in df.columns:
        df['Clean_Uma'] = df['Clean_Uma'].apply(lambda x: smart_match_name(x, ORIGINAL_UMAS))

    return df

def analyze_significant_roles(df, role_col='Clean_Role', score_col='Calculated_WinRate', threshold=5.0):
    """
    Analyzes if specific roles have a significant impact on Win Rate.
    Only returns stats if deviation from global average > threshold %.
    """
    if role_col not in df.columns or df[role_col].nunique() <= 1:
        return None

    # Filter out "Unknown" or invalid roles
    valid_df = df[~df[role_col].isin(['Unknown', '', 'nan'])]
    if valid_df.empty:
        return None

    global_avg = valid_df[score_col].mean()
    
    # Aggregation
    role_stats = valid_df.groupby(role_col).agg(
        Win_Rate=(score_col, 'mean'),
        Count=('Clean_Races', 'sum') # Use Sum of races for weight, or 'count' for entries
    ).reset_index()

    # Calculate Impact
    role_stats['Diff_vs_Avg'] = role_stats['Win_Rate'] - global_avg
    
    # Filter for significance (e.g., > 5% difference) and Sample Size (> 5 entries)
    sig_roles = role_stats[
        (role_stats['Diff_vs_Avg'].abs() >= threshold) & 
        (role_stats['Count'] >= 10)
    ].sort_values('Win_Rate', ascending=False)
    
    if sig_roles.empty:
        return None
        
    return sig_roles, global_avg

def smart_match_name(raw_name, valid_csv_names):
    if pd.isna(raw_name): return "Unknown"
    raw_name = str(raw_name).strip()
    
    # 1. FAST ALIAS CHECK (Pre-parsing)
    # catches "TM Opera" directly if listed
    if raw_name in NAME_ALIASES:
        return NAME_ALIASES[raw_name]

    # 2. PARSE BRACKETS (Existing Logic)
    base_match = re.search(r'\]\s*(.*)', raw_name)
    title_match = re.search(r'\[(.*?)\]', raw_name)
    
    base_name = base_match.group(1).strip() if base_match else raw_name.strip()
    title_text = title_match.group(1) if title_match else ""

    # 3. ALIAS CHECK (On Base Name)
    # catches "[New Year] TM Opera" -> "TM Opera" -> "T.M. Opera O"
    if base_name in NAME_ALIASES:
        base_name = NAME_ALIASES[base_name]

    # 4. VARIANT DETECTION (Existing Logic)
    variant_suffix = None
    for keyword, suffix in VARIANT_MAP.items():
        if keyword.lower() in title_text.lower():
            variant_suffix = suffix
            break
    
    candidates = []
    if variant_suffix:
        # Reconstruct canonical variant name: "T.M. Opera O (New Year)"
        candidates.append(f"{base_name} ({variant_suffix})")
        # Handle "New Year T.M. Opera O" style
        candidates.append(f"{variant_suffix} {base_name}")
        
    candidates.append(base_name)
    
    # 5. VALIDATION MATCHING
    # Try exact match first
    for cand in candidates:
        match = next((valid for valid in valid_csv_names if valid.lower() == cand.lower()), None)
        if match: return match
            
    # 6. FUZZY NORMALIZATION MATCH (The Scalable Logic)
    # This catches "T.M. Opera O" vs "TM Opera O" without an alias
    norm_base = _normalize_name_string(base_name)
    
    for valid in valid_csv_names:
        # We assume valid_csv_names contains the canonical "T.M. Opera O"
        if _normalize_name_string(valid) == norm_base:
            # If we found a base match, re-apply suffix if needed
            if variant_suffix:
                # Check if the variant exists in valid list
                canon_variant = f"{valid} ({variant_suffix})"
                if canon_variant in valid_csv_names:
                    return canon_variant
                return valid # Fallback to base if variant not found
            return valid

    # Fallback to Original List if valid_csv_names didn't help
    if base_name in ORIGINAL_UMAS: return base_name
    
    return base_name

def sanitize_text(text):
    if pd.isna(text): return text
    return html.escape(str(text))

def show_description(key):
    if key in DESCRIPTIONS:
        with st.expander("ℹ️ How is this calculated?", expanded=False):
            st.markdown(DESCRIPTIONS[key])

def find_column(df: pd.DataFrame, keywords: List[str], case_sensitive: bool = False) -> Optional[str]:
    if df.empty: return None
    cols = df.columns.tolist()
    
    for col in cols:
        for key in keywords:
            if case_sensitive:
                if col == key: return col
            elif col.lower() == key.lower(): return col
            
    clean_cols = df.columns.str.lower().str.replace(r'[\s_\-]', '', regex=True)
    for i, col in enumerate(clean_cols):
        for key in keywords:
            if key.lower() in col: return df.columns[i]
    return None

def find_col_fuzzy(df_columns, pattern_str):
    pattern = re.compile(pattern_str, re.IGNORECASE)
    for col in df_columns:
        if pattern.search(col):
            return col
    return None

def _explode_raw_form_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Detects and transforms Raw 'Wide' format. 
    Preserves Timestamp (for run uniqueness) and Cards.
    Updated to capture 'Role' if available.
    """
    print("DEBUG: Checking if file is Raw Data...")
    
    # 1. Detection
    test_col = find_col_fuzzy(df.columns, r"Day\s*1.*Team\s*Comp\s*1.*Uma\s*1.*Name")
    if test_col:
        print(f"DEBUG: Raw Data detected! Found key column: {test_col}")
    else:
        print("DEBUG: Not Raw Data (or detection failed). Skipping explode.")
        return df

    # 2. Identify Core Metadata
    ign_col = find_column(df, ['ign', 'player'])
    group_col = find_column(df, ['cmgroup', 'bracket', 'league', 'selection'])
    money_col = find_column(df, ['spent', 'eur/usd', 'money'])
    time_col = find_column(df, ['timestamp', 'date'])
    
    # --- CARD DETECTION ---
    card_cols = [c for c in df.columns if "card status in account" in c.lower()]
    print(f"DEBUG: Found {len(card_cols)} card columns in Raw Data.")
    
    card_rename_map = {}
    for col in card_cols:
        match = re.search(r'\[(.*?)\]', col)
        if match:
            clean_name = match.group(1).strip()
            card_rename_map[col] = f"card_{clean_name}"
        else:
            card_rename_map[col] = f"card_{col[:30]}"

    # 3. Iteration
    processed_dfs = []
    
    for day in range(1, 5):
        for team_idx in range(1, 3):
            prefix_pattern = f"Day\\s*{day}.*Team\\s*Comp\\s*{team_idx}"
            
            wins_col = find_col_fuzzy(df.columns, f"{prefix_pattern}.*wins")
            races_col = find_col_fuzzy(df.columns, f"{prefix_pattern}.*(races|attempts)")
            
            if not wins_col or not races_col:
                continue

            for uma_idx in range(1, 4):
                name_col = find_col_fuzzy(df.columns, f"{prefix_pattern}.*Uma\\s*{uma_idx}.*Name")
                style_col = find_col_fuzzy(df.columns, f"{prefix_pattern}.*Uma\\s*{uma_idx}.*Style")
                # --- NEW: Look for Role ---
                role_col = find_col_fuzzy(df.columns, f"{prefix_pattern}.*Uma\\s*{uma_idx}.*Role")
                
                if not name_col:
                    continue
                
                # Selection
                cols_to_select = [ign_col, group_col, money_col, name_col, style_col, wins_col, races_col] + card_cols
                if time_col: cols_to_select.append(time_col)
                if role_col: cols_to_select.append(role_col)

                subset = df[cols_to_select].copy()
                
                # Renaming
                base_rename = {
                    ign_col: 'ign', 
                    group_col: 'group', 
                    money_col: 'money', 
                    name_col: 'uma', 
                    style_col: 'style', 
                    wins_col: 'wins', 
                    races_col: 'races'
                }
                if time_col: base_rename[time_col] = 'Timestamp'
                if role_col: base_rename[role_col] = 'role'

                subset.rename(columns={**base_rename, **card_rename_map}, inplace=True)
                
                # Context
                subset['Day'] = str(day)
                subset['Round'] = "CM" 
                subset['Team_Comp'] = str(team_idx)
                
                subset = subset[subset['uma'].notna() & (subset['uma'] != '')]
                
                if not subset.empty:
                    processed_dfs.append(subset)

    if not processed_dfs:
        return df 
    
    final_df = pd.concat(processed_dfs, ignore_index=True)
    return final_df

def _clean_raw_data(df: pd.DataFrame) -> pd.DataFrame:
    string_cols = df.select_dtypes(include=['object']).columns
    for col in string_cols: 
        df[col] = df[col].apply(sanitize_text)

    # Backup Card Normalization
    raw_card_cols = [c for c in df.columns if "card status in account" in c.lower() and not c.startswith("card_")]
    if raw_card_cols:
        card_rename_map = {}
        for col in raw_card_cols:
            match = re.search(r'\[(.*?)\]', col)
            if match:
                clean_name = match.group(1).strip()
                card_rename_map[col] = f"card_{clean_name}"
            else:
                card_rename_map[col] = f"card_{col[:30]}"
        df.rename(columns=card_rename_map, inplace=True)

    col_map = {
        'ign': find_column(df, ['ign', 'player']),
        'group': find_column(df, ['cmgroup', 'bracket', 'league', 'selection', 'group']),
        'money': find_column(df, ['spent', 'eur/usd', 'money']),
        'uma': find_column(df, ['uma']),
        'style': find_column(df, ['style', 'running']),
        'wins': find_column(df, ['wins', 'victory']),
        'races': find_column(df, ['races', 'played', 'attempts', 'career']),
        'Round': find_column(df, ['Round'], case_sensitive=True), 
        'Day': find_column(df, ['Day'], case_sensitive=True),
        'Timestamp': find_column(df, ['Timestamp', 'timestamp'], case_sensitive=False),
        'Role': find_column(df, ['role', 'position'])
    }

    defaults = {
        'money': ('Original_Spent', "Unknown"),
        'group': ('Clean_Group', "Unknown"),
        'ign': ('Clean_IGN', "Anonymous"),
        'style': ('Clean_Style', "Unknown"),
        'Round': ('Round', "Unknown"),
        'Day': ('Day', "Unknown"),
        'uma': ('Clean_Uma', "Unknown"),
        'Timestamp': ('Clean_Timestamp', "Unknown"),
        'Role': ('Clean_Role', "Unity Cup Scenario Ace")
    }

    for key, (target_col, default_val) in defaults.items():
        source_col = col_map.get(key)
        if source_col:
            df[target_col] = df[source_col].fillna(default_val)
        else:
            df[target_col] = default_val

    # Type Casting
    if 'Round' in df.columns: df['Round'] = df['Round'].astype(str)
    if 'Day' in df.columns: df['Day'] = df['Day'].astype(str)
    
    # Fill Cards
    card_cols = [c for c in df.columns if c.startswith('card_')]
    if card_cols: df[card_cols] = df[card_cols].fillna("Unknown")

    # Group Mapping
    group_map = {
        'Graded (No Uma Restrictions)': 'Graded (No Limit)',
        'Graded': 'Graded (No Limit)',
        'Open (No Uma Restrictions)': 'Open (B and below)',
        'Open': 'Open (B and below)'
    }
    df['Clean_Group'] = df['Clean_Group'].replace(group_map)

    # Round/Day Normalization
    if not df.empty and 'Day' in df.columns:
        has_day_34 = df['Day'].astype(str).str.contains(r'[34]').any()
        round_is_cm = df['Round'].astype(str).str.contains('CM').any()
        
        if has_day_34 or round_is_cm:
            mask_r1d1 = df['Day'].str.contains(r'1')
            df.loc[mask_r1d1, 'Round'] = "R1"
            df.loc[mask_r1d1, 'Day'] = "D1"

            mask_r1d2 = df['Day'].str.contains(r'2')
            df.loc[mask_r1d2, 'Round'] = "R1"
            df.loc[mask_r1d2, 'Day'] = "D2"

            mask_r2d1 = df['Day'].str.contains(r'3')
            df.loc[mask_r2d1, 'Round'] = "R2"
            df.loc[mask_r2d1, 'Day'] = "D1"

            mask_r2d2 = df['Day'].str.contains(r'4')
            df.loc[mask_r2d2, 'Round'] = "R2"
            df.loc[mask_r2d2, 'Day'] = "D2"

    round_map = {'Round 1': 'R1', 'Round 2': 'R2', 'Round 3': 'R3', 'Finals': 'Finals', 'CM': 'R1'}
    day_map = {'Day 1': 'D1', 'Day 2': 'D2', '1': 'D1', '2': 'D2'}
    
    if 'Round' in df.columns: df['Round'] = df['Round'].replace(round_map)
    if 'Day' in df.columns: df['Day'] = df['Day'].astype(str).replace(day_map)

    if col_map['money']: df['Sort_Money'] = clean_currency_numeric(df[col_map['money']])
    else: df['Sort_Money'] = 0.0

    if col_map['uma']: df['Clean_Uma'] = parse_uma_details(df[col_map['uma']])

    if col_map['races']: df['Clean_Races'] = extract_races_count(df[col_map['races']])
    else: df['Clean_Races'] = 1
        
    if col_map['wins']: df['Clean_Wins'] = pd.to_numeric(df[col_map['wins']], errors='coerce').fillna(0)
    else: df['Clean_Wins'] = 0

    df = df[df['Clean_Wins'] <= df['Clean_Races']].copy()
    df['Calculated_WinRate'] = (df['Clean_Wins'] / df['Clean_Races']) * 100
    df.loc[df['Calculated_WinRate'] > 100, 'Calculated_WinRate'] = 100

    # Filter out rows where Round is 'Finals'
    if 'Round' in df.columns:
        df = df[df['Round'] != 'Finals']
    
    # robustly check Day column as well just in case
    if 'Day' in df.columns:
        df = df[df['Day'] != 'Finals']

    return df

def _process_teams(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregates individual uma rows into team rows."""
    
    filter_mask = (
        df['Clean_Style'].str.contains('Runaway|Oonige|Great Escape', case=False, na=False) & 
        (df['Clean_Uma'] != 'Silence Suzuka')
    )
    df_filtered = df[~filter_mask].copy()

    # --- CRITICAL FIX: DO NOT GROUP BY CARDS ---
    # We move cards to Aggregation so they don't split the rows if data is messy
    card_cols = [c for c in df.columns if c.startswith('card_')]
    
    # Identify unique run keys. Use Timestamp if available, otherwise fallback.
    # Note: 'Team_Comp' comes from exploded data to distinguish Team 1 vs 2 on same day
    potential_keys = ['Clean_IGN', 'Display_IGN', 'Clean_Group', 'Round', 'Day', 'Original_Spent', 'Sort_Money', 'Clean_Timestamp', 'Team_Comp']
    group_cols = [c for c in potential_keys if c in df.columns]

    print(f"DEBUG: Grouping by {len(group_cols)} keys: {group_cols}")
    print(f"DEBUG: Collapsing {len(card_cols)} card columns using 'first'.")

    # Define Aggregations
    agg_rules = {
        'Clean_Uma': lambda x: sorted(list(x)), 
        'Clean_Style': lambda x: list(x),       
        'Calculated_WinRate': 'mean',    
        'Clean_Races': 'max',            
        'Clean_Wins': 'max'              
    }
    
    # Add cards to aggregation rules (Take first value found for the team)
    for c in card_cols:
        agg_rules[c] = 'first'

    # Perform Grouping
    team_df = df_filtered.groupby(group_cols, dropna=False).agg(agg_rules).reset_index()
    
    team_df['Score'] = team_df.apply(lambda x: calculate_score(x['Clean_Wins'], x['Clean_Races']), axis=1)
    
    # Filter for valid teams (3 members)
    team_df = team_df[team_df['Clean_Uma'].apply(len) == 3]
    team_df['Team_Comp'] = team_df['Clean_Uma'].apply(lambda x: ", ".join(x))
    
    
    # Filter out rows where Round is 'Finals'
    if 'Round' in team_df.columns:
        team_df = team_df[team_df['Round'] != 'Finals']
    
    # robustly check Day column as well just in case
    if 'Day' in team_df.columns:
        team_df = team_df[team_df['Day'] != 'Finals']
    return team_df

@st.cache_data(ttl=3600)
def load_data(sheet_url: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    if sheet_url == None or sheet_url.strip() == "":
        return pd.DataFrame(), pd.DataFrame()
    else:
        try:
            df = pd.read_csv(sheet_url)
            df = _explode_raw_form_data(df)
            df = _clean_raw_data(df)

            # Sort by timestamp (if available) or Races/Wins to keep the best data
            sort_cols = ['Clean_Races', 'Clean_Wins']
            if 'Clean_Timestamp' in df.columns:
                # Convert timestamp to datetime for accurate sorting
                df['Clean_Timestamp'] = pd.to_datetime(df['Clean_Timestamp'], errors='coerce')
                sort_cols.insert(0, 'Clean_Timestamp')
                
            df = df.sort_values(by=sort_cols, ascending=False)
            
            # --- CRITICAL FIX: AGGRESSIVE DEDUPLICATION ---
            # We assume one submission per player per round/day is the valid one.
            # We drop duplicates based on Player + Round + Day + Uma Name
            # This keeps the "latest" or "most complete" entry for that specific slot.
            subset_cols = ['Clean_IGN', 'Round', 'Day', 'Clean_Uma']
            df = df.drop_duplicates(subset=subset_cols, keep='first')

            df = anonymize_players(df)
            team_df = _process_teams(df)
            
            # --- DOUBLE CHECK: Deduplicate Teams ---
            # Ensure we don't have multiple team entries for the same player/round/day in the final team_df
            team_df = team_df.drop_duplicates(subset=['Clean_IGN', 'Round', 'Day'], keep='first')
            
            return df, team_df

        except Exception as e:
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
    calc_height = n_items * per_item
    return max(min_height, calc_height)

# --- SHARED FILTER WIDGET ---
def render_filters(df):
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
            
    if sel_group: df = df[df['Clean_Group'].isin(sel_group)]
    if sel_round: df = df[df['Round'].isin(sel_round)]
    if sel_day: df = df[df['Day'].isin(sel_day)]
    
    return df


@st.cache_data(ttl=300) 
def load_ocr_data(parquet_file):
    try:
        if not os.path.exists(parquet_file):
            return pd.DataFrame()
            
        df = pd.read_parquet(parquet_file)
        string_cols = df.select_dtypes(include=['object']).columns
        for col in string_cols:
            df[col] = df[col].apply(sanitize_text)
        
        df.dropna(subset=['name'], inplace=True)
        
        stat_cols = ['Speed', 'Stamina', 'Power', 'Guts', 'Wit', 'score']
        for col in stat_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                df[col] = df[col].fillna(df[col].median())
                df[col] = df[col].astype(int)

        text_cols = ['rank', 'skills', 'Turf', 'Dirt', 'Sprint', 'Mile', 'Medium', 'Long'] 
        for col in text_cols:
            if col in df.columns:
                df[col] = df[col].fillna('Unknown')
                
        for col in stat_cols:
             if col in df.columns:
                df[col] = df[col].clip(upper=2000)

        return df
    except Exception as e:
        st.error(f"Error loading Parquet: {e}")
        return pd.DataFrame()

# --- LOAD FINALS DATA ---
@st.cache_data
def load_finals_data(config_item: dict):
    """
    Universal loader for Finals with Strict Deduplication and Style Normalization.
    """
    df_auto = pd.DataFrame()
    df_csv_exploded = pd.DataFrame()
    raw_dfs = {} 
    
    # ==========================================
    # 1. LOAD AUTOMATED PARQUETS
    # ==========================================
    if config_item.get('is_multipart_parquet', False):
        parts = config_item.get('finals_parts', {})
        try:
            p_stat = parts.get("statsheet")
            p_pod = parts.get("podium")
            p_deck = parts.get("deck")
            
            df_stat = pd.read_parquet(p_stat) if p_stat and os.path.exists(p_stat) else pd.DataFrame()
            df_pod = pd.read_parquet(p_pod) if p_pod and os.path.exists(p_pod) else pd.DataFrame()
            df_deck = pd.read_parquet(p_deck) if p_deck and os.path.exists(p_deck) else pd.DataFrame()
            
            if 'row' in df_stat.columns and 'row_id' not in df_stat.columns:
                df_stat = df_stat.rename(columns={'row': 'row_id'})

            # Deduplicate
            if not df_stat.empty and 'row_id' in df_stat.columns:
                df_stat = df_stat.drop_duplicates(subset=['row_id'])
            if not df_pod.empty and 'row_id' in df_pod.columns:
                df_pod = df_pod.drop_duplicates(subset=['row_id'])
            if not df_deck.empty and 'row_id' in df_deck.columns:
                df_deck = df_deck.drop_duplicates(subset=['row_id'])

            raw_dfs['statsheet'] = df_stat
            raw_dfs['podium'] = df_pod
            raw_dfs['deck'] = df_deck
            
            # Merge
            if not df_pod.empty:
                df_auto = df_pod
                if not df_stat.empty:
                    if 'row_id' in df_auto.columns and 'row_id' in df_stat.columns:
                        df_auto = pd.merge(df_auto, df_stat, on='row_id', how='inner', suffixes=('', '_stat'))
                    else:
                        st.warning("Merge fallback: Concatenating.")
                        df_auto = pd.concat([df_auto.reset_index(drop=True), df_stat.reset_index(drop=True)], axis=1)

                if not df_deck.empty:
                    if 'row_id' in df_deck.columns and 'row_id' in df_auto.columns:
                        df_deck_clean = df_deck.drop(columns=['id', 'is_user'], errors='ignore')
                        df_auto = pd.merge(df_auto, df_deck_clean, on='row_id', how='left')
                
                df_auto = df_auto.loc[:, ~df_auto.columns.duplicated()]
                df_auto = _normalize_libra_columns(df_auto)
                df_auto['Source'] = 'Automated'
                df_auto['Finals_Group'] = "A Finals" 
                
        except Exception as e:
            st.error(f"Error merging Libra Parquets: {e}")
            
    else:
        # Legacy
        pq_path = config_item.get('finals_parquet')
        if pq_path and os.path.exists(pq_path):
            try:
                df_auto = pd.read_parquet(pq_path)
                df_auto['Source'] = 'Automated'
                rename_map = {'name': 'Clean_Uma', 'rank': 'Result', 'time': 'Run_Time_Str'}
                df_auto.rename(columns=rename_map, inplace=True)
                if 'Clean_Uma' in df_auto.columns:
                    df_auto['Clean_Uma'] = df_auto['Clean_Uma'].apply(lambda x: smart_match_name(x, ORIGINAL_UMAS))
                if 'Result' in df_auto.columns:
                     df_auto['Is_Winner'] = df_auto['Result'].apply(lambda x: 1 if str(x) in ['1', '1st'] else 0)
                # Apply Style Normalization to legacy too
                if 'Clean_Style' not in df_auto.columns and 'style' in df_auto.columns:
                    df_auto['Clean_Style'] = df_auto['style']
                if 'Clean_Style' in df_auto.columns:
                    df_auto['Clean_Style'] = df_auto['Clean_Style'].apply(_normalize_style)
                    
                df_auto['Finals_Group'] = "A Finals"
                raw_dfs['legacy_parquet'] = df_auto
            except Exception as e:
                st.error(f"Error loading Legacy Parquet: {e}")

    # ==========================================
    # 2. IDENTIFY AUTOMATED USERS
    # ==========================================
    auto_ign_set = set()
    if not df_auto.empty and 'Clean_IGN' in df_auto.columns:
        auto_ign_set = set(df_auto['Clean_IGN'].astype(str).str.lower().str.strip().unique())

    # ==========================================
    # 3. LOAD MANUAL CSV
    # ==========================================
    csv_path = config_item.get('finals_csv')
    
    if csv_path and os.path.exists(csv_path):
        try:
            raw_csv = pd.read_csv(csv_path)
            raw_dfs['manual_csv'] = raw_csv 
            
            if 'A or B Finals?' in raw_csv.columns:
                raw_csv = raw_csv.dropna(subset=['A or B Finals?'])
            
            processed_rows = []
            for _, row in raw_csv.iterrows():
                ign_raw = str(row.get('Player IGN', 'Unknown'))
                
                if ign_raw.lower().strip() in auto_ign_set:
                    continue
                
                group = row.get('A or B Finals?', 'Unknown')
                
                for i in range(1, 4):
                    uma_col = f"Finals - Team Comp - Uma {i} - Name"
                    style_col = f"Finals - Team Comp - Uma {i} - Running Style"
                    
                    if uma_col in raw_csv.columns:
                        uma_name = row.get(uma_col)
                        raw_style = row.get(style_col, 'Unknown')
                        
                        if pd.notna(uma_name) and str(uma_name).strip() != "":
                            clean_name = smart_match_name(str(uma_name), ORIGINAL_UMAS)
                            # Normalize Style Here
                            clean_style = _normalize_style(raw_style)
                            
                            processed_rows.append({
                                'Clean_Uma': clean_name,
                                'Clean_Style': clean_style,
                                'Clean_IGN': ign_raw,
                                'Finals_Group': group,
                                'Source': 'Manual',
                                'Is_Winner': 0, 
                                'Result': np.nan,
                                'Skill_Count': 0
                            })
            
            if processed_rows:
                df_csv_exploded = pd.DataFrame(processed_rows)
                
        except Exception as e:
            st.error(f"Error loading CSV: {e}")

    # ==========================================
    # 4. COMBINE
    # ==========================================
    combined_df = pd.concat([df_auto, df_csv_exploded], ignore_index=True)
    
    return combined_df, raw_dfs
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