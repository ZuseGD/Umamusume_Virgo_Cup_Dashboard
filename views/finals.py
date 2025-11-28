import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from virgo_utils import load_finals_data, load_ocr_data, load_data, style_fig, PLOT_CONFIG, calculate_score, SHEET_URL, find_column, parse_uma_details

def resolve_lobby_winner(row, winner_ref, col_map):
    """
    Resolves the name of the winning Uma based on the reference column.
    e.g. Reference: "Own Team - Uma 1" -> returns value in "Own Team - Uma 1" column.
    """
    if pd.isna(winner_ref):
        return None
    
    ref = str(winner_ref).strip()
    
    # 1. Direct Match in Map (Reference -> Column Name)
    if ref in col_map:
        col_name = col_map[ref]
        uma_name = row.get(col_name)
        if pd.notna(uma_name) and str(uma_name).strip():
            return str(uma_name)
            
    # 2. Fallback: Check if the reference looks like a column header itself (fuzzy match)
    # Some forms might save "Opponent's Team 1 - Uma 4" directly
    for col in row.index:
        if ref.lower() in col.lower() and "running style" not in col.lower() and "role" not in col.lower():
            # Found the column the reference points to
            uma_name = row[col]
            if pd.notna(uma_name) and str(uma_name).strip():
                return str(uma_name)
                
    # 3. Fallback: The user might have selected "Other" and typed a name directly
    # If the reference doesn't look like a pointer (no "Team" or "Uma" keyword), assume it's the name
    if "team" not in ref.lower() and "uma" not in ref.lower():
        return ref
        
    return None

def show_view(current_config):
    st.header("🏆 Finals: Comprehensive Analysis")
    st.markdown("""
    **Deep Dive into the Finals Meta.** This section analyzes the "Real" meta—what actually won in the A-Finals. 
    It identifies the specific single winner of each lobby to avoid team-bias.
    """)
    
    # 1. LOAD DATA
    csv_path = current_config.get('finals_csv')
    pq_path = current_config.get('finals_parquet')
    prelims_pq = current_config.get('parquet_file') 
    
    if not csv_path:
        st.info("🚫 No Finals data configured.")
        return

    with st.spinner("Crunching Finals Data..."):
        # Load Raw for specific "Lobby Winner" column
        try:
            raw_finals_df = pd.read_csv(csv_path)
        except Exception as e:
            st.error(f"Could not load CSV: {e}")
            return

        prelims_raw = load_ocr_data(prelims_pq)
        matches_df, finals_ocr = load_finals_data(csv_path, pq_path, main_ocr_df=prelims_raw)
        sheet_df, _ = load_data(SHEET_URL)
    
    if matches_df.empty:
        st.warning("⚠️ Could not parse Finals data.")
        return

    # --- LOGIC: RESOLVE TRUE WINNERS ---
    # Robust Column Finding
    search_keys = [
        'Which uma won the finals lobby? (optional)', 
        'Which uma won the finals lobby', 
        'finalslobby', 
        'winninguma', 
        'lobbywinner'
    ]
    col_winner_ref = find_column(raw_finals_df, search_keys)
    
    # Manual Fallback if find_column fails (due to strict cleaning)
    if not col_winner_ref:
        for c in raw_finals_df.columns:
            c_lower = str(c).lower()
            if 'which uma won' in c_lower and 'lobby' in c_lower:
                col_winner_ref = c
                break

    # Map references (e.g. "Own Team - Uma 1") to actual column names in CSV
    ref_col_map = {}
    if col_winner_ref:
        for c in raw_finals_df.columns:
            # Generate keys for standard form options
            # Removes " (optional)" to match the dropdown values usually
            clean_c = str(c).replace(" (optional)", "").strip()
            ref_col_map[clean_c] = c
            ref_col_map[clean_c + " (optional)"] = c 
            
            # Handle specific variations if needed
            if "Opponent's" in clean_c:
                ref_col_map[clean_c.replace("Opponent's", "Opponent")] = c

    true_winners = []
    if col_winner_ref:
        for idx, row in raw_finals_df.iterrows():
            ref = row[col_winner_ref]
            if pd.notna(ref):
                w_name = resolve_lobby_winner(row, ref, ref_col_map)
                if w_name:
                    # Parse details (remove " - Runner" etc if present)
                    clean_name = parse_uma_details(pd.Series([w_name]))[0]
                    true_winners.append(clean_name)
    
    true_winners_df = pd.DataFrame(true_winners, columns=['Clean_Uma'])

    # --- DATA PREP ---
    winning_igns = set(matches_df[matches_df['Is_Winner'] == 1]['Match_IGN'].unique())
    prelims_baseline = prelims_raw.copy()
    if not prelims_baseline.empty and 'ign' in prelims_baseline.columns:
        prelims_baseline['Match_IGN'] = prelims_baseline['ign'].astype(str).str.lower().str.strip()
        prelims_baseline = prelims_baseline[~prelims_baseline['Match_IGN'].isin(winning_igns)]

    # --- METRICS ---
    total_entries = len(raw_finals_df)
    total_true_wins = len(true_winners_df)
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Finalists Analyzed", total_entries)
    m2.metric("Winner Umas Identified", total_true_wins, help="Unique winning horses extracted from 'Which uma won' column")
    m3.metric("Data Source", "A-Finals" if "A" in str(raw_finals_df.get('A or B Finals?', 'A')).upper() else "Mixed")
    
    st.markdown("---")

    # --- TABS ---
    tab_new, tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🥇 True Individual Winners",
        "📊 Meta Overview", 
        "⚔️ Team Comps", 
        "⚡ Skill Lift", 
        "🏆 Champion Stats",
        "🌐 Global Stats",
        "💸 Economics"
    ])

    # --- NEW TAB: INDIVIDUAL WINNERS ---
    with tab_new:
        st.subheader("🥇 True Finals Lobby Winners")
        
        if not true_winners_df.empty:
            st.markdown(f"""
            **Analysis of {total_true_wins} confirmed lobby winners.**
            This chart shows the exact character that won the race, excluding teammates.
            """)
            
            # 1. Aggregate counts
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
        st.caption("Note: This counts an Uma as a 'Winner' if they were on a winning team (Triple Counting). Use the 'True Individual Winners' tab for exact win counts.")
        
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
            comp_stats, x='Wins', y='Team', orientation='h', text='Label',
            title="Top Winning Teams (Win Count)", template='plotly_dark', color='Win_Rate', color_continuous_scale='Plasma'
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

    # --- TAB 3: SKILL LIFT ---
    with tab3:
        st.subheader("⚡ Skill Lift Analysis")
        if finals_ocr.empty or prelims_baseline.empty:
            st.warning("Need Finals OCR + Prelims OCR data.")
        else:
            c1, c2 = st.columns(2)
            winners_ocr = finals_ocr[finals_ocr['Is_Winner'] == 1].copy()
            if 'Clean_Role' in winners_ocr.columns:
                winners_ocr = winners_ocr[winners_ocr['Clean_Role'].str.contains('Ace', case=False, na=False)]
            
            with c1:
                all_umas = sorted(list(set(winners_ocr['Match_Uma'].unique()) | set(prelims_baseline['Match_Uma'].unique()))) if 'Match_Uma' in prelims_baseline.columns else sorted(winners_ocr['Match_Uma'].unique())
                sel_uma = st.selectbox("Filter by Character:", ["All"] + all_umas, key="lift_uma")
            with c2:
                sel_style = st.selectbox("Filter by Style:", ["All"] + sorted(winners_ocr['Clean_Style'].unique()), key="lift_style")
            
            w_filt = winners_ocr.copy()
            p_filt = prelims_baseline.copy()
            
            if sel_uma != "All":
                w_filt = w_filt[w_filt['Match_Uma'] == sel_uma]
                if 'Match_Uma' in p_filt.columns: p_filt = p_filt[p_filt['Match_Uma'] == sel_uma]
            if sel_style != "All":
                w_filt = w_filt[w_filt['Clean_Style'] == sel_style]

            if len(w_filt) < 5: st.caption("⚠️ Low sample size for winners.")

            def get_freq(df):
                if 'skills' not in df.columns or df.empty: return pd.Series()
                s = df['skills'].astype(str).str.replace(r"[\[\]']", "", regex=True).str.split(',')
                return s.explode().str.strip().replace("", np.nan).dropna().value_counts(normalize=True) * 100

            lift = pd.concat([get_freq(w_filt).rename("Winner %"), get_freq(p_filt).rename("Baseline %")], axis=1).fillna(0)
            lift['Lift'] = lift['Winner %'] - lift['Baseline %']
            lift['New'] = lift['Baseline %'] == 0
            lift = lift[lift['Winner %'] > 5].copy()
            
            top = lift.sort_values('Lift', ascending=False).head(20).copy()
            if not top.empty:
                fig = px.bar(top, x='Lift', y=top.index, orientation='h', color='New',
                             title="Skill Lift (Winners vs Baseline)", template='plotly_dark',
                             color_discrete_map={True: '#FFD700', False: '#00CC96'})
                fig.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(style_fig(fig), width='stretch', config=PLOT_CONFIG)
            else:
                st.info("No significant skills found.")

    # --- TAB 4: CHAMPION STATS ---
    with tab4:
        st.subheader("🏆 Champion Stat Distribution")
        if not finals_ocr.empty and not prelims_baseline.empty:
            c1, c2 = st.columns(2)
            with c1:
                all_umas_stat = sorted(list(set(finals_ocr['Match_Uma'].unique()) | set(prelims_baseline['Match_Uma'].unique()))) if 'Match_Uma' in prelims_baseline.columns else sorted(finals_ocr['Match_Uma'].unique())
                sel_uma_stat = st.selectbox("Character:", ["All"] + all_umas_stat, key="stat_uma")
            with c2:
                sel_style_stat = st.selectbox("Style:", ["All"] + sorted(finals_ocr['Clean_Style'].unique()), key="stat_style")
            
            w_df = finals_ocr[finals_ocr['Is_Winner'] == 1].copy()
            w_df['Group'] = 'Champions'
            f_df = prelims_baseline.copy()
            f_df['Group'] = 'The Field'
            
            if sel_uma_stat != "All":
                w_df = w_df[w_df['Match_Uma'] == sel_uma_stat]
                if 'Match_Uma' in f_df.columns: f_df = f_df[f_df['Match_Uma'] == sel_uma_stat]
            if sel_style_stat != "All":
                w_df = w_df[w_df['Clean_Style'] == sel_style_stat]
                if 'Clean_Style' in f_df.columns: f_df = f_df[f_df['Clean_Style'] == sel_style_stat]

            cols = [c for c in ['Speed', 'Stamina', 'Power', 'Guts', 'Wit'] if c in w_df.columns and c in f_df.columns]
            if cols and not w_df.empty and not f_df.empty:
                melt = pd.concat([w_df[cols+['Group']], f_df[cols+['Group']]]).melt(id_vars='Group', value_vars=cols)
                fig = px.box(melt, x='variable', y='value', color='Group', template='plotly_dark',
                             color_discrete_map={'Champions': '#00CC96', 'The Field': '#EF553B'})
                st.plotly_chart(style_fig(fig), width='stretch', config=PLOT_CONFIG)
            else:
                st.warning("Insufficient stats data.")

    # --- TAB 5: GLOBAL STATS ---
    with tab5:
        st.subheader("🌐 Global Event Statistics")
        
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

        # Row 1: The Bad (Fraud & Struggles)
        col_g1, col_g2 = st.columns(2)

        # 1. Fraud Award
        with col_g1:
            st.markdown("##### 🤡 The 'Fraud' Award")
            st.caption("Highest usage (>200) with **lowest** Win Rates.")
            
            fraud_stats = global_agg[global_agg['Entries'] > 200].sort_values('Win_Rate', ascending=True).head(10).copy()
            
            if not fraud_stats.empty:
                fig_fraud = px.bar(
                    fraud_stats, x='Win_Rate', y='Uma', orientation='h', text='Entries',
                    title="Lowest Win Rates (Min 200 Entries)",
                    labels={'Win_Rate': 'Win Rate (%)', 'Uma': 'Character'},
                    template='plotly_dark', color='Win_Rate', color_continuous_scale='Redor_r'
                )
                fig_fraud.update_traces(texttemplate='%{text} Entries', textposition='outside')
                fig_fraud.update_yaxes(categoryorder='array', categoryarray=fraud_stats['Uma'][::-1]) 
                st.plotly_chart(style_fig(fig_fraud, height=400), width='stretch', config=PLOT_CONFIG)
            else:
                st.info("No characters met the >200 entries criteria.")

        # 2. Oshi Strugglers
        with col_g2:
            st.markdown("##### 💔 Oshi Strugglers")
            st.caption("Niche picks (<200 Entries) with **lowest** 1st Place %.")
            
            # Filter < 200 but > 20 to avoid noise
            struggle_stats = global_agg[(global_agg['Entries'] < 200) & (global_agg['Entries'] > 20)].sort_values('First_Rate', ascending=True).head(10).copy()
            
            if not struggle_stats.empty:
                fig_struggle = px.bar(
                    struggle_stats, x='First_Rate', y='Uma', orientation='h', text='Entries',
                    title="Lowest 1st Place % (20 < Entries < 200)",
                    labels={'First_Rate': '1st Place %', 'Uma': 'Character'},
                    template='plotly_dark', color='First_Rate', color_continuous_scale='Redor_r'
                )
                fig_struggle.update_traces(texttemplate='%{text} Entries', textposition='outside')
                fig_struggle.update_yaxes(categoryorder='array', categoryarray=struggle_stats['Uma'][::-1])
                st.plotly_chart(style_fig(fig_struggle, height=400), width='stretch', config=PLOT_CONFIG)
            else:
                st.info("No data in range.")

        st.markdown("---")
        
        # Row 2: The Good (Oshi Winners)
        col_g3, col_g4 = st.columns(2)
        
        with col_g3:
            st.markdown("##### 💎 Oshi Winners (Hidden Gems)")
            st.caption("Niche picks (<200 Entries) with **highest** Win Rates.")
            
            # Filter < 200 but > 20, Sort Descending
            oshi_winners = global_agg[(global_agg['Entries'] < 200) & (global_agg['Entries'] > 20)].sort_values('Win_Rate', ascending=False).head(10).copy()
            
            if not oshi_winners.empty:
                fig_oshi = px.bar(
                    oshi_winners, x='Win_Rate', y='Uma', orientation='h', text='Entries',
                    title="Highest Win Rates (20 < Entries < 200)",
                    labels={'Win_Rate': 'Win Rate (%)', 'Uma': 'Character'},
                    template='plotly_dark', color='Win_Rate', color_continuous_scale='Greens'
                )
                fig_oshi.update_traces(texttemplate='%{text} Entries', textposition='outside')
                fig_oshi.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(style_fig(fig_oshi, height=400), width='stretch', config=PLOT_CONFIG)
            else:
                st.info("No data in range.")

        with col_g4:
            st.info("ℹ️ 'Oshi' charts filter out meta characters (>200 entries) to highlight performance of less common picks.")

        st.markdown("---")
        
        # 4. Placement Breakdown (Sorted Chart - 1st vs Did Not Win)
        st.markdown("##### 🏅 Finals Placement Breakdown (1st vs Did Not Win)")
        
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
        st.markdown("##### 📊 Placement Distribution (%) - Sorted by 1st Place")
        
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

    # --- TAB 6: ECONOMICS & CARDS ---
    with tab6:
        st.subheader("💸 Economics & Investment Analysis")
        st.markdown("Impact of **Spending** and **Grind Volume** on Results.")
        
        econ_df = matches_df[matches_df['Spending_Text'] != 'Unknown'].copy()
        
        if econ_df.empty:
            st.warning("No spending/runs data found in CSV.")
        else:
            c1, c2 = st.columns(2)
            
            with c1:
                st.markdown("##### 💰 Win Rate by Spending Tier")
                spend_stats = econ_df.groupby('Spending_Text').agg({
                    'Is_Winner': ['mean', 'count'],
                    'Sort_Money': 'mean' 
                }).reset_index()
                spend_stats.columns = ['Tier', 'Win_Rate', 'Entries', 'Sort_Val']
                spend_stats['Win_Rate'] *= 100
                spend_stats = spend_stats.sort_values('Sort_Val')
                
                fig_spend = px.bar(
                    spend_stats, x='Tier', y='Win_Rate', text='Entries',
                    title="Money vs. Win Rate",
                    template='plotly_dark', color='Win_Rate', color_continuous_scale='Greens'
                )
                fig_spend.update_traces(texttemplate='%{text} Entries', textposition='outside')
                st.plotly_chart(style_fig(fig_spend), width='stretch', config=PLOT_CONFIG)
            
            with c2:
                st.markdown("##### 🏃 Win Rate by Daily Grind")
                if 'Runs_Text' in econ_df.columns:
                    runs_df = econ_df[~econ_df['Runs_Text'].astype(str).str.contains('Unknown', case=False)].copy()
                    
                    if not runs_df.empty:
                        def sort_runs(val):
                            val = str(val)
                            if '0' in val: return 0
                            if '1' in val: return 1
                            if '3' in val: return 3
                            if '6' in val: return 6
                            return 99

                        run_stats = runs_df.groupby('Runs_Text').agg({
                            'Is_Winner': ['mean', 'count']
                        }).reset_index()
                        run_stats.columns = ['Runs', 'Win_Rate', 'Entries']
                        run_stats['Sort_Val'] = run_stats['Runs'].apply(sort_runs)
                        run_stats['Win_Rate'] *= 100
                        run_stats = run_stats.sort_values('Sort_Val')

                        fig_runs = px.bar(
                            run_stats, x='Runs', y='Win_Rate', text='Entries',
                            title="Grind Volume vs. Win Rate",
                            template='plotly_dark', color='Win_Rate', color_continuous_scale='Blues'
                        )
                        fig_runs.update_traces(texttemplate='%{text} Entries', textposition='outside')
                        st.plotly_chart(style_fig(fig_runs), width='stretch', config=PLOT_CONFIG)
                    else:
                        st.info("No valid run data found.")
                else:
                    st.info("No runs data available.")

            st.markdown("---")
            st.subheader("🃏 Support Card Impact")
            
            if 'Card_Kitasan' in econ_df.columns:
                kitasan_stats = econ_df.groupby('Card_Kitasan').agg({'Is_Winner': ['mean', 'count']}).reset_index()
                kitasan_stats.columns = ['Level', 'Win_Rate', 'Entries']
                kitasan_stats['Win_Rate'] *= 100
                kitasan_stats = kitasan_stats[kitasan_stats['Entries'] > 5].sort_values('Win_Rate', ascending=False)
                
                fig_kita = px.bar(
                    kitasan_stats, x='Level', y='Win_Rate', color='Entries',
                    title="Speed SSR: Kitasan Black", template='plotly_dark'
                )
                st.plotly_chart(style_fig(fig_kita, height=400), width='stretch', config=PLOT_CONFIG)
            
            if 'Card_Fine' in econ_df.columns:
                fine_stats = econ_df.groupby('Card_Fine').agg({'Is_Winner': ['mean', 'count']}).reset_index()
                fine_stats.columns = ['Level', 'Win_Rate', 'Entries']
                fine_stats['Win_Rate'] *= 100
                fine_stats = fine_stats[fine_stats['Entries'] > 5].sort_values('Win_Rate', ascending=False)
                
                fig_fine = px.bar(
                    fine_stats, x='Level', y='Win_Rate', color='Entries',
                    title="Wit SSR: Fine Motion", template='plotly_dark'
                )
                st.plotly_chart(style_fig(fig_fine, height=400), width='stretch', config=PLOT_CONFIG)