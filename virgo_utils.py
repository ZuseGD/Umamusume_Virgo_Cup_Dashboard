import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import os
import re
import html
import ast
from typing import Tuple, List, Optional
import duckdb
import difflib

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

# 1. CANONICAL LIST (The "Clean" Names you want to see in the Dashboard)
ORIGINAL_UMAS = [
    # Originals
    "Symboli Rudolf", "Maruzensky", "Oguri Cap", "El Condor Pasa", "Grass Wonder",
    "Mejiro McQueen", "Vodka", "Daiwa Scarlet", "Taiki Shuttle", "Gold Ship",
    
    # Variants (Costumes / Alts)
    "Symboli Rudolf (Festival)",  # The "Archer/Monk" version
    "Maruzensky (Summer)",
    "Oguri Cap (Christmas)",
    "El Condor Pasa (Fantasy)",   # Often called Monk, distinct from Rudolf
    "Grass Wonder (Fantasy)",
    "Mejiro McQueen (Anime)",
    "Gold Ship (Summer)",
    
    # ... (Add other canonicals as needed)
    "Special Week", "Special Week (Summer)", "Silence Suzuka", "Tokai Teio",
    "Fuji Kiseki", "Fuji Kiseki (Dance)", "Hishi Amazon", "Hishi Amazon (Wedding)",
    "T.M. Opera O", "T.M. Opera O (New Year)", "Narita Brian", "Narita Brian (Blaze)", 
    "Curren Chan", "Curren Chan (Wedding)", "Agnes Digital", "Agnes Digital (Halloween)", "Seiun Sky", "Seiun Sky (Dance)",
    "Tamamo Cross", "Tamamo Cross (Festival)", "Fine Motion", "Fine Motion (Wedding)", "Biwa Hayahide", "Biwa Hayahide (Xmas)",
    "Mayano Top Gun", "Mayano Top Gun (Wedding)", "Manhattan Cafe", "Mihono Bourbon", "Mihono Bourbon (Valentine)",
    "Mejiro Ryan", "Mejiro Ryan (Valentine)", "Hishi Akebono", "Yukino Bijin", "Rice Shower", "Rice Shower (Halloween)",
    "Ines Fujin", "Ines Fujin (Valentine)", "Agnes Tachyon", "Agnes Tachyon (Summer)", "Admire Vega", "Inari One", "Inari One (Summer)",
    "Winning Ticket", "Winning Ticket (Steam)", "Air Groove", "Air Groove (Wedding)",
    "Matikanefukukitaru", "Matikanefukukitaru (Full Armor)", "Meisho Doto", "Meisho Doto (Halloween)", "Mejiro Dober", "Mejiro Dober (Camp)",
    "Nice Nature", "Nice Nature (Cheer)", "King Halo", "King Halo (Cheer)", "Machikane Tannhauser", "Ikuno Dictus",
    "Mejiro Palmer", "Daitaku Helios", "Twin Turbo", "Satono Diamond", "Kitasan Black", "Kitasan Black (New Year)",
    "Sakura Chiyono O", "Sakura Chiyono O (Dance)", "Sirius Symboli", "Mejiro Ardan", "Yaeno Muteki", "Tsurumaru Tsuyoshi",
    "Mejiro Bright", "Sakura Bakushin O", "Sakura Bakushin O (New Year)", "Shinko Windy", "Agnes Pearl", "Sweep Tosho",
    "Nishino Flower", "Nishino Flower (Wedding)", "Super Creek", "Super Creek (Halloween)", "Bamboo Memory", "Bamboo Memory (Summer)",
    "Biko Pegasus", "Marvelous Sunday", "Tosen Jordan", "Tosen Jordan (Summer)", "Nakayama Festa", "Narita Taishin", "Narita Taishin (Steam)",
    "Hishi Miracle", "Neo Universe", "Tap Dance City", "Jungle Pocket", "Copano Rickey",
    "Hokko Tarumae", "Wonder Acosta", "Symboli Kris S", "Tanino Gimlet", "Daiichi Ruby", "K.S. Miracle", "Aston Machan",
    "Satono Crown", "Cheval Grand", "Vivilos", "Dantsu Flame", "Air Shakur", "Gold City", "Gold City (New Year)",
    "Eishin Flash", "Eishin Flash (Valentine)", "Karen Chan", "Smart Falcon", "Smart Falcon (Yellow)", "Zenno Rob Roy"
]

# 2. VARIANT MAP (The "Detectors")
# Maps unique keywords (lowercase) to the Canonical Name.
# Keys should be specific enough not to match the Original accidentally.
VARIANT_MAP = {
    # Symboli Rudolf
    "archer": "Symboli Rudolf (Festival)",
    "moonlight": "Symboli Rudolf (Festival)",
    "festival rudolf": "Symboli Rudolf (Festival)",
    "monk rudolf": "Symboli Rudolf (Festival)",
    
    # Maruzensky
    "swimsuit maru": "Maruzensky (Summer)",
    "summer maru": "Maruzensky (Summer)",
    "supersonic": "Maruzensky (Summer)", # Title: [Supersonic]
    
    # Oguri Cap
    "christmas oguri": "Oguri Cap (Christmas)",
    "xmas oguri": "Oguri Cap (Christmas)",
    "claus": "Oguri Cap (Christmas)", # Title: [Miracle of the White Star Claus]
    
    # Gold Ship
    "summer golshi": "Gold Ship (Summer)",
    "run! run!": "Gold Ship (Summer)", # Title keyword
    
    # Mejiro McQueen
    "endless": "Mejiro McQueen (Endless)",
    "summer mcqueen": "Mejiro McQueen (Summer)",
    "ripple": "Mejiro McQueen (Summer)", # Title: [Ripple in the Blue]
    
    # El Condor Pasa
    "fantasy": "El Condor Pasa (Fantasy)", 
    "monk el": "El Condor Pasa (Fantasy)",

    "[beyond the horizon] tokai teio": "Tokai Teio (Anime)",
    "[Hopp'n♪Happy Heart] Special Week (Summer)": "Special Week (Summer)",
    
    # Add any other specific titles from your CSVs here
    # Format: "unique keyword found in csv": "Target Canonical Name"
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
    col_map = {
        'trainee_name': 'Clean_Uma', 'trainer_name': 'Clean_IGN', 'placement': 'Result',
        'post': 'Post', 'time': 'Run_Time_Str', 'style': 'Clean_Style', 'skills': 'Skill_List',
        'skill_count': 'Skill_Count', 'Speed': 'Speed', 'Stamina': 'Stamina', 'Power': 'Power', 
        'Guts': 'Guts', 'Wit': 'Wit', 'wisdom': 'Wit', 
        'score': 'Score', 'rank': 'Rank' 
    }
    df = df.rename(columns=col_map)
    
    
    if 'Result' in df.columns:
        df['Result'] = pd.to_numeric(df['Result'], errors='coerce')
        df['Is_Winner'] = df['Result'].apply(lambda x: 1 if x == 1 else 0)
    else: df['Is_Winner'] = 0

    if 'Run_Time_Str' in df.columns:
        df['Run_Time'] = df['Run_Time_Str'].apply(_parse_run_time_to_seconds)

    if 'Clean_Style' in df.columns:
        df['Clean_Style'] = df['Clean_Style'].apply(_normalize_style)

    if 'Skill_List' not in df.columns: df['Skill_List'] = np.empty((len(df), 0)).tolist()
    
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
    
    # --- APTITUDE MAPPING (NEW) ---
    # 1. Distance & Surface (Hardcoded for Libra Cup: Long / Turf)
    if 'Long' in df.columns: 
        df['Aptitude_Dist'] = df['Long']
    if 'Turf' in df.columns: 
        df['Aptitude_Surface'] = df['Turf']

    # 2. Strategy (Dynamic based on the runner's chosen style)
    def get_style_aptitude(row):
        # Normalize style string to check against column names
        style = str(row.get('Clean_Style', '')).lower()
        
        # Check specific strategy columns from schema
        if 'runaway' in style or 'front' in style: return row.get('Front')
        if 'pace' in style: return row.get('Pace')
        if 'late' in style: return row.get('Late')
        if 'end' in style: return row.get('End')
        return None

    # Apply if style columns exist
    if all(col in df.columns for col in ['Front', 'Pace', 'Late', 'End']):
        df['Aptitude_Style'] = df.apply(get_style_aptitude, axis=1)


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

def smart_match_name(name, known_names=ORIGINAL_UMAS):
    """
    Matches a raw name to the known list with Priority Logic.
    1. Check VARIANT_MAP for specific keywords (Archer, Summer, etc.)
    2. Exact Match
    3. Fuzzy Match
    """
    if pd.isna(name) or name == "": return "Unknown"
    
    raw_input = str(name).strip()
    norm_input = raw_input.lower()
    
    # --- PRIORITY 1: VARIANT MAPPING ---
    # Check if any variant keyword exists in the input string
    # e.g. Input: "[Archer by Moonlight] Symboli Rudolf" -> matches "archer" -> Returns "Symboli Rudolf (Festival)"
    for keyword, canonical in VARIANT_MAP.items():
        if keyword in norm_input:
            return canonical

    # --- PRIORITY 2: EXACT MATCH ---
    if raw_input in known_names:
        return raw_input
    
    # --- PRIORITY 3: FUZZY MATCH ---
    # We use a stricter cutoff (0.2) to avoid bad guesses
    matches = difflib.get_close_matches(raw_input, known_names, n=1, cutoff=0.3)
    if matches:
        return matches[0]
        
    return "Unknown"

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


@st.cache_data(ttl=3600) 
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
    combined_df = pd.DataFrame()
    df_auto = pd.DataFrame()
    df_csv_exploded = pd.DataFrame()
    raw_dfs = {} 
    
    # -------------------------------------------------------------
    # 1. BUILD LOOKUP MAPS (Same as before)
    # -------------------------------------------------------------
    ign_group_map = {}
    team_group_map = {}
    ign_league_map = {}
    team_league_map = {}
    
    csv_path = config_item.get('finals_csv')
    if csv_path and os.path.exists(csv_path):
        try:
            temp_csv = pd.read_csv(csv_path)
            group_col = 'A or B Finals?'
            league_col = None
            for col in temp_csv.columns:
                if 'league' in col.lower() or 'selection' in col.lower():
                    league_col = col
                    break
            
            if group_col in temp_csv.columns:
                temp_csv = temp_csv.dropna(subset=[group_col])
                for _, row in temp_csv.iterrows():
                    ign = str(row.get('Player IGN', '')).strip()
                    norm_ign = ign.lower()
                    group_val = str(row.get(group_col, 'B Finals')).strip()
                    league_val = "Graded"
                    if league_col:
                        raw_l = str(row.get(league_col, '')).lower()
                        league_val = "Open" if "open" in raw_l else "Graded"

                    if norm_ign:
                        ign_group_map[norm_ign] = group_val
                        ign_league_map[norm_ign] = league_val
                    
                    umas = []
                    for i in range(1, 4):
                        u = row.get(f"Finals - Team Comp - Uma {i} - Name")
                        if pd.notna(u) and str(u).strip():
                            clean_u = smart_match_name(str(u), ORIGINAL_UMAS)
                            umas.append(clean_u)
                    if umas:
                        team_key = frozenset(umas)
                        team_group_map[team_key] = group_val
                        team_league_map[team_key] = league_val
        except Exception as e:
            print(f"Error building lookup maps: {e}")

    # -------------------------------------------------------------
    # 2. LOAD AUTOMATED PARQUETS (Robust DuckDB)
    # -------------------------------------------------------------
    if config_item.get('is_multipart_parquet', False):
        parts = config_item.get('finals_parts', {})
        try:
            p_stat = parts.get("statsheet")
            p_pod = parts.get("podium")
            p_deck = parts.get("deck")

            
            # --- HELPER 1: Standardize ID Column in CTE ---
            def get_cte_select(path):
                """Returns '*, row as row_id' or '*' depending on schema."""
                try:
                    df_schema = duckdb.sql(f"DESCRIBE SELECT * FROM read_parquet('{path}') LIMIT 0").df()
                    cols = df_schema['column_name'].tolist()
                    if 'row' in cols and 'row_id' not in cols:
                        return "*, row AS row_id", cols
                    return "*", cols
                except:
                    return "*", []

            # --- HELPER 2: Safe Column Selector ---
            def safe_col(table_alias, col_name, target_alias, available_cols):
                """Returns 't.col as target' if exists, else 'NULL as target'."""
                if col_name in available_cols:
                    return f"{table_alias}.{col_name} as {target_alias}"
                return f"NULL as {target_alias}"
            
            # --- HELPER: Case-Insensitive Column Finder ---
            def find_col(target, cols):
                """Returns the actual column name if found (case-insensitive), else None."""
                target_lower = target.lower()
                for c in cols:
                    if str(c).lower() == target_lower:
                        return c
                return None

            # 1. Inspect Files & Build CTE Selects
            sel_stat, cols_stat = get_cte_select(p_stat)
            sel_pod, cols_pod = get_cte_select(p_pod)
            sel_deck, cols_deck = get_cte_select(p_deck)

            # 2. Build Main SELECT List Dynamically
            select_parts = []
            
            # -- PODIUM COLUMNS --
            select_parts.append(safe_col('p', 'trainee_name', 'Clean_Uma', cols_pod))
            select_parts.append(safe_col('p', 'trainer_name', 'Clean_IGN', cols_pod))
            select_parts.append(safe_col('p', 'placement', 'Result', cols_pod))
            select_parts.append(safe_col('p', 'post', 'Post', cols_pod))
            select_parts.append(safe_col('p', 'time', 'Run_Time_Str', cols_pod))
            select_parts.append(safe_col('p', 'style', 'Clean_Style', cols_pod))
            
            # -- STATSHEET COLUMNS --
            # Skills might be in 'skills' or 'skill_list'
            select_parts.append(safe_col('s', 'skills', 'Skill_List', cols_stat))
            select_parts.append(safe_col('s', 'skill_count', 'Skill_Count', cols_stat))
            
            for stat in ['Speed', 'Stamina', 'Power', 'Guts', 'Wit', 'score', 'rank']:
                tgt = stat.capitalize() if stat not in ['score', 'rank'] else stat.capitalize()
                select_parts.append(safe_col('s', stat, tgt, cols_stat))
            

            # -- DECK COLUMNS (Dynamic 1-6) --
            for i in range(1, 7):
                cname = f"card{i}_name"
                if cname in cols_deck:
                    select_parts.append(f"d.{cname}")
                else:
                    select_parts.append(f"NULL as {cname}")
            
            # -- IS_USER (FIX: Check Podium First, then Deck) --
            is_user_pod = find_col('is_user', cols_pod)
            is_user_deck = find_col('is_user', cols_deck)

            # -- APTITUDE COLUMNS (DYNAMIC) --
            # Get targets from config, defaulting to Libra standard if missing
            target_dist = config_item.get('aptitude_dist', 'Long') 
            target_surf = config_item.get('aptitude_surf', 'Turf')

            # Dynamically select the configured columns
            # Maps generic 'Aptitude_Dist' to whatever specific column (e.g. 'Medium') is needed
            select_parts.append(safe_col('s', target_dist, 'Aptitude_Dist', cols_stat))
            select_parts.append(safe_col('s', target_surf, 'Aptitude_Surface', cols_stat))
            
            # -- STYLE APTITUDE (Conditional Logic needs columns to exist) --
            # We wrap the CASE WHEN in a check. If columns don't exist, we just output NULL.
            needed_apts = ['Front', 'Pace', 'Late', 'End']
            if all(c in cols_stat for c in needed_apts) and 'style' in cols_pod:
                style_logic = """
                CASE 
                    WHEN lower(p.style) LIKE '%front%' OR lower(p.style) LIKE '%runaway%' THEN s.Front
                    WHEN lower(p.style) LIKE '%pace%' THEN s.Pace
                    WHEN lower(p.style) LIKE '%late%' THEN s.Late
                    WHEN lower(p.style) LIKE '%end%' THEN s.End
                    ELSE NULL
                END as Aptitude_Style
                """
                select_parts.append(style_logic)
            else:
                select_parts.append("NULL as Aptitude_Style")

            # -- WINNER & LEAGUE LOGIC --
            # FIXED: Robust Winner Check (Handles 1, '1', '1st')
            place_col = find_col('placement', cols_pod)
            if place_col:
                select_parts.append(f"""
                CASE 
                    WHEN try_cast(p.\"{place_col}\" as INTEGER) = 1 THEN 1 
                    WHEN starts_with(lower(cast(p.\"{place_col}\" as VARCHAR)), '1') THEN 1
                    ELSE 0 
                END as Is_Winner
                """)
            else:
                select_parts.append("0 as Is_Winner")
            
            # FIXED: Cast is_user to integer for consistent 1/0/NULL handling
            # (Previously handled in 'DECK COLUMNS' block - update it there)
            # Find the line: select_parts.append(safe_col('d', 'is_user', 'is_user', cols_deck))
            # Replace with:
            if 'is_user' in cols_deck:
                select_parts.append("try_cast(s.is_user as INTEGER) as is_user")
            else:
                select_parts.append("NULL as is_user")

            # League
            if 'rank' in cols_stat:
                league_logic = """
                CASE 
                    WHEN s.rank IS NOT NULL AND (
                        starts_with(upper(s.rank), 'U') OR 
                        starts_with(upper(s.rank), 'S') OR 
                        starts_with(upper(s.rank), 'A')
                    ) THEN 'Graded'
                    ELSE 'Open' 
                END as League_Inferred
                """
                select_parts.append(league_logic)
            else:
                select_parts.append("'Graded' as League_Inferred")

            # Construct Final Query
            select_string = ",\n                ".join(select_parts)
            
            query = f"""
            WITH stat_data AS ( SELECT {sel_stat} FROM read_parquet('{p_stat}') ),
                 pod_data AS ( SELECT {sel_pod} FROM read_parquet('{p_pod}') ),
                 deck_data AS ( SELECT {sel_deck} FROM read_parquet('{p_deck}') )
            SELECT 
                {select_string},
                'Automated' as Source
            FROM pod_data p
            LEFT JOIN stat_data s ON p.row_id = s.row_id
            LEFT JOIN deck_data d ON p.row_id = d.row_id
            """
            
            df_auto = duckdb.query(query).to_df()
            
            # --- POST-PROCESSING ---
            
            if 'Run_Time_Str' in df_auto.columns:
                df_auto['Run_Time'] = df_auto['Run_Time_Str'].apply(_parse_run_time_to_seconds)
            
            if 'Clean_Style' in df_auto.columns:
                df_auto['Clean_Style'] = df_auto['Clean_Style'].apply(lambda x: _normalize_style(x) if pd.notna(x) else "Unknown")
            else:
                df_auto['Clean_Style'] = "Unknown" # Fallback if SQL failed to create it
            
            if 'Clean_Uma' in df_auto.columns:
                unique_names = df_auto['Clean_Uma'].dropna().unique()
                name_map = {name: smart_match_name(name, ORIGINAL_UMAS) for name in unique_names}
                df_auto['Clean_Uma'] = df_auto['Clean_Uma'].map(name_map)
            
            def safe_parse_skills(x):
                if isinstance(x, (np.ndarray, list)): return list(x)
                if isinstance(x, str):
                    try:
                        if x.startswith('['): return ast.literal_eval(x)
                        return [x] 
                    except: return []
                return []
            
            if 'Skill_List' in df_auto.columns:
                df_auto['Skill_List'] = df_auto['Skill_List'].apply(safe_parse_skills)
            else:
                df_auto['Skill_List'] = np.empty((len(df_auto), 0)).tolist()

            # Metadata Matching (Group/League)
            if 'Clean_IGN' in df_auto.columns:
                ign_to_team_auto = df_auto.groupby('Clean_IGN')['Clean_Uma'].apply(lambda x: frozenset([i for i in x if pd.notna(i)])).to_dict()
            else:
                ign_to_team_auto = {}

            def resolve_metadata(row):
                ign = str(row.get('Clean_IGN', '')).strip()
                norm_ign = ign.lower()
                
                res_group = "B Finals"
                res_league = row.get('League_Inferred', 'Graded')
                
                if norm_ign in ign_group_map:
                    res_group = ign_group_map[norm_ign]
                    res_league = ign_league_map.get(norm_ign, res_league)
                    return pd.Series([res_group, res_league])
                
                if ign in ign_to_team_auto:
                    team_set = ign_to_team_auto[ign]
                    if team_set in team_group_map:
                        res_group = team_group_map[team_set]
                        res_league = team_league_map.get(team_set, res_league)
                        return pd.Series([res_group, res_league])

                return pd.Series([res_group, res_league])

            meta_cols = df_auto.apply(resolve_metadata, axis=1)
            df_auto['Finals_Group'] = meta_cols[0]
            df_auto['League'] = meta_cols[1]

        except Exception as e:
            st.error(f"Error loading DuckDB Parquets: {e}")
    else:
        pass

    # 3. COMBINE WITH CSV
    if csv_path and os.path.exists(csv_path):
        try:
            raw_csv = pd.read_csv(csv_path)
            
            if 'A or B Finals?' in raw_csv.columns:
                 raw_csv = raw_csv.dropna(subset=['A or B Finals?'])
            
            league_col = None
            for col in raw_csv.columns:
                if 'league' in col.lower() or 'selection' in col.lower():
                    league_col = col
                    break
            
            processed_rows = []
            auto_ign_set = set(df_auto['Clean_IGN'].astype(str).str.lower().str.strip().unique()) if not df_auto.empty and 'Clean_IGN' in df_auto.columns else set()

            for _, row in raw_csv.iterrows():
                ign_raw = str(row.get('Player IGN', 'Unknown'))
                if ign_raw.lower().strip() in auto_ign_set: continue
                
                group = row.get('A or B Finals?', 'Unknown')
                if league_col:
                    raw_league = str(row.get(league_col, 'Graded'))
                    league = "Open" if "open" in raw_league.lower() else "Graded"
                else:
                    league = "Graded"
                
                for i in range(1, 4):
                    uma_col = f"Finals - Team Comp - Uma {i} - Name"
                    style_col = f"Finals - Team Comp - Uma {i} - Running Style"
                    if uma_col in raw_csv.columns:
                        uma_name = row.get(uma_col)
                        raw_style = row.get(style_col, 'Unknown')
                        if pd.notna(uma_name) and str(uma_name).strip() != "":
                            clean_name = smart_match_name(str(uma_name), ORIGINAL_UMAS)
                            clean_style = _normalize_style(raw_style)
                            processed_rows.append({
                                'Clean_Uma': clean_name, 'Clean_Style': clean_style, 'Clean_IGN': ign_raw,
                                'Finals_Group': group, 'League': league, 'Source': 'Manual',
                                'Is_Winner': 0, 'Result': np.nan, 'Skill_Count': 0
                            })
            if processed_rows: df_csv_exploded = pd.DataFrame(processed_rows)
        except Exception as e: st.error(f"Error loading CSV: {e}")

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