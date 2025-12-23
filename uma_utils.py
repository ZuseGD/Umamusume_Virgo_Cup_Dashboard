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
    'modeBarButtonsToRemove': ['sendDataToCloud', 'lasso2d', 'select2d', 'zoom2d', 'pan2d'],
    'responsive': True
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
    # ... (Add other canonicals as needed)
    "Special Week",  "Silence Suzuka", "Tokai Teio",
    "Fuji Kiseki",  "Hishi Amazon",
    "T.M. Opera O", "Narita Brian", 
    "Curren Chan",  "Agnes Digital",  "Seiun Sky", 
    "Tamamo Cross",  "Fine Motion",  "Biwa Hayahide", 
    "Mayano Top Gun", "Manhattan Cafe", "Mihono Bourbon", 
    "Mejiro Ryan",  "Hishi Akebono", "Yukino Bijin", "Rice Shower", 
    "Ines Fujin",  "Agnes Tachyon",  "Admire Vega", "Inari One", 
    "Winning Ticket", "Air Groove", 
    "Matikanefukukitaru",  "Meisho Doto",  "Mejiro Dober", 
    "Nice Nature",  "King Halo",  "Machikane Tannhauser", "Ikuno Dictus",
    "Mejiro Palmer", "Daitaku Helios", "Twin Turbo", "Satono Diamond", "Kitasan Black", 
    "Sakura Chiyono O", "Sirius Symboli", "Mejiro Ardan", "Yaeno Muteki", "Tsurumaru Tsuyoshi",
    "Mejiro Bright", "Sakura Bakushin O",  "Shinko Windy", "Agnes Pearl", "Sweep Tosho",
    "Nishino Flower", "Super Creek",  "Bamboo Memory", 
    "Biko Pegasus", "Marvelous Sunday", "Tosen Jordan",  "Nakayama Festa", "Narita Taishin", 
    "Hishi Miracle", "Neo Universe", "Tap Dance City", "Jungle Pocket", "Copano Rickey",
    "Hokko Tarumae", "Wonder Acosta", "Symboli Kris S", "Tanino Gimlet", "Daiichi Ruby", "K.S. Miracle", "Aston Machan",
    "Satono Crown", "Cheval Grand", "Vivilos", "Dantsu Flame", "Air Shakur", "Gold City", 
    "Eishin Flash", "Smart Falcon", "Zenno Rob Roy"
]

# 2. VARIANT MAP (The "Detectors")
# Maps unique keywords (lowercase) to the Canonical Name.
# Keys should be specific enough not to match the Original accidentally.
VARIANT_MAP = {
    # Festival Alts
    "archer": "Symboli Rudolf (Festival)",
    "moonlight": "Symboli Rudolf (Festival)",
    "festival rudolf": "Symboli Rudolf (Festival)",
    "autumn cosmos": "Gold City (Festival)",
    "cosmos": "Gold City (Festival)",
    
    # Summer
    "swimsuit maru": "Maruzensky (Summer)",
    "summer night": "Maruzensky (Summer)",
    "hot☆summer": "Maruzensky (Summer)", 
    "happy heart": "Special Week (Summer)",
    "hopp'n": "Special Week (Summer)",

    # Matikane Fukukitaru
    "lucky tidings": "Matikanefukukitaru (Full Armor)",
    "lucky": "Matikanefukukitaru (Full Armor)",

    # Oguri Cap
    "christmas oguri": "Oguri Cap (Christmas)",
    "xmas oguri": "Oguri Cap (Christmas)",
    "claus": "Oguri Cap (Christmas)", # Title: [Miracle of the White Star Claus]
    
    # Gold Ship
    "summer golshi": "Gold Ship (Summer)",
    "run! run!": "Gold Ship (Summer)", # Title keyword
    
    # Anime Versions
    "end of the skies": "Mejiro McQueen (Anime)",
    "beyond the horizon": "Tokai Teio (Anime)",

    # Fantasy Versions
    "kukulkan": "El Condor Pasa (Fantasy)", 
    "monk el": "El Condor Pasa (Fantasy)",
    "saintly jade": "Grass Wonder (Fantasy)",

    # Hallloween Variants
    "halloween digital": "Agnes Digital (Halloween)",
    "vampire": "Rice Shower (Halloween)",
    "chiffon-wrapped": "Super Creek (Halloween)",
    "mummy": "Super Creek (Halloween)",

    # Wedding Variants
    "sunlight bouquet": "Mayano Top Gun (Wedding)",
    "sunlight": "Mayano Top Gun (Wedding)",
    "quercus civilis": "Air Groove (Wedding)",
    "quercus": "Air Groove (Wedding)",

    
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

def hybrid_merge_entries(df_ocr, df_manual):
    """
    Merges OCR data with Manual data using a Cascading 3-Pass Strategy + Smart Fill.
    
    1. Pass 1 (Name Match): Matches (IGN + Horse). High precision.
    2. Pass 2 (ID Match): Matches (Row ID + Horse). Fixes OCR IGN errors.
    3. Pass 3 (Winner Fallback): Matches (Row ID) of Manual WINNERS to OCR data.
       - This links 'Unknown' OCR stats (like Aaaa's) to the Winner of the CSV row.
       - CSV Losers are ignored for merging (stats blank) but kept as Orphans (count preserved).
    """
    # 1. Handle Empty inputs
    if df_ocr.empty and df_manual.empty: return pd.DataFrame()
    if df_ocr.empty: return df_manual
    if df_manual.empty: return df_ocr
    
    # 2. Normalize Keys
    if 'Clean_IGN' in df_ocr.columns:
        df_ocr['join_ign'] = df_ocr['Clean_IGN'].astype(str).str.lower().str.strip()
    else:
        df_ocr['join_ign'] = "unknown"

    if 'Clean_IGN' in df_manual.columns:
        df_manual['join_ign'] = df_manual['Clean_IGN'].astype(str).str.lower().str.strip()
    else:
        df_manual['join_ign'] = "unknown"
        
    # Ensure types
    if 'row_id' in df_manual.columns: df_manual['row_id'] = pd.to_numeric(df_manual['row_id'], errors='coerce')
    if 'row_id' in df_ocr.columns: df_ocr['row_id'] = pd.to_numeric(df_ocr['row_id'], errors='coerce')

    # --- CASCADING MERGE LOGIC ---
    keys_p1 = ['join_ign', 'Clean_Uma']
    keys_p2 = ['row_id', 'Clean_Uma']
    # Pass 3 key is just row_id, but we apply special filtering logic below
    
    # Protected Keys (Prevent suffixing)
    all_keys = list(set(keys_p1 + keys_p2 + ['row_id', '_m_idx', '_o_idx']))
    
    def suffix_df(df, suffix):
        rename_map = {c: f"{c}{suffix}" for c in df.columns if c not in all_keys}
        return df.rename(columns=rename_map)
    
    df_manual = df_manual.copy()
    df_ocr = df_ocr.copy()
    
    # Track indices explicitly
    df_manual['_m_idx'] = df_manual.index
    df_ocr['_o_idx'] = df_ocr.index
    
    man_s = suffix_df(df_manual, '_manual')
    ocr_s = suffix_df(df_ocr, '_ocr')
    
    # PASS 1: IGN + Horse Name
    m1 = pd.merge(man_s, ocr_s, on=keys_p1, how='inner')
    
    # Leftovers 1
    used_m = m1['_m_idx'].unique()
    used_o = m1['_o_idx'].unique()
    man_rem1 = man_s[~man_s['_m_idx'].isin(used_m)]
    ocr_rem1 = ocr_s[~ocr_s['_o_idx'].isin(used_o)]
    
    # PASS 2: Row ID + Horse Name
    m2 = pd.merge(man_rem1, ocr_rem1, on=keys_p2, how='inner')
    
    # Leftovers 2
    used_m2 = np.concatenate([used_m, m2['_m_idx'].unique()]) if not m2.empty else used_m
    used_o2 = np.concatenate([used_o, m2['_o_idx'].unique()]) if not m2.empty else used_o
    man_rem2 = man_s[~man_s['_m_idx'].isin(used_m2)]
    ocr_rem2 = ocr_s[~ocr_s['_o_idx'].isin(used_o2)]
    
    # PASS 3: Row ID -> MANUAL WINNER ONLY
    # We filter the Manual leftovers to only include Winners. 
    # This ensures we attach the OCR stats to the Winner, avoiding "Alice/Bob" collisions on loser rows.
    # Non-winners are implicitly skipped here and fall through to Orphans (Count kept, Stats empty).
    
    # Check for Is_Winner column existence
    if 'Is_Winner_manual' in man_rem2.columns:
        man_winners = man_rem2[man_rem2['Is_Winner_manual'] == 1]
    else:
        # Fallback if column missing (unlikely), treat all as candidates
        man_winners = man_rem2
        
    m3 = pd.merge(man_winners, ocr_rem2, on=['row_id'], how='inner')
    
    # Dedupe Pass 3 (If OCR has multiple rows for same ID, pick first match to be safe)
    m3 = m3.drop_duplicates(subset=['_m_idx'])
    m3 = m3.drop_duplicates(subset=['_o_idx'])
    
    # Orphans
    used_m3 = np.concatenate([used_m2, m3['_m_idx'].unique()]) if not m3.empty else used_m2
    used_o3 = np.concatenate([used_o2, m3['_o_idx'].unique()]) if not m3.empty else used_o2
    
    man_orphans = man_s[~man_s['_m_idx'].isin(used_m3)]
    ocr_orphans = ocr_s[~ocr_s['_o_idx'].isin(used_o3)]
    
    # Combine
    merged = pd.concat([m1, m2, m3, man_orphans, ocr_orphans], ignore_index=True)
    merged.drop(columns=['_m_idx', '_o_idx'], inplace=True, errors='ignore')
    
    # --- SMART FILL ---
    def smart_fill_column(df, base_col, primary_suffix, secondary_suffix):
        col_p = f"{base_col}{primary_suffix}"
        col_s = f"{base_col}{secondary_suffix}"
        invalid = ['Unknown', 'unknown', 'nan', '', 'None']
        
        if col_p in df.columns: s_p = df[col_p].replace(invalid, np.nan)
        else: s_p = pd.Series(np.nan, index=df.index)
            
        if col_s in df.columns: s_s = df[col_s].replace(invalid, np.nan)
        else: s_s = pd.Series(np.nan, index=df.index)
            
        filled = s_p.fillna(s_s)
        if base_col in df.columns: filled = filled.fillna(df[base_col])
        return filled

    # Coalesce Columns (OCR Priority for Data)
    all_cols = ['Finals_Group', 'League', 'Post', 'Result', 
                'Clean_IGN', 'Clean_Uma', 'Clean_Style', 
                'Speed', 'Stamina', 'Power', 'Guts', 'Wit', 'Score', 'Rank', 
                'Skill_List', 'Skill_Count', 'Aptitude_Dist', 'Aptitude_Surface', 'Aptitude_Style',
                'Run_Time', 'Run_Time_Str', 'is_user', 'Is_Winner']

    for col in all_cols:
        merged[col] = smart_fill_column(merged, col, '_ocr', '_manual')

    # Fix Types
    merged['is_user'] = merged['is_user'].fillna(0).astype(int)
    merged['Is_Winner'] = merged['Is_Winner'].fillna(0)

    # Recover Deck
    for col in merged.columns:
        if col.endswith('_ocr'):
            base_name = col[:-4]
            if base_name not in merged.columns:
                merged[base_name] = merged[col]

    drop_suffixes = [c for c in merged.columns if c.endswith('_ocr') or c.endswith('_manual')]
    merged.drop(columns=drop_suffixes, inplace=True, errors='ignore')
    
    # Safety Net for Metadata
    for col in ['Finals_Group', 'League']:
        if col not in merged.columns: merged[col] = "Unknown"

    return merged

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
    if pd.isna(name) or name == "": return "Unknown Uma Name"
    
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

@st.cache_data
def load_finals_data(config_item: dict):
    combined_df = pd.DataFrame()
    df_auto = pd.DataFrame()
    df_csv_exploded = pd.DataFrame()
    
    # 1. LOAD AUTOMATED PARQUETS
    if config_item.get('is_multipart_parquet', False):
        parts = config_item.get('finals_parts', {})
        try:
            p_stat = parts.get("statsheet")
            p_pod = parts.get("podium")
            p_deck = parts.get("deck")
            
            def get_cte_info(path):
                try:
                    df_schema = duckdb.sql(f"DESCRIBE SELECT * FROM read_parquet('{path}') LIMIT 0").df()
                    cols = df_schema['column_name'].tolist()
                    lower_cols = [c.lower() for c in cols]
                    sel_stmt = "*"
                    if 'row' in lower_cols and 'row_id' not in lower_cols: sel_stmt = "*, row AS row_id"
                    return sel_stmt, cols, lower_cols
                except: return "*", [], []

            def coalesce_col(target_alias, candidates, available_maps):
                valid_sources = []
                for alias, pattern in candidates:
                    cols = available_maps.get(alias, [])
                    found = None
                    for c in cols:
                        if c.lower() == pattern.lower(): found = c; break
                    if found: valid_sources.append(f"{alias}.\"{found}\"")
                if not valid_sources: return f"NULL as {target_alias}"
                return f"COALESCE({', '.join(valid_sources)}) as {target_alias}"

            def safe_col(table_alias, col_name, target_alias, available_cols):
                for c in available_cols:
                    if c.lower() == col_name.lower(): return f"{table_alias}.\"{c}\" as {target_alias}"
                return f"NULL as {target_alias}"

            sel_stat, cols_stat, _ = get_cte_info(p_stat)
            sel_pod, cols_pod, _ = get_cte_info(p_pod)
            sel_deck, cols_deck, _ = get_cte_info(p_deck)
            col_map = {'p': cols_pod, 's': cols_stat, 'd': cols_deck}

            select_parts = []
            select_parts.append(coalesce_col('Clean_Uma', [('p', 'trainee_name'), ('s', 'name'), ('d', 'name')], col_map))
            select_parts.append(coalesce_col('Clean_IGN', [('p', 'trainer_name'), ('s', 'trainer_name')], col_map))
            select_parts.append("COALESCE(p.row_id, s.row_id, d.row_id) as row_id")

            # Explicit Columns
            select_parts.append(safe_col('p', 'placement', 'Result', cols_pod))
            select_parts.append(safe_col('p', 'post', 'Post', cols_pod))
            select_parts.append(safe_col('p', 'time', 'Run_Time_Str', cols_pod))
            select_parts.append(safe_col('p', 'style', 'Clean_Style', cols_pod))

            select_parts.append(safe_col('s', 'skills', 'Skill_List', cols_stat))
            select_parts.append(safe_col('s', 'skill_count', 'Skill_Count', cols_stat))
            for stat in ['Speed', 'Stamina', 'Power', 'Guts', 'Wit', 'score', 'rank']:
                select_parts.append(safe_col('s', stat, stat.capitalize(), cols_stat))
            
            # Deck Columns
            for i in range(1, 7):
                cname = f"card{i}_name"
                select_parts.append(safe_col('d', cname, cname, cols_deck))
                clevel = f"card{i}_level"
                select_parts.append(safe_col('d', clevel, clevel, cols_deck))

            target_dist = config_item.get('aptitude_dist', 'Long') 
            target_surf = config_item.get('aptitude_surf', 'Turf')
            select_parts.append(safe_col('s', target_dist, 'Aptitude_Dist', cols_stat))
            select_parts.append(safe_col('s', target_surf, 'Aptitude_Surface', cols_stat))

            needed_apts = ['Front', 'Pace', 'Late', 'End']
            lower_stat_cols = [c.lower() for c in cols_stat]
            has_apts = all(n.lower() in lower_stat_cols for n in needed_apts)
            if has_apts and 'style' in [c.lower() for c in cols_pod]:
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

            place_col = None
            for c in cols_pod:
                if c.lower() == 'placement': place_col = c; break
            if place_col:
                select_parts.append(f"""
                CASE 
                    WHEN p."{place_col}" IS NULL THEN NULL
                    WHEN try_cast(p."{place_col}" as INTEGER) = 1 THEN 1 
                    WHEN starts_with(lower(cast(p."{place_col}" as VARCHAR)), '1') THEN 1
                    ELSE 0 
                END as Is_Winner
                """)
            else:
                select_parts.append("NULL as Is_Winner")

            p_is_user_col = None
            for c in cols_pod:
                if c.lower() == 'is_user': p_is_user_col = c; break
            
            p_check = "NULL"
            if p_is_user_col: p_check = f"TRY_CAST(p.\"{p_is_user_col}\" AS INTEGER)"

            is_user_logic = f"""
            CASE 
                WHEN {p_check} IS NOT NULL THEN {p_check}
                WHEN s.row_id IS NOT NULL THEN 1
                WHEN d.row_id IS NOT NULL THEN 1
                ELSE 0
            END as is_user
            """
            select_parts.append(is_user_logic)

            if any(c.lower() == 'rank' for c in cols_stat):
                league_logic = """
                CASE 
                    WHEN s.rank IS NOT NULL AND (
                        starts_with(upper(s.rank), 'B') OR 
                        starts_with(upper(s.rank), 'C') OR 
                        starts_with(upper(s.rank), 'D') OR
                        starts_with(upper(s.rank), 'E') OR
                        starts_with(upper(s.rank), 'F') OR
                        starts_with(upper(s.rank), 'G')
                    ) THEN 'Open'
                    WHEN s.rank IS NOT NULL THEN 'Graded'
                    ELSE 'Unknown' 
                END as League_Inferred
                """
                select_parts.append(league_logic)
            else:
                select_parts.append("'Unknown' as League_Inferred")

            select_string = ",\n                ".join(select_parts)
            
            query = f"""
            WITH stat_data AS ( SELECT {sel_stat} FROM read_parquet('{p_stat}') ),
                 pod_data AS ( SELECT {sel_pod} FROM read_parquet('{p_pod}') ),
                 deck_data AS ( SELECT {sel_deck} FROM read_parquet('{p_deck}') )
            SELECT 
                {select_string},
                'Automated' as Source
            FROM pod_data p
            FULL JOIN stat_data s ON p.row_id = s.row_id
            FULL JOIN deck_data d ON COALESCE(p.row_id, s.row_id) = d.row_id
            """
            
            df_auto = duckdb.query(query).to_df()
            
            # --- FIX: ROBUST METADATA & ERROR HANDLING ---
            if df_auto.empty:
                # Initialize columns to prevent KeyErrors downstream
                df_auto['Finals_Group'] = pd.Series(dtype='object')
                df_auto['League'] = pd.Series(dtype='object')
                df_auto['uma_slot'] = pd.Series(dtype='int')
            else:
                if 'Run_Time_Str' in df_auto.columns:
                    df_auto['Run_Time'] = df_auto['Run_Time_Str'].apply(_parse_run_time_to_seconds)
                
                if 'Clean_Style' in df_auto.columns:
                    df_auto['Clean_Style'] = df_auto['Clean_Style'].apply(lambda x: _normalize_style(x) if pd.notna(x) else "Unknown")
                
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
                
                if 'is_user' in df_auto.columns:
                     df_auto['is_user'] = pd.to_numeric(df_auto['is_user'], errors='coerce').fillna(0).astype(int)

                # Metadata Resolution
                if 'Clean_IGN' in df_auto.columns:
                    ign_to_team_auto = df_auto.groupby('Clean_IGN')['Clean_Uma'].apply(lambda x: frozenset([i for i in x if pd.notna(i)])).to_dict()
                else:
                    ign_to_team_auto = {}

                def resolve_metadata(row):
                    # Default logic placeholder (requires external map context, using Unknown for safety)
                    res_group = "Unknown"
                    res_league = row.get('League_Inferred', 'Unknown')
                    return pd.Series([res_group, res_league])

                meta_cols = df_auto.apply(resolve_metadata, axis=1)
                df_auto['Finals_Group'] = meta_cols[0]
                df_auto['League'] = meta_cols[1]
                
                if 'row_id' in df_auto.columns:
                    df_auto['uma_slot'] = df_auto.groupby('row_id').cumcount()

        except Exception as e:
            st.error(f"Error loading DuckDB Parquets: {e}")
    else:
        pass

    csv_path = config_item.get('finals_csv', None)

    # 3. COMBINE WITH CSV
    if csv_path and os.path.exists(csv_path):
        try:
            raw_csv = pd.read_csv(csv_path)
            
            if 'A or B Finals?' in raw_csv.columns:
                 raw_csv = raw_csv.dropna(subset=['A or B Finals?'])
            
            league_col = find_column(raw_csv, ['league', 'selection'])
            winner_type_col = find_column(raw_csv, ["ownumaoropponent", "winnerown"]) 
            winner_style_col = find_column(raw_csv, ["winnerrunningstyle", "winnerstyle"])
            winner_name_col = find_column(raw_csv, ["winnername"])
            result_col = find_column(raw_csv, ['final result', 'finals result', 'result'])
            
            processed_rows = []
            
            for i, (_, row) in enumerate(raw_csv.iterrows()):
                row_id = i + 2
                ign_raw = str(row.get('Player IGN', 'Unknown'))
                
                group = row.get('A or B Finals?', 'Unknown')
                league = "Graded"
                if league_col:
                    raw_league = str(row.get(league_col, 'Graded'))
                    league = "Open" if "open" in raw_league.lower() else "Graded"
                
                w_type = str(row.get(winner_type_col, '')).lower()
                w_name_raw = row.get(winner_name_col)
                w_style_raw = row.get(winner_style_col)
                
                w_clean_name = "Unknown"
                if pd.notna(w_name_raw): w_clean_name = smart_match_name(str(w_name_raw), ORIGINAL_UMAS)
                
                w_clean_style = "Unknown"
                if pd.notna(w_style_raw): w_clean_style = _normalize_style(w_style_raw)

                row_result_str = str(row.get(result_col, '')).lower().strip()
                is_result_1st = row_result_str in ['1st', '1', 'first', 'winner', 'win']

                team_data = []
                for k in range(1, 4):
                    uma_col = f"Finals - Team Comp - Uma {k} - Name"
                    style_col = f"Finals - Team Comp - Uma {k} - Running Style"
                    if uma_col in raw_csv.columns:
                        uname = row.get(uma_col)
                        ustyle = row.get(style_col, 'Unknown')
                        if pd.notna(uname) and str(uname).strip() != "":
                            team_data.append({
                                'clean_name': smart_match_name(str(uname), ORIGINAL_UMAS),
                                'clean_style': _normalize_style(ustyle)
                            })
                        else:
                            team_data.append(None)
                    else:
                        team_data.append(None)

                # Determine Winner Index
                winner_idx = -1
                
                # 1. Explicit "Own" win flag check
                is_explicit_own = 'own' in w_type
                
                if is_explicit_own:
                    for k, u in enumerate(team_data):
                        if u and u['clean_name'] == w_clean_name and w_clean_name != "Unknown":
                            winner_idx = k; break
                    if winner_idx == -1 and w_clean_name == "Unknown" and w_clean_style != "Unknown":
                        for k, u in enumerate(team_data):
                            if u and u['clean_style'] == w_clean_style:
                                winner_idx = k; break
                    if winner_idx == -1:
                        for k, u in enumerate(team_data):
                            if u: winner_idx = k; break

                # 2. Implied "1st" check
                elif 'opponent' not in w_type and is_result_1st:
                    for k, u in enumerate(team_data):
                        if u and u['clean_name'] == w_clean_name and w_clean_name != "Unknown":
                            winner_idx = k; break
                    if winner_idx == -1:
                        for k, u in enumerate(team_data):
                            if u: winner_idx = k; break

                # --- PROCESS TEAM UMAS (1-3) ---
                for k in range(3):
                    u_data = team_data[k]
                    if u_data:
                        is_win = 1 if k == winner_idx else 0
                        result = 1 if k == winner_idx else np.nan
                        
                        processed_rows.append({
                            'row_id': row_id,
                            'uma_slot': k,
                            'Clean_Uma': u_data['clean_name'], 
                            'Clean_Style': u_data['clean_style'], 
                            'Clean_IGN': ign_raw,
                            'Finals_Group': group, 
                            'League': league, 
                            'Source': 'Manual',
                            'Is_Winner': is_win, 
                            'Result': result, 
                            'Skill_Count': 0,
                            'is_user': 1 
                        })

                # --- PROCESS OPPONENT WINNER ---
                if 'opponent' in w_type and w_clean_name != "Unknown":
                    processed_rows.append({
                        'row_id': row_id,
                        'uma_slot': -1,
                        'Clean_Uma': w_clean_name,
                        'Clean_Style': w_clean_style,
                        'Clean_IGN': f"{ign_raw} (Opponent)", 
                        'Finals_Group': group,
                        'League': league,
                        'Source': 'Manual_Opponent',
                        'Is_Winner': 1,
                        'Result': 1,
                        'Skill_Count': 0,
                        'is_user': 0 
                    })

            if processed_rows: df_csv_exploded = pd.DataFrame(processed_rows)
        except Exception as e: st.error(f"Error loading CSV: {e}")

    # --- HYBRID MERGE (Manual + OCR) ---
    combined_df = hybrid_merge_entries(df_auto, df_csv_exploded)
    raw_dfs = {
        'automated': df_auto,
        'manual_csv': df_csv_exploded
    }
    
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