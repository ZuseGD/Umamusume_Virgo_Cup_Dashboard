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
    "leaderboard": """
    **Leaderboard Logic:**
    - **Score Formula:** `Win Rate * log(Total Races + 1)`
    - **Why?** This rewards players who maintain a high win rate over *many* races, rather than someone who went 1/1 (100%).
    """,
    "money": """
    **Spending vs. Performance:**
    - **Box Plot:** The box shows the middle 50% of players. The line in the middle is the median.
    - **Goal:** To visualize if spending more money guarantees a higher win rate (pay-to-win) or if F2P players remain competitive.
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
    - **Metric:** Win rate by strategy (Runaway/Nigeru, Front/Senkou, etc.).
    - **Goal:** Identifies the dominant running style for this specific track.
    """,
    "runaway": """
    **Runaway Impact:**
    - **Hypothesis:** "You need a Runaway (Nigeru) to control the pace."
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

# --- DATA LOADING ---
@st.cache_data(ttl=3600) # Cache for 1 hour
def load_data(sheet_url):
    try:
        df = pd.read_csv(sheet_url)
        
        # 1. SANITIZE
        string_cols = df.select_dtypes(include=['object']).columns
        for col in string_cols: df[col] = df[col].apply(sanitize_text)

        # 2. MAP COLUMNS (Specific to Exploded Format)
        col_map = {
            'ign': find_column(df, ['ign', 'player']),
            'group': find_column(df, ['cmgroup', 'bracket']),
            'money': find_column(df, ['spent', 'eur/usd']),
            'uma': find_column(df, ['uma']),
            'style': find_column(df, ['style', 'running']),
            'wins': find_column(df, ['wins', 'victory']),          # <--- Matches "Wins"
            'races': find_column(df, ['races', 'played', 'attempts']), # <--- Matches "Races Played"
            'Round': find_column(df, ['Round'], case_sensitive=True), 
            'Day': find_column(df, ['Day'], case_sensitive=True),
        }

        # 3. CLEAN & PARSE
        if col_map['money']: 
            df['Original_Spent'] = df[col_map['money']].fillna("Unknown")
            df['Sort_Money'] = clean_currency_numeric(df[col_map['money']])
        else: 
            df['Original_Spent'], df['Sort_Money'] = "Unknown", 0.0

        if col_map['uma']: df['Clean_Uma'] = parse_uma_details(df[col_map['uma']])
        else: df['Clean_Uma'] = "Unknown"

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

        # 4. PARSE STATS (Handle "4 Attempts - 20 Races")
        if col_map['races']:
            df['Clean_Races'] = extract_races_count(df[col_map['races']])
        else:
            df['Clean_Races'] = 1
            
        if col_map['wins']:
            df['Clean_Wins'] = pd.to_numeric(df[col_map['wins']], errors='coerce').fillna(0)
        else:
            df['Clean_Wins'] = 0

        # Safety: Cap Wins to Races
        df['Clean_Wins'] = df.apply(lambda x: min(x['Clean_Wins'], x['Clean_Races']), axis=1)

        # Calc WR
        df['Calculated_WinRate'] = (df['Clean_Wins'] / df['Clean_Races']) * 100
        df.loc[df['Calculated_WinRate'] > 100, 'Calculated_WinRate'] = 100

        # 5. DEDUPLICATE (CRITICAL STEP for Long Format)
        # Ensure we only have ONE row per Uma per Session (Trainer + Round + Day + Uma)
        # Sorting descending by Races ensures we keep the entry with the most complete data
        df = df.sort_values(by=['Clean_Races', 'Clean_Wins'], ascending=[False, False])
        df = df.drop_duplicates(subset=['Clean_IGN', 'Round', 'Day', 'Clean_Uma'], keep='first')

        # 6. ANONYMIZE
        df = anonymize_players(df)
        
        # 7. REBUILD TEAMS (Group by Session)
        # Since data is Long Format (1 row per Uma), we group by Session ID to get the Team
        # IMPORTANT: 'max' for Wins/Races because these columns contain the SESSION Total
        team_df = df.groupby(['Clean_IGN', 'Display_IGN', 'Clean_Group', 'Round', 'Day', 'Original_Spent', 'Sort_Money']).agg({
            'Clean_Uma': lambda x: sorted(list(x)), 
            'Clean_Style': lambda x: list(x),       
            'Calculated_WinRate': 'mean',    # Average WR of the team entries (should be same)
            'Clean_Races': 'max',            # <--- Use MAX, not SUM (Avoids triple counting)
            'Clean_Wins': 'max'              # <--- Use MAX, not SUM (Avoids triple counting)
        }).reset_index()
        
        team_df['Score'] = team_df.apply(lambda x: calculate_score(x['Clean_Wins'], x['Clean_Races']), axis=1)
        team_df['Uma_Count'] = team_df['Clean_Uma'].apply(len)
        team_df = team_df[team_df['Uma_Count'] == 3]
        team_df['Team_Comp'] = team_df['Clean_Uma'].apply(lambda x: ", ".join(x))
        
        return df, team_df
    except Exception as e:
        st.error(f"Data Error: {e}")
        return pd.DataFrame(), pd.DataFrame()
    
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