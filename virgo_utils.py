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
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    try:
        raw_df = pd.read_csv(csv_path)
        
        # --- 1. CALCULATE GLOBAL STATS (Using User's Logic) ---
        # Define slots
        entry_cols = [ 
            'Own Team - Uma 1', 'Own Team - Uma 2', 'Own Team - Uma 3', 
            "Opponent's Team 1 - Uma 4 (optional)", "Opponent's Team 1 - Uma 5 (optional)", "Opponent's Team 1 - Uma 6 (optional)", 
            "Opponent's Team 2 - Uma 7 (optional)", "Opponent's Team 2 - Uma 8 (optional)", "Opponent's Team 2 - Uma 9 (optional)" 
        ]
        
        # Identify Winner Column
        required_col = 'Which uma won the finals lobby? (optional)'
        # Fallback search if exact name not found
        if required_col not in raw_df.columns:
            required_col = find_column(raw_df, ['which uma won', 'lobby winner'])

        # A. Calculate Total Entries
        all_entries = pd.Series(dtype='object')
        for col in entry_cols:
            # Use find_column to be safe against minor typos/spacing in CSV
            actual_col = find_column(raw_df, [col])
            if actual_col:
                # Clean names (Remove strategy/role)
                cleaned_col = parse_uma_details(raw_df[actual_col])
                all_entries = pd.concat([all_entries, cleaned_col])
        
        # Remove empty/NaN entries
        all_entries = all_entries[all_entries.str.strip() != '']
        all_entries = all_entries[all_entries.str.lower() != 'nan']
        all_entries = all_entries[all_entries.str.lower() != 'unknown']
        
        entry_counts = all_entries.value_counts().reset_index()
        entry_counts.columns = ['Uma Name', 'Total Entries']

        # B. Identify Actual Winner Name
        def get_winner_name(row):
            if not required_col: return None
            winner_ref = row.get(required_col)
            if pd.isna(winner_ref): return None
            
            # Mapping Reference String -> Actual Column
            # Note: The drop-down in forms typically returns the Column Header string or a specific value
            # Assuming the CSV contains the text chosen from the dropdown which matches the column header
            
            # Map user-friendly dropdown values back to the column names in raw_df
            # Based on provided CSV snippet, the 'Which uma won...' column contains strings like "Own Team - Uma 1"
            # Or it might contain the actual name if it was a write-in.
            # Let's create a map of standard dropdown options to the column they represent.
            
            mapping = {
                'Own Team - Uma 1': find_column(raw_df, ['Own Team - Uma 1']),
                'Own Team - Uma 2': find_column(raw_df, ['Own Team - Uma 2']),
                'Own Team - Uma 3': find_column(raw_df, ['Own Team - Uma 3']),
                "Opponent's Team 1 - Uma 4": find_column(raw_df, ["Opponent's Team 1 - Uma 4"]),
                "Opponent's Team 1 - Uma 5": find_column(raw_df, ["Opponent's Team 1 - Uma 5"]),
                "Opponent's Team 1 - Uma 6": find_column(raw_df, ["Opponent's Team 1 - Uma 6"]),
                "Opponent's Team 2 - Uma 7": find_column(raw_df, ["Opponent's Team 2 - Uma 7"]),
                "Opponent's Team 2 - Uma 8": find_column(raw_df, ["Opponent's Team 2 - Uma 8"]),
                "Opponent's Team 2 - Uma 9": find_column(raw_df, ["Opponent's Team 2 - Uma 9"]),
            }
            
            # Check if the value is a key in our map (e.g. "Own Team - Uma 1")
            # The CSV snippet shows the column "Which uma won..." might contain names directly or references?
            # Looking at the CSV provided earlier: 
            # Row: "Frey... Which uma won... : Opponent's Team 2 - Uma 7"
            # Row: "Wadachi... Which uma won... : Opponent's Team 1 - Uma 4"
            # Row: "FzyBny... Which uma won... : Own Team - Uma 2"
            
            # So it contains the Reference String.
            # We need to handle partial matches or slight variations
            for key, col_name in mapping.items():
                if key in str(winner_ref) and col_name:
                    val = row.get(col_name)
                    if pd.notna(val):
                         return str(val).split(' - ')[0].strip().title()
            
            return None

        raw_df['Real Winner Name'] = raw_df.apply(get_winner_name, axis=1)
        winner_counts = raw_df['Real Winner Name'].value_counts().reset_index()
        winner_counts.columns = ['Uma Name', 'Wins']

        # C. Merge
        global_stats = pd.merge(entry_counts, winner_counts, on='Uma Name', how='outer').fillna(0)
        global_stats['Wins'] = global_stats['Wins'].astype(int)
        global_stats['Total Entries'] = global_stats['Total Entries'].astype(int)
        global_stats['Losses'] = global_stats['Total Entries'] - global_stats['Wins']
        
        # Calc Rates
        global_stats['Win Rate'] = (global_stats['Wins'] / global_stats['Total Entries'])
        global_stats['Win Rate %'] = (global_stats['Win Rate'] * 100).round(1)


        # --- 2. PROCESS FINALS MATCHES (Own Team for other tabs) ---
        col_spent = find_column(raw_df, ['spent', 'money', 'eur/usd', 'howmuchhaveyouspent'])
        col_runs = find_column(raw_df, ['career runs', 'runs per day', 'howmanycareer'])
        col_kitasan = find_column(raw_df, ['kitasan', 'speed: kitasan'])
        col_fine = find_column(raw_df, ['fine motion', 'wit: fine'])

        processed_rows = []
        
        for _, row in raw_df.iterrows():
            ign = str(row.get('Player in-game name (IGN)', 'Unknown')).strip()
            result = str(row.get('Finals race result', 'Unknown'))
            team_won = 1 if '1st' in str(result).lower() else 0
            
            spending = row.get(col_spent, 'Unknown') if col_spent else 'Unknown'
            runs_per_day = row.get(col_runs, 'Unknown') if col_runs else 'Unknown'
            card_kitasan = row.get(col_kitasan, 'Unknown') if col_kitasan else 'Unknown'
            card_fine = row.get(col_fine, 'Unknown') if col_fine else 'Unknown'
            
            # Determine if this row has a specific winner (for linking to stats)
            lobby_winner_name = row.get('Real Winner Name') # We calculated this above

            match_opponents = []
            # (Skipping opp extraction for the 'finals_matches' df as we have global_stats now)

            for i in range(1, 4):
                col_name = find_column(raw_df, [f'Own Team - Uma {i}'])
                if col_name:
                    uma_val = row.get(col_name)
                    
                    if pd.notna(uma_val) and str(uma_val).strip() != "":
                        clean_name = parse_uma_details(pd.Series([uma_val]))[0]
                        
                        # Is this specific Uma the winner?
                        is_specific_winner = 0
                        if lobby_winner_name and clean_name.lower() == lobby_winner_name.lower():
                            is_specific_winner = 1

                        processed_rows.append({
                            'Match_IGN': ign.lower(),
                            'Display_IGN': ign,
                            'Clean_Uma': clean_name,
                            'Result': result,
                            'Spending_Text': spending,
                            'Runs_Text': runs_per_day,
                            'Card_Kitasan': card_kitasan,
                            'Card_Fine': card_fine,
                            'Is_Winner': team_won,
                            'Is_Specific_Winner': is_specific_winner
                        })
        
        finals_matches = pd.DataFrame(processed_rows)
        if not finals_matches.empty:
            finals_matches['Sort_Money'] = clean_currency_numeric(finals_matches['Spending_Text'])

    except Exception as e:
        st.error(f"Error parsing Finals CSV: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

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
        return finals_matches, final_merged_df, global_stats
        
    except Exception as e:
        st.error(f"Error merging Finals Parquet: {e}")
        return finals_matches, pd.DataFrame(), pd.DataFrame()

@st.cache_data(ttl=3600)
def load_data(sheet_url):
    try:
        df = pd.read_csv(sheet_url)
        string_cols = df.select_dtypes(include=['object']).columns
        for col in string_cols: df[col] = df[col].apply(sanitize_text)
        
        if 'Round' not in df.columns: df['Round'] = 'Unknown'

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
        
        team_df = pd.DataFrame(columns=['Round', 'Team_Comp', 'Wins', 'Races', 'Win_Rate'])
        return df, team_df
    except:
        return pd.DataFrame(columns=['Round']), pd.DataFrame(columns=['Round'])

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