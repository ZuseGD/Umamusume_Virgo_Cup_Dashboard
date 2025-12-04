import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import re
from virgo_utils import load_finals_data, load_ocr_data, load_data, style_fig, PLOT_CONFIG, calculate_score, SHEET_URL, find_column, parse_uma_details, VARIANT_MAP, smart_match_name

def normalize_name(name):
    """
    Normalizes Uma names by merging variants based on VARIANT_MAP.
    e.g. "Uma (Anime Collab)" -> "Uma (Anime)"
    """
    n = str(name)
    for v_key, v_target in VARIANT_MAP.items():
        if v_key.lower() in n.lower():
            # Regex replace to preserve surrounding formatting
            n = re.sub(re.escape(v_key), v_target, n, flags=re.IGNORECASE)
    return n

def resolve_lobby_winner(row, winner_ref, col_map):
    """
    Resolves the name of the winning Uma based on the reference column.
    """
    if pd.isna(winner_ref):
        return None
    
    ref = str(winner_ref).strip()
    
    # 1. Direct Match in Map
    if ref in col_map:
        col_name = col_map[ref]
        uma_name = row.get(col_name)
        if pd.notna(uma_name) and str(uma_name).strip():
            return str(uma_name)
            
    # 2. Fallback: Check if the reference looks like a column header
    for col in row.index:
        if ref.lower() in col.lower() and "running style" not in col.lower() and "role" not in col.lower():
            uma_name = row[col]
            if pd.notna(uma_name) and str(uma_name).strip():
                return str(uma_name)
                
    # 3. Fallback: Type-in name
    if "team" not in ref.lower() and "uma" not in ref.lower():
        return ref
        
    return None

def show_view(current_config):
    st.header("🏆 Finals: Comprehensive Analysis")
    st.markdown("""
    **Deep Dive into the Finals Meta.** """)
    
    # 1. LOAD DATA
    csv_path = current_config.get('finals_csv')
    pq_path = current_config.get('finals_parquet')
    prelims_pq = current_config.get('parquet_file') 
    
    if not csv_path:
        st.info("🚫 No Finals data configured.")
        return

    with st.spinner("Crunching Finals Data..."):
        try:
            raw_finals_df = pd.read_csv(csv_path)
        except Exception as e:
            st.error(f"Could not load CSV: {e}")
            return

        prelims_raw = load_ocr_data(prelims_pq)
        matches_df, finals_ocr = load_finals_data(csv_path, pq_path, main_ocr_df=prelims_raw)
        
        # Load Raw Finals Parquet explicitly for "Opponent Recovery"
        raw_finals_pq = load_ocr_data(pq_path)
        
        sheet_df, _ = load_data(SHEET_URL)
    
    if matches_df.empty:
        st.warning("⚠️ Could not parse Finals data.")
        return

    # --- NORMALIZE NAMES & DATA PREP ---
    valid_names = []
    if not matches_df.empty:
        # Get valid names for smart matching
        valid_names = matches_df['Clean_Uma'].unique().tolist()
        
        # Normalize matches_df
        matches_df['Clean_Uma'] = matches_df['Clean_Uma'].apply(normalize_name)
        matches_df['Uma'] = matches_df['Clean_Uma'] 
        
    # FIX: Ensure raw_finals_pq has Match_Uma
    if not raw_finals_pq.empty:
        if 'Match_Uma' not in raw_finals_pq.columns:
            if 'name' in raw_finals_pq.columns:
                 # Use smart_match_name to align with CSV names
                 raw_finals_pq['Match_Uma'] = raw_finals_pq['name'].apply(lambda x: smart_match_name(x, valid_names))
            elif 'Name' in raw_finals_pq.columns:
                 raw_finals_pq['Match_Uma'] = raw_finals_pq['Name'].apply(lambda x: smart_match_name(x, valid_names))
            else:
                 # Fallback
                 # st.warning("Finals Parquet missing 'name' column. OCR analysis for champions might be incomplete.")
                 raw_finals_pq['Match_Uma'] = "Unknown"
        
        # Normalize
        raw_finals_pq['Match_Uma'] = raw_finals_pq['Match_Uma'].apply(normalize_name)
        
    if not finals_ocr.empty:
        finals_ocr['Match_Uma'] = finals_ocr['Match_Uma'].apply(normalize_name)
        
    # Prelims raw might have been modified by load_finals_data (pandas side-effect), but verify
    if not prelims_raw.empty:
        if 'Match_Uma' not in prelims_raw.columns and 'name' in prelims_raw.columns:
             prelims_raw['Match_Uma'] = prelims_raw['name'].apply(lambda x: smart_match_name(x, valid_names))
        if 'Match_Uma' in prelims_raw.columns:
             prelims_raw['Match_Uma'] = prelims_raw['Match_Uma'].apply(normalize_name)

    # --- LOGIC: RESOLVE TRUE WINNERS ---
    search_keys = [
        'Which uma won the finals lobby? (optional)', 
        'Which uma won the finals lobby', 
        'finalslobby', 
        'winninguma', 
        'lobbywinner'
    ]
    col_winner_ref = find_column(raw_finals_df, search_keys)
    
    if not col_winner_ref:
        for c in raw_finals_df.columns:
            if 'which uma won' in str(c).lower() and 'lobby' in str(c).lower():
                col_winner_ref = c
                break

    ref_col_map = {}
    if col_winner_ref:
        for c in raw_finals_df.columns:
            clean_c = str(c).replace(" (optional)", "").strip()
            ref_col_map[clean_c] = c
            ref_col_map[clean_c + " (optional)"] = c 
            if "Opponent's" in clean_c:
                ref_col_map[clean_c.replace("Opponent's", "Opponent")] = c

    true_winners_list = []
    if col_winner_ref:
        for idx, row in raw_finals_df.iterrows():
            ref = row[col_winner_ref]
            if pd.notna(ref):
                w_name = resolve_lobby_winner(row, ref, ref_col_map)
                if w_name:
                    clean_name = parse_uma_details(pd.Series([w_name]))[0]
                    # Normalize the resolved winner name
                    clean_name = normalize_name(clean_name)
                    
                    ign_col = find_column(raw_finals_df, ['ign', 'player name', 'in-game name'])
                    player_ign = str(row.get(ign_col, 'Unknown')).strip() if ign_col else 'Unknown'
                    
                    is_own_win = "own team" in str(ref).lower()
                    winning_trainer = player_ign if is_own_win else "Opponent"
                    
                    true_winners_list.append({
                        'Clean_Uma': clean_name,
                        'Winner_Trainer': winning_trainer,
                        'Source_Ref': str(ref)
                    })
    
    true_winners_df = pd.DataFrame(true_winners_list)

    # --- STATS GENERATION ---
    popularity = matches_df['Clean_Uma'].value_counts().reset_index()
    popularity.columns = ['Uma', 'Entries']
    
    if not true_winners_df.empty:
        wins = true_winners_df['Clean_Uma'].value_counts().reset_index()
        wins.columns = ['Uma', 'Wins']
    else:
        wins = pd.DataFrame(columns=['Uma', 'Wins'])
        
    stats = pd.merge(popularity, wins, on='Uma', how='outer').fillna(0)
    stats['Entries'] = stats[['Entries', 'Wins']].max(axis=1)
    
    stats['Win_Rate'] = (stats['Wins'] / stats['Entries']) * 100
    stats['Win_Rate'] = stats['Win_Rate'].clip(upper=100)
    
    oshi_cutoff = 10
    stats['Is_Oshi'] = stats['Entries'] < oshi_cutoff

    # --- METRICS ---
    total_entries = len(raw_finals_df)
    total_true_wins = len(true_winners_df)
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Finalists Analyzed", total_entries)
    m2.metric("Lobbies Resolved", total_true_wins)
    m3.metric("Oshi Cutoff", f"< {oshi_cutoff} Entries")
    
    st.markdown("---")

    # --- PREPARE DATA FOR TABS ---
    
    # 1. Prelims Baseline (Remove Winners)
    winning_igns = set(matches_df[matches_df['Is_Winner'] == 1]['Match_IGN'].unique())
    prelims_baseline = prelims_raw.copy()
    if not prelims_baseline.empty and 'ign' in prelims_baseline.columns:
        prelims_baseline['Match_IGN'] = prelims_baseline['ign'].astype(str).str.lower().str.strip()
        prelims_baseline = prelims_baseline[~prelims_baseline['Match_IGN'].isin(winning_igns)]

    # 2. EXPANDED CHAMPION POOL (The "Better Way")
    # Identify stats for ALL winners (Own + Opponent) by matching Lobby Winners to Raw Parquet data
    
    champion_stats_df = pd.DataFrame()
    if not true_winners_df.empty and not raw_finals_pq.empty and 'Match_Uma' in raw_finals_pq.columns:
        # A. Identify Known Losers (from CSV linked data) to exclude them
        # We don't want to accidentally count a "King Halo" that got 3rd place as a Winner
        # just because "King Halo" won the lobby.
        known_losers = finals_ocr[finals_ocr['Is_Winner'] == 0].copy()
        
        def get_sig(row):
            # Create a signature to identify unique OCR entries (Name + Stats + Skills)
            return f"{row.get('Match_Uma')}_{row.get('Speed')}_{row.get('Power')}_{str(row.get('skills'))[:20]}"
            
        known_loser_sigs = set(known_losers.apply(get_sig, axis=1)) if not known_losers.empty else set()
        
        # B. Filter Raw Parquet for Confirmed Winner Names
        winner_names = set(true_winners_df['Clean_Uma'].unique())
        
        # Keep rows where: Name is a Winner AND It is NOT a known loser
        champion_stats_df = raw_finals_pq[
            raw_finals_pq['Match_Uma'].isin(winner_names) & 
            ~raw_finals_pq.apply(get_sig, axis=1).isin(known_loser_sigs)
        ].copy()
        
        # C. Patch Missing 'Clean_Style' for Opponents (Raw PQ doesn't have CSV dropdown data)
        if 'Clean_Style' not in champion_stats_df.columns:
            champion_stats_df['Clean_Style'] = 'Unknown'
            
        # Try to backfill Style from finals_ocr for known rows
        if not finals_ocr.empty:
            # Create a lookup for style based on signature
            finals_ocr['sig'] = finals_ocr.apply(get_sig, axis=1)
            style_map = dict(zip(finals_ocr['sig'], finals_ocr['Clean_Style']))
            
            champion_stats_df['sig'] = champion_stats_df.apply(get_sig, axis=1)
            champion_stats_df['Clean_Style'] = champion_stats_df.apply(
                lambda x: style_map.get(x['sig'], 'Unknown'), axis=1
            )

    # Fallback if logic fails
    if champion_stats_df.empty:
        champion_stats_df = finals_ocr[finals_ocr['Is_Winner'] == 1].copy()

    # --- REPAIR DATA: Fix Missing Runs/Spending ---
    col_runs_raw = None
    for c in raw_finals_df.columns:
        if 'career' in c.lower() and 'runs' in c.lower():
            col_runs_raw = c
            break
    col_ign_raw = find_column(raw_finals_df, ['ign', 'player name', 'in-game name'])
    if col_runs_raw and col_ign_raw:
        runs_map = dict(zip(raw_finals_df[col_ign_raw].astype(str).str.lower().str.strip(), raw_finals_df[col_runs_raw]))
        if 'Runs_Text' not in matches_df.columns: matches_df['Runs_Text'] = 'Unknown'
        matches_df['Runs_Text'] = matches_df.apply(
            lambda x: runs_map.get(str(x['Match_IGN']), x['Runs_Text']) if x['Runs_Text'] == 'Unknown' else x['Runs_Text'], axis=1
        )

    # --- TABS ---
    tab_oshi, tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "💖 Oshi & Awards",
        "📊 Meta Overview", 
        "⚔️ Team Comps", 
        "⚡ Skill Lift", 
        "🏆 Champion Stats",
        "🌐 Global Stats",
        "💸 Economics"
    ])

        # --- TAB 1: OSHI & AWARDS (NEW) ---
    with tab_oshi:
        st.subheader("🏅 Performance Awards & Oshi Analysis")
        st.markdown('''This section analyzes the "Real" meta... What actually won in the A Finals? 
    It identifies the specific single winner of each lobby to avoid team-bias.''')
        
        if stats.empty:
            st.warning("Insufficient data to generate awards.")
        else:
            # CHART 1: BEST PERFORMING (Scatter)
            st.markdown("#### 1. The Meta Matrix: Usage vs. Win Rate")
            st.caption("Who actually wins the games they are used in? (Bubble size = Total Wins)")
            
            fig_perf = px.scatter(
                stats[stats['Entries'] > 3], # Filter out 1/1 anomalies
                x='Entries', y='Win_Rate',
                size='Wins', color='Win_Rate',
                hover_name='Uma',
                title="Performance Matrix (Wins vs Games Played)",
                labels={'Entries': 'Total Picks (Popularity)', 'Win_Rate': 'Win Rate (%)'},
                template='plotly_dark',
                color_continuous_scale='Turbo'
            )
            # Add a line for average win rate
            avg_wr = stats['Win_Rate'].mean()
            fig_perf.add_hline(y=avg_wr, line_dash="dash", line_color="white", annotation_text="Avg Win Rate")
            st.plotly_chart(style_fig(fig_perf), width='stretch', config=PLOT_CONFIG)
            
            c1, c2 = st.columns(2)
            
            # CHART 2: BEST OSHI (Hidden Gems)
            with c1:
                st.markdown("#### 💎 Best 'Oshi' (Hidden Gems)")
                st.caption(f"Highest Win Rate characters with < {oshi_cutoff} Picks")
                
                oshi_stats = stats[stats['Is_Oshi'] ].sort_values('Win_Rate', ascending=False).head(10)
                oshi_stats = oshi_stats[oshi_stats['Win_Rate'] > 0]
                if not oshi_stats.empty:
                    fig_gems = px.bar(
                        oshi_stats, x='Win_Rate', y='Uma', orientation='h',
                        title="Top Performing Niche Picks",
                        template='plotly_dark', color='Win_Rate', color_continuous_scale='Teal'
                    )
                    fig_gems.update_layout(yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(style_fig(fig_gems, height=400), width='stretch', config=PLOT_CONFIG)
                else:
                    st.info("Not enough data for Oshi awards (Min 3 entries).")
            
            # CHART 3: WORST PERFORMING
            with c2:
                st.markdown("#### 💀 The Struggle (Lowest Win Rate)")
                st.caption("Lowest Win Rate characters (Min. 5 Picks).")
                
                worst_stats = stats[stats['Entries'] >= 5].sort_values('Win_Rate', ascending=True).head(10)
                
                if not worst_stats.empty:
                    fig_worst = px.bar(
                        worst_stats, x='Win_Rate', y='Uma', orientation='h',
                        text='Entries',
                        title="Lowest Win Rates (Min 5 Entries)",
                        template='plotly_dark', color='Win_Rate', color_continuous_scale='Redor_r'
                    )
                    fig_worst.update_traces(texttemplate='%{text} Picks', textposition='outside')
                    fig_worst.update_layout(yaxis={'categoryorder':'total descending'})
                    st.plotly_chart(style_fig(fig_worst, height=400), width='stretch', config=PLOT_CONFIG)
                else:
                    st.info("Not enough data.")

            st.markdown("---")
            
            # TABLE 4: BEST OSHI PVPERS
            st.markdown("#### 👑 Oshi PvP-ers Hall of Fame")
            st.markdown(f"Trainers who **Won the Finals** using a certified Oshi and **SUBMITTED THEIR DATA** (Character with < {oshi_cutoff} total entries).")
            
            # Filter the true winners list for those who used an Oshi
            oshi_names = set(stats[stats['Is_Oshi']]['Uma'].unique())
            
            # Filter list for Oshi winners who are NOT 'Opponent' (we want to credit the player)
            oshi_pvpers = [
                row for row in true_winners_list 
                if row['Clean_Uma'] in oshi_names 
                and row['Winner_Trainer'] not in ['Unknown', 'Opponent']
            ]
            
            if oshi_pvpers:
                oshi_pvper_df = pd.DataFrame(oshi_pvpers)
                # Deduplicate entries if a player is listed twice for the same win (unlikely but safe)
                oshi_pvper_display = oshi_pvper_df[['Winner_Trainer', 'Clean_Uma']].drop_duplicates().reset_index(drop=True)
                
                st.dataframe(
                    oshi_pvper_display, 
                    width='stretch',
                    hide_index=True
                )
            else:
                st.info("No submitted runs found where the player won with an Oshi.")
        
        if not true_winners_df.empty:
            st.markdown(f"""
            **Analysis of {total_true_wins} confirmed lobby winners.**
            This chart shows the exact character that won the race (**INCLUDING THE OPPONENTS**), excluding the other horses.
            """)
            
            # 1. Aggregate counts
            # --- FIX: NORMALIZE NAMES FOR TRUE WINNERS CHART TOO ---
            true_winners_df['Clean_Uma'] = true_winners_df['Clean_Uma'].apply(normalize_name)
            
            win_counts = true_winners_df['Clean_Uma'].value_counts().reset_index()
            win_counts.columns = ['Uma', 'Wins']
            win_counts['Percentage'] = (win_counts['Wins'] / total_true_wins) * 100
            
            # 2. Sort and Filter
            win_counts = win_counts.sort_values('Wins', ascending=True) # For horizontal bar
            
            # 3. Plot
            fig_true = px.bar(
                win_counts, x='Wins', y='Uma', orientation='h', text='Wins',
                title=f"Individual Lobby Winners (Count)",
                template='plotly_dark', 
                color='Wins', 
                color_continuous_scale='Sunsetdark'
            )
            
            # Add percentage as hover
            fig_true.update_traces(
                texttemplate='%{text}', 
                textposition='outside',
                hovertemplate='<b>%{y}</b><br>Wins: %{x}<br>Share: %{customdata:.1f}%',
                customdata=win_counts['Percentage']
            )
            
            # Dynamic Height
            h = max(500, len(win_counts) * 30)
            st.plotly_chart(style_fig(fig_true, height=h), width='stretch', config=PLOT_CONFIG)
            
        else:
            st.warning("⚠️ No 'Lobby Winner' data identified.")
            st.markdown(f"**Debug Info:** Found Column: `{col_winner_ref}`. Rows: {len(raw_finals_df)}")
            if col_winner_ref:
                 st.write("Sample References:", raw_finals_df[col_winner_ref].dropna().head().tolist())

    # --- TAB 1: META OVERVIEW (Legacy Team Based) ---
    with tab1:
        st.subheader("🏁 Character Team Presence (Legacy)")
        st.caption("Note: This counts an Uma as a 'Winner' if they were on a **winning team** Use the 'Oshi & Awards' tab for exact win counts.")
        
        if not sheet_df.empty:
            prelim_stats = sheet_df.groupby('Clean_Uma')[['Clean_Wins', 'Clean_Races']].sum()
        else:
            prelim_stats = pd.DataFrame(columns=['Clean_Wins', 'Clean_Races'])
            
        finals_stats = matches_df.groupby('Clean_Uma').agg(
            Clean_Wins=('Is_Winner', 'sum'),
            Clean_Races=('Is_Winner', 'count')
        )
        
        cum_stats = prelim_stats.add(finals_stats, fill_value=0)
        cum_stats = cum_stats[cum_stats['Clean_Races'] > 0]
        cum_stats['Win_Rate'] = (cum_stats['Clean_Wins'] / cum_stats['Clean_Races']) * 100
        cum_stats['Meta_Score'] = cum_stats.apply(lambda x: calculate_score(x['Clean_Wins'], x['Clean_Races']), axis=1)
        
        tier_data = cum_stats[cum_stats['Clean_Races'] >= 5].reset_index().rename(columns={'index': 'Uma'})
        
        if not tier_data.empty:
            slope, intercept = np.polyfit(tier_data['Meta_Score'], tier_data['Win_Rate'], 1)
            x_trend = np.linspace(tier_data['Meta_Score'].min(), tier_data['Meta_Score'].max(), 100)
            y_trend = slope * x_trend + intercept

            mean_s = tier_data['Meta_Score'].mean()
            std_s = tier_data['Meta_Score'].std()
            max_s = tier_data['Meta_Score'].max() * 1.1
            min_s = 0

            fig = px.scatter(
                tier_data, x='Meta_Score', y='Win_Rate', size='Clean_Races', color='Win_Rate',
                hover_name='Clean_Uma', title="Cumulative Meta: Impact vs Efficiency (Team Presence)",
                template='plotly_dark', color_continuous_scale='Viridis',
                labels={'Meta_Score': 'Meta Score', 'Win_Rate': 'Team Win Rate (%)', 'Clean_Races': 'Total Races'}
            )
            fig.add_trace(go.Scatter(x=x_trend, y=y_trend, mode='lines', name='Trend', line=dict(color='white', width=2, dash='dash'), opacity=0.5))
            
            fig.add_vrect(x0=mean_s + std_s, x1=max_s, fillcolor="purple", opacity=0.15, annotation_text="S Tier")
            fig.add_vrect(x0=mean_s, x1=mean_s + std_s, fillcolor="green", opacity=0.1, annotation_text="A Tier")
            fig.add_vrect(x0=mean_s - std_s, x1=mean_s, fillcolor="yellow", opacity=0.05, annotation_text="B Tier")
            fig.add_vrect(x0=min_s, x1=mean_s - std_s, fillcolor="red", opacity=0.05, annotation_text="C Tier")

            st.plotly_chart(style_fig(fig), width='stretch', config=PLOT_CONFIG)
        else:
            st.info("Not enough cumulative data.")

    # --- TAB 2: TEAM COMPS ---
    with tab2:
        st.subheader("⚔️ Winning Team Compositions")
        team_df = matches_df.groupby(['Display_IGN', 'Result']).agg({
            'Clean_Uma': lambda x: sorted(list(x)), 
            'Is_Winner': 'max'
        }).reset_index()
        team_df['Team_Comp'] = team_df['Clean_Uma'].apply(lambda x: ", ".join(x))
        
        comp_stats = team_df.groupby('Team_Comp').agg({'Is_Winner': ['count', 'sum']}).reset_index()
        comp_stats.columns = ['Team', 'Entries', 'Wins']
        comp_stats['Win_Rate'] = (comp_stats['Wins'] / comp_stats['Entries']) * 100
        comp_stats = comp_stats[comp_stats['Wins'] >= 1].sort_values(by=['Wins', 'Win_Rate'], ascending=False).head(15).copy()
        
        comp_stats['Label'] = comp_stats.apply(lambda x: f"<b>{int(x['Win_Rate'])}%</b> ({int(x['Wins'])}/{int(x['Entries'])})", axis=1)
        
        fig = px.bar(
            comp_stats, x='Win_Rate', y='Team', orientation='h', text='Label',
            title="Top Winning Teams (Win Count)", template='plotly_dark', color='Wins', color_continuous_scale='Plasma'
        )
        fig.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(style_fig(fig), width='stretch', config=PLOT_CONFIG)

        st.markdown("---")
        
        st.subheader("🏅 Team Placement Distribution")
        def norm_res(r):
            r = str(r).lower()
            if '1st' in r: return '1st'
            if '2nd' in r: return '2nd'
            if '3rd' in r: return '3rd'
            return 'Other'
            
        team_df['Clean_Result'] = team_df['Result'].apply(norm_res)
        top_teams = team_df['Team_Comp'].value_counts().head(15).index.tolist()
        filtered_teams = team_df[team_df['Team_Comp'].isin(top_teams)]
        team_pivot = filtered_teams.pivot_table(index='Team_Comp', columns='Clean_Result', values='Display_IGN', aggfunc='count', fill_value=0)
        team_long = team_pivot.reset_index().melt(id_vars='Team_Comp', var_name='Place', value_name='Count')
        team_long = team_long[team_long['Place'].isin(['1st', '2nd', '3rd'])]
        
        fig_team_place = px.bar(
            team_long, x='Count', y='Team_Comp', color='Place', orientation='h',
            title="Placement Breakdown for Top 15 Teams", template='plotly_dark',
            category_orders={'Place': ['1st', '2nd', '3rd']},
            color_discrete_map={'1st': '#FFD700', '2nd': '#C0C0C0', '3rd': '#CD7F32'}
        )
        fig_team_place.update_layout(yaxis={'categoryorder':'total ascending'}, barmode='stack')
        st.plotly_chart(style_fig(fig_team_place, height=600), width='stretch', config=PLOT_CONFIG)

    # --- TAB 3: SKILL LIFT (UPDATED WITH EXPANDED POOL) ---
    with tab3:
        st.subheader("⚡ Skill Lift Analysis")
        st.markdown(f"**Analyzing {len(champion_stats_df)} Champion profiles (Own + Verified Opponents).**")
        
        if champion_stats_df.empty or prelims_baseline.empty:
            st.warning("Need Finals OCR + Prelims OCR data.")
        else:
            c1, c2 = st.columns(2)
            with c1:
                all_umas = sorted(list(set(champion_stats_df['Match_Uma'].unique()) | set(prelims_baseline['Match_Uma'].unique())))
                sel_uma = st.selectbox("Filter by Character:", ["All"] + all_umas, key="lift_uma")
            with c2:
                # Use 'Unknown' style if missing from Opponent data
                avail_styles = sorted(champion_stats_df['Clean_Style'].unique())
                sel_style = st.selectbox("Filter by Style:", ["All"] + avail_styles, key="lift_style")
            
            w_filt = champion_stats_df.copy()
            p_filt = prelims_baseline.copy()
            
            if sel_uma != "All":
                w_filt = w_filt[w_filt['Match_Uma'] == sel_uma]
                if 'Match_Uma' in p_filt.columns: p_filt = p_filt[p_filt['Match_Uma'] == sel_uma]
            if sel_style != "All":
                w_filt = w_filt[w_filt['Clean_Style'] == sel_style]

            st.caption(f"Comparing **{len(w_filt)} Winners** vs **{len(p_filt)} Baseline** entries.")

            def get_freq(df):
                if 'skills' not in df.columns or df.empty: return pd.Series()
                s = df['skills'].astype(str).str.replace(r"[\[\]']", "", regex=True).str.split('|')
                return s.explode().str.strip().replace("", np.nan).dropna().value_counts(normalize=True) * 100

            lift = pd.concat([get_freq(w_filt).rename("Winner %"), get_freq(p_filt).rename("Baseline %")], axis=1).fillna(0)
            lift['Lift'] = lift['Winner %'] - lift['Baseline %']
            lift['New'] = lift['Baseline %'] == 0
            lift = lift[lift['Winner %'] > 5].copy()
            
            top = lift.sort_values('Lift', ascending=False).head(20).copy()
            if not top.empty:
                fig = px.bar(top, x='Lift', y=top.index, orientation='h', color='New', title="Skill Lift (Winners vs Baseline)", template='plotly_dark', color_discrete_map={True: '#FFD700', False: '#00CC96'})
                fig.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(style_fig(fig), width='stretch', config=PLOT_CONFIG)
            else:
                st.info("No significant skills found.")

    # --- TAB 4: CHAMPION STATS (UPDATED WITH EXPANDED POOL) ---
    with tab4:
        st.subheader("🏆 Champion Stat Distribution")
        st.warning("This analysis compares the in-game stats of all identified Finals Champions (including Opponents) against the general pool of Prelims participants. It helps identify any statistical advantages held by winning characters against **SUBMITTED ROUNDS DATA** (which is a smaller pool) THIS MEANS THAT IF THERE IS A SMALLER SAMPLE OF UMAS THEN THE GRAPHS MAY BE SIMILAR DUE TO SURVIVORSHIP BIAS.")
        if not champion_stats_df.empty and not prelims_baseline.empty:
            c1, c2 = st.columns(2)
            with c1:
                all_umas_stat = sorted(list(set(champion_stats_df['Match_Uma'].unique()) | set(prelims_baseline['Match_Uma'].unique())))
                sel_uma_stat = st.selectbox("Character:", ["All"] + all_umas_stat, key="stat_uma")
            with c2:
                avail_styles_stat = sorted(champion_stats_df['Clean_Style'].unique())
                sel_style_stat = st.selectbox("Style:", ["All"] + avail_styles_stat, key="stat_style")
            
            w_df = champion_stats_df.copy()
            w_df['Group'] = 'Champions'
            f_df = prelims_baseline.copy()
            f_df['Group'] = 'The Field'
            
            if sel_uma_stat != "All":
                w_df = w_df[w_df['Match_Uma'] == sel_uma_stat]
                if 'Match_Uma' in f_df.columns: f_df = f_df[f_df['Match_Uma'] == sel_uma_stat]
            if sel_style_stat != "All":
                w_df = w_df[w_df['Clean_Style'] == sel_style_stat]
                if 'Clean_Style' in f_df.columns: f_df = f_df[f_df['Clean_Style'] == sel_style_stat]

            st.caption(f"Comparing stats of **{len(w_df)} Champions**.")

            cols = [c for c in ['Speed', 'Stamina', 'Power', 'Guts', 'Wit'] if c in w_df.columns and c in f_df.columns]
            if cols and not w_df.empty and not f_df.empty:
                melt = pd.concat([w_df[cols+['Group']], f_df[cols+['Group']]]).melt(id_vars='Group', value_vars=cols)
                fig = px.box(melt, x='variable', y='value', color='Group', template='plotly_dark', color_discrete_map={'Champions': '#00CC96', 'The Field': '#EF553B'})
                st.plotly_chart(style_fig(fig), width='stretch', config=PLOT_CONFIG)
            else:
                st.warning("Insufficient stats data.")

    # --- TAB 5: GLOBAL STATS ---
    with tab5:
        st.subheader("🌐 Team Event Statistics")
        st.warning("This analysis focuses on entire team compositions that won Finals matches. It identifies the most successful team setups based on submitted data. Note that this is a statistical overview from **SUBMITTED DATA** and may not account for all variables.")
        # Prepare Data needed for all charts
        def is_first(res): return 1 if str(res).lower() == '1st' else 0
        matches_df['Is_1st'] = matches_df['Result'].apply(is_first)
        
        # Aggregation
        global_agg = matches_df.groupby('Clean_Uma').agg({
            'Is_Winner': ['mean', 'count'],
            'Is_1st': ['mean']
        }).reset_index()
        global_agg.columns = ['Uma', 'Win_Rate', 'Entries', 'First_Rate']
        global_agg['Win_Rate'] *= 100
        global_agg['First_Rate'] *= 100

        
        # 4. Placement Breakdown (Sorted Chart - 1st vs Did Not Win)
        st.markdown("##### 🏅 Team Finals Placement Breakdown (1st vs Did Not Win)")
        
        # NEW LOGIC: Only two categories
        def norm_res_final(r):
            r = str(r).lower()
            if '1st' in r: return '1st'
            return 'Didn\'t Win'

        matches_df['Clean_Result_Binary'] = matches_df['Result'].apply(norm_res_final)
        
        place_pivot = matches_df.pivot_table(index='Clean_Uma', columns='Clean_Result_Binary', values='Match_IGN', aggfunc='count', fill_value=0)
        # Ensure cols exist
        for c in ['1st', "Didn't Win"]:
            if c not in place_pivot.columns: place_pivot[c] = 0
            
        place_pivot['Total'] = place_pivot.sum(axis=1)
        place_pivot = place_pivot.sort_values('Total', ascending=False).head(20)
        place_counts_long = place_pivot[['1st', "Didn't Win"]].reset_index().melt(id_vars='Clean_Uma', var_name='Place', value_name='Count')
        
        fig_place_counts = px.bar(
            place_counts_long, x='Count', y='Clean_Uma', color='Place', orientation='h',
            title="Placement Counts (Top 20 Most Popular)", template='plotly_dark',
            category_orders={'Place': ['1st', "Didn't Win"]},
            color_discrete_map={'1st': '#FFD700', "Didn't Win": '#333333'}
        )
        fig_place_counts.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(style_fig(fig_place_counts), width='stretch', config=PLOT_CONFIG)
        
        # 5. Placement Distribution (%) (Sorted by 1st Place)
        st.markdown("##### 📊 Placement Distribution (%) - Sorted by 1st Place Teams")
        
        place_pivot['1st_Pct'] = (place_pivot['1st'] / place_pivot['Total']) * 100
        place_pivot['Loss_Pct'] = (place_pivot["Didn't Win"] / place_pivot['Total']) * 100
        
        place_pivot_sorted = place_pivot.sort_values('1st_Pct', ascending=True)
        place_long_pct = place_pivot_sorted[['1st_Pct', 'Loss_Pct']].reset_index().melt(id_vars='Clean_Uma', var_name='Place', value_name='Pct')
        place_long_pct['Place'] = place_long_pct['Place'].map({'1st_Pct': '1st', 'Loss_Pct': "Didn't Win"})

        fig_place_pct = px.bar(
            place_long_pct, x='Pct', y='Clean_Uma', color='Place', orientation='h',
            title="Placement Shares (Sorted by 1st Place %)", template='plotly_dark',
            category_orders={'Place': ['1st', "Didn't Win"]},
            color_discrete_map={'1st': '#FFD700', "Didn't Win": '#333333'}
        )
        fig_place_pct.update_yaxes(categoryorder='array', categoryarray=place_pivot_sorted.index)
        st.plotly_chart(style_fig(fig_place_pct), width='stretch', config=PLOT_CONFIG)

    # --- TAB 6: ECONOMICS (UPDATED) ---
    with tab6:
        st.subheader("💸 Economics & Investment Analysis")
        st.markdown("Impact of **Spending** and **Grind Volume** on Results.")
        
        econ_df = matches_df
        print(econ_df.head())
        if econ_df.empty:
            st.warning("No spending/runs data found in CSV.")
        else:
            c1, c2 = st.columns(2)
            
            with c1:
                st.markdown("##### 💰 Win Rate by Spending Tier")
                
                # FIX 1: Rename 'None' to 'F2P' for visibility
                econ_df['Spending_Text'] = econ_df['Spending_Text'].replace({'None': 'F2P', 'NaN': 'F2P', 'Unknown': 'F2P'})
                econ_df['Spending_Text'] = econ_df['Spending_Text'].fillna('F2P')
                spend_stats = econ_df.groupby('Spending_Text').agg({
                    'Is_Winner': ['mean', 'count'],
                    'Sort_Money': 'mean' 
                }).reset_index()
                spend_stats.columns = ['Tier', 'Win_Rate', 'Entries', 'Sort_Val']
                spend_stats['Win_Rate'] *= 100
                
                spend_stats['Tier'] = spend_stats['Tier'].map({
                    'F2P': 'F2P',
                    '$1-$50': 'Sardine ($1-$50)',
                    '$51-100': 'Salmon ($51-$100)',
                    '$101-$500': 'Bluefin Tuna ($101-$500)',
                    '$501-$1000': 'Dolphin $501-$1000',
                    '$1000+': 'Whale $1000+'})

                custom_order = ['F2P', 'Sardine ($1-$50)', 'Salmon ($51-$100)', 'Bluefin Tuna ($101-$500)', 'Dolphin $501-$1000', 'Whale $1000+']
                
                fig_spend = px.bar(
                    spend_stats, x='Tier', y='Win_Rate', text= 'Entries',
                    title="Money vs. Win Rate",
                    template='plotly_dark', color='Win_Rate', color_continuous_scale='Greens', category_orders={'Tier': custom_order}
                )
                fig_spend.update_traces(texttemplate='%{text} Entries', textposition='outside')
                fig_spend.update_xaxes(categoryorder='array', categoryarray=custom_order)
                
                st.plotly_chart(style_fig(fig_spend), width='stretch', config=PLOT_CONFIG)
            
            with c2:
                st.markdown("##### 🏃 Win Rate by Daily Grind")
                if 'Runs_Text' in econ_df.columns:
                    runs_df = econ_df[~econ_df['Runs_Text'].astype(str).str.contains('Unknown', case=False)].copy()
                    
                    if not runs_df.empty:
                        def sort_runs(val):
                            v = str(val).lower()
                            if '0-2' in v: return 0
                            if '0-3' in v: return 1
                            if '1-3' in v: return 2
                            if v.strip() == '3': return 3
                            if '4-5' in v: return 4
                            if '6+' in v: return 6
                            return 99

                        run_stats = runs_df.groupby('Runs_Text').agg({
                            'Is_Winner': ['mean', 'count']
                        }).reset_index()
                        run_stats.columns = ['Runs', 'Win_Rate', 'Entries']
                        run_stats['Sort_Val'] = run_stats['Runs'].apply(sort_runs)
                        run_stats['Win_Rate'] *= 100
                        run_stats = run_stats.sort_values('Sort_Val')
                        
                        # FIX 3: Enforce Order
                        run_order = run_stats['Runs'].tolist()

                        fig_runs = px.bar(
                            run_stats, x='Runs', y='Win_Rate', text='Entries',
                            title="Grind Volume vs. Win Rate",
                            template='plotly_dark', color='Win_Rate', color_continuous_scale='Blues'
                        )
                        fig_runs.update_traces(texttemplate='%{text} Entries', textposition='outside')
                        fig_runs.update_xaxes(categoryorder='array', categoryarray=run_order)
                        
                        st.plotly_chart(style_fig(fig_runs), width='stretch', config=PLOT_CONFIG)
                    else:
                        st.info("No valid run data found.")
                else:
                    st.info("No runs data available.")