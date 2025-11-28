import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import os
import re
import html


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

# --- HELPER FUNCTIONS ---

def smart_match_name(raw_name, valid_csv_names):
    """Matches OCR names (e.g. [Summer] Maruzensky) to CSV names (Maruzensky)."""
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
    
    # Try exact match first
    for cand in candidates:
        match = next((valid for valid in valid_csv_names if valid.lower() == cand.lower()), None)
        if match: return match
            
    if base_name in ORIGINAL_UMAS: return base_name
    return base_name 

def sanitize_text(text):
    if pd.isna(text): return text
    return html.escape(str(text))

def show_description(key):
    if key in DESCRIPTIONS:
        with st.expander("ℹ️ Info", expanded=False):
            st.markdown(DESCRIPTIONS[key])

def style_fig(fig, height=600):
    fig.update_layout(
        font=dict(size=14), 
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=10, r=10, t=40, b=10),
        autosize=True,
        height=height,
        template='plotly_dark'
    )
    return fig

def dynamic_height(n, min_h=400, per_item=40):
    return max(min_h, n * per_item)

def calculate_score(wins, races):
    if races == 0: return 0
    return (wins / races * 100) * np.sqrt(races)

def parse_uma_details(series):
    return series.astype(str).apply(lambda x: x.split(' - ')[0].strip().title())

def clean_currency_numeric(series):
    return (series.astype(str)
            .str.replace('$', '', regex=False)
            .str.replace(',', '', regex=False)
            .str.split('-').str[0]
            .apply(pd.to_numeric, errors='coerce')
            .fillna(0))

def extract_races_count(series):
    def parse(t):
        t = str(t).lower()
        m = re.search(r'(\d+)\s*races', t)
        if m: return int(m.group(1))
        if t.isdigit(): return int(t)
        return 1
    return series.apply(parse)

def find_column(df, keywords):
    for col in df.columns:
        if any(k.lower() in col.lower() for k in keywords): return col
    return None

def anonymize_players(df, top_n=10):
    if 'Clean_IGN' not in df.columns: return df
    
    player_stats = df.groupby('Clean_IGN').agg({
        'Clean_Wins': 'sum',
        'Clean_Races': 'sum'
    }).reset_index()
    
    player_stats['Score'] = player_stats.apply(lambda x: calculate_score(x['Clean_Wins'], x['Clean_Races']), axis=1)
    eligible_pros = player_stats[player_stats['Clean_Races'] >= 20]
    top_players = eligible_pros.sort_values('Score', ascending=False).head(top_n)['Clean_IGN'].tolist()
    
    df['Display_IGN'] = df['Clean_IGN'].apply(lambda x: x if x in top_players else "Anonymous Trainer")
    return df

# --- DATA LOADERS ---

@st.cache_data(ttl=3600)
def load_data(sheet_url):
    """Loads Standard Prelims CSV (Rounds 1 & 2)"""
    try:
        df = pd.read_csv(sheet_url)
        
        # 1. Sanitize
        string_cols = df.select_dtypes(include=['object']).columns
        for col in string_cols: df[col] = df[col].apply(sanitize_text)

        # 2. Find Columns
        col_ign = find_column(df, ['ign', 'player'])
        col_group = find_column(df, ['cmgroup', 'bracket', 'group'])
        col_money = find_column(df, ['spent', 'eur/usd'])
        col_uma = find_column(df, ['uma'])
        col_style = find_column(df, ['style', 'running'])
        col_wins = find_column(df, ['wins', 'victory'])
        col_races = find_column(df, ['races', 'played', 'attempts'])
        col_round = find_column(df, ['round'])
        col_day = find_column(df, ['day'])

        # 3. Create Standard Columns (GUARANTEED TO EXIST)
        df['Clean_IGN'] = df[col_ign].fillna("Anonymous") if col_ign else "Anonymous"
        df['Clean_Group'] = df[col_group].fillna("Unknown") if col_group else "Unknown"
        df['Original_Spent'] = df[col_money].fillna("Unknown") if col_money else "Unknown"
        df['Clean_Uma'] = parse_uma_details(df[col_uma]) if col_uma else "Unknown"
        df['Clean_Style'] = df[col_style].fillna("Unknown") if col_style else "Unknown"
        df['Round'] = df[col_round].fillna("Unknown") if col_round else "Unknown"
        df['Day'] = df[col_day].fillna("Unknown") if col_day else "Unknown"
        
        # Numeric Clean
        df['Sort_Money'] = clean_currency_numeric(df[col_money]) if col_money else 0.0
        df['Clean_Wins'] = pd.to_numeric(df[col_wins], errors='coerce').fillna(0) if col_wins else 0
        df['Clean_Races'] = extract_races_count(df[col_races]) if col_races else 1
        
        # Cap wins
        df['Clean_Wins'] = df.apply(lambda x: min(x['Clean_Wins'], x['Clean_Races']), axis=1)
        df['Calculated_WinRate'] = (df['Clean_Wins'] / df['Clean_Races']) * 100
        
        # 4. Deduplicate
        df = df.sort_values(by=['Clean_Races', 'Clean_Wins'], ascending=[False, False])
        df = df.drop_duplicates(subset=['Clean_IGN', 'Round', 'Day', 'Clean_Uma'], keep='first')
        
        # 5. Anonymize
        df = anonymize_players(df)
        
        # 6. Create Team DF (Group by Session)
        # We perform groupby ONLY on columns we just guaranteed exist above
        grp_cols = ['Clean_IGN', 'Display_IGN', 'Clean_Group', 'Round', 'Day', 'Original_Spent', 'Sort_Money']
        
        team_df = df.groupby(grp_cols).agg({
            'Clean_Uma': lambda x: sorted(list(x)), 
            'Clean_Style': lambda x: list(x),       
            'Calculated_WinRate': 'mean',
            'Clean_Races': 'max',
            'Clean_Wins': 'max'
        }).reset_index()
        
        team_df['Score'] = team_df.apply(lambda x: calculate_score(x['Clean_Wins'], x['Clean_Races']), axis=1)
        team_df['Uma_Count'] = team_df['Clean_Uma'].apply(len)
        team_df = team_df[team_df['Uma_Count'] == 3]
        team_df['Team_Comp'] = team_df['Clean_Uma'].apply(lambda x: ", ".join(x))
        
        return df, team_df
        
    except Exception as e:
        # Fallback to empty if anything critically fails
        print(f"Error in load_data: {e}")
        return pd.DataFrame(), pd.DataFrame()

@st.cache_data(ttl=3600)
def load_ocr_data(parquet_file):
    """Loads Standard OCR Data"""
    try:
        if not os.path.exists(parquet_file): return pd.DataFrame()
        df = pd.read_parquet(parquet_file)
        if 'ign' in df.columns:
            df['Match_IGN'] = df['ign'].astype(str).str.lower().str.strip()
        return df
    except:
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def load_finals_data(csv_path, parquet_path):
    """Loads Finals Wide-Format CSV and Finals Parquet."""
    if not csv_path or not os.path.exists(csv_path):
        return pd.DataFrame(), pd.DataFrame()

    # 1. LOAD CSV (Wide -> Long)
    try:
        raw_df = pd.read_csv(csv_path)
        processed_rows = []
        
        for _, row in raw_df.iterrows():
            ign = str(row.get('Player in-game name (IGN)', 'Unknown')).strip()
            result = str(row.get('Finals race result', 'Unknown'))
            is_win = 1 if result == '1st' else 0
            
            for i in range(1, 4):
                uma_name = row.get(f'Own Team - Uma {i}')
                style = row.get(f'Own team - Uma {i} - Running Style')
                
                if pd.notna(uma_name) and str(uma_name).strip() != "":
                    processed_rows.append({
                        'Match_IGN': ign.lower(),
                        'Display_IGN': ign,
                        'Clean_Uma': parse_uma_details(pd.Series([uma_name]))[0],
                        'Clean_Style': style,
                        'Result': result,
                        'Calculated_WinRate': is_win * 100,
                        'Is_Winner': is_win
                    })
        
        finals_matches = pd.DataFrame(processed_rows)
    except Exception as e:
        print(f"Error parsing Finals CSV: {e}")
        return pd.DataFrame(), pd.DataFrame()

    # 2. LOAD PARQUET & MERGE
    try:
        if not parquet_path or not os.path.exists(parquet_path):
            return finals_matches, pd.DataFrame()
            
        ocr_df = pd.read_parquet(parquet_path)
        
        if 'ign' in ocr_df.columns:
            ocr_df['Match_IGN'] = ocr_df['ign'].astype(str).str.lower().str.strip()
        
        if not finals_matches.empty:
            valid_names = finals_matches['Clean_Uma'].unique().tolist()
            ocr_df['Match_Uma'] = ocr_df['name'].apply(lambda x: smart_match_name(x, valid_names))
            finals_matches['Match_Uma'] = finals_matches['Clean_Uma']
            
            merged_df = pd.merge(
                ocr_df, 
                finals_matches, 
                on=['Match_IGN', 'Match_Uma'], 
                how='inner'
            )
            return finals_matches, merged_df
        
        return finals_matches, pd.DataFrame()
        
    except Exception as e:
        print(f"Error merging Finals Parquet: {e}")
        return finals_matches, pd.DataFrame()

# Common Footer
footer_html = """
<style>
.footer {
    position: fixed; left: 0; bottom: 0; width: 100%;
    background-color: #0E1117; color: #888; text-align: center;
    padding: 10px; font-size: 12px; border-top: 1px solid #333; z-index: 100;
}
</style>
<div class="footer">Made by Zuse 🚀</div>
"""