import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np
from virgo_utils import load_finals_data, load_ocr_data, style_fig, PLOT_CONFIG, calculate_score

def show_view(current_config):
    st.header("🏆 Finals: Comprehensive Analysis")
    st.markdown("""
    **Deep Dive into the Finals Meta.** This section analyzes the "Real" meta—what actually won in the A-Finals. 
    It compares the *Winning Aces* against the general population to identify the specific stats, skills, and team compositions that made the difference.
    """)
    
    # 1. LOAD DATA
    csv_path = current_config.get('finals_csv')
    pq_path = current_config.get('finals_parquet')
    prelims_pq = current_config.get('parquet_file') # For baseline comparison
    
    if not csv_path:
        st.info("🚫 No Finals data configured.")
        return

    with st.spinner("Crunching Finals Data..."):
        # Load Finals
        matches_df, finals_ocr = load_finals_data(csv_path, pq_path)
        
        # Load Prelims (Baseline)
        prelims_raw = load_ocr_data(prelims_pq)
    
    if matches_df.empty:
        st.warning("⚠️ Could not load Finals CSV.")
        return

    # --- 2. DATA PREPARATION: EXCLUDE WINNERS FROM BASELINE ---
    # We want "The Field" (Prelims) to NOT include the "Champions" (Finals Winners)
    # so we can see what the Champions did differently from the crowd.
    
    # Identify Winning IGNs
    winning_igns = set(matches_df[matches_df['Is_Winner'] == 1]['Match_IGN'].unique())
    
    # Prepare Baseline (Prelims)
    prelims_df = prelims_raw.copy()
    if not prelims_df.empty:
        # Create a normalized IGN column for filtering if it doesn't exist nicely
        if 'ign' in prelims_df.columns:
            prelims_df['Match_IGN'] = prelims_df['ign'].astype(str).str.lower().str.strip()
            # FILTER: Exclude Finals Winners from Prelims Data
            prelims_baseline = prelims_df[~prelims_df['Match_IGN'].isin(winning_igns)]
            excluded_count = len(prelims_df) - len(prelims_baseline)
        else:
            prelims_baseline = prelims_df
            excluded_count = 0
            st.warning("⚠️ Prelims data lacks IGNs; could not exclude Finals winners from baseline.")
    else:
        prelims_baseline = pd.DataFrame()
        excluded_count = 0

    # --- METRICS ---
    total_entries = matches_df['Display_IGN'].nunique()
    total_winners = matches_df[matches_df['Is_Winner'] == 1]['Display_IGN'].nunique()
    
    if 'Clean_Role' in matches_df.columns:
        ace_count = len(matches_df[matches_df['Clean_Role'].str.contains("Ace", case=False, na=False)])
        debuff_count = len(matches_df[matches_df['Clean_Role'].str.contains("Debuff", case=False, na=False)])
    else:
        ace_count, debuff_count = 0, 0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Finalists Analyzed", total_entries)
    m2.metric("Winners Confirmed", total_winners)
    m3.metric("Baseline Exclusions", f"{excluded_count} Entries", help="Finals winners removed from Prelims comparison data to prevent data leakage.")
    m4.metric("Ace Debuffer Ratio", ace_count + ":" + debuff_count)
    
    st.markdown("---")

    # --- TABS ---
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Meta Overview", 
        "⚔️ Team Comps", 
        "⚡ Skill Lift", 
        "🏆 Champion Stats"
    ])

    # --- TAB 1: META OVERVIEW (Uma Tier List) ---
    with tab1:
        st.subheader("🏁 Finals Character Tier List")
        st.markdown("""
        **Meta Score vs. Win Rate**
        - **X-Axis (Meta Score):** A weighted metric derived from *Usage Frequency* and *Winning Performance*.
        - **Y-Axis (Avg Win Rate):** The raw probability of this character winning when fielded.
        """)
        
        # Aggregate Finals Stats
        uma_stats = matches_df.groupby('Clean_Uma').agg({
            'Is_Winner': ['count', 'sum']
        }).reset_index()
        uma_stats.columns = ['Uma', 'Entries', 'Wins']
        
        # Calculate Metrics
        uma_stats['Win_Rate'] = (uma_stats['Wins'] / uma_stats['Entries']) * 100
        uma_stats['Meta_Score'] = uma_stats.apply(lambda x: calculate_score(x['Wins'], x['Entries']), axis=1)
        
        # Filter low sample size
        uma_stats = uma_stats[uma_stats['Entries'] >= 3]
        
        fig = px.scatter(
            uma_stats, 
            x='Meta_Score', 
            y='Win_Rate',
            size='Entries',
            color='Win_Rate',
            hover_name='Uma',
            title="Finals Meta: Meta Score vs Win Rate",
            labels={'Meta_Score': 'Meta Score (Impact)', 'Win_Rate': 'Win Rate (%)'},
            template='plotly_dark',
            color_continuous_scale='Viridis'
        )
        avg_score = uma_stats['Meta_Score'].mean()
        avg_win = uma_stats['Win_Rate'].mean()
        fig.add_vline(x=avg_score, line_dash="dot", annotation_text="Avg Impact")
        fig.add_hline(y=avg_win, line_dash="dot", annotation_text="Avg Win Rate")
        
        st.plotly_chart(style_fig(fig), width='stretch', config=PLOT_CONFIG)
        
        with st.expander("💡 Suggestions to improve this view"):
            st.markdown("""
            - **Tier Bands:** Add background colored regions (S, A, B Tier) based on standard deviations from the mean.
            - **Role Split:** Split the chart into "Runners", "Leaders", etc., to see which strategy dominated.
            - **Trend Line:** Add a regression line to see if higher usage actually correlates with higher win rates (detecting "Overused" vs "Meta" units).
            """)

    # --- TAB 2: TEAM COMPS ---
    with tab2:
        st.subheader("⚔️ Winning Team Compositions")
        st.markdown("""
        **Most Effective Trios**
        - Teams are **normalized** (e.g., "Taiki, Oguri, Suzuka" is treated the same as "Oguri, Suzuka, Taiki").
        - **Ratio:** Shows exactly how many times this specific trio won out of how many times it was fielded.
        """)
        
        # 1. Reconstruct Teams (Order Independent)
        # Group by Player/Result -> List of Umas -> Sort List -> Join
        team_df = matches_df.groupby(['Display_IGN', 'Result']).agg({
            'Clean_Uma': lambda x: sorted(list(x)), # SORTING ensures "Taiki, Oguri" == "Oguri, Taiki"
            'Is_Winner': 'max'
        }).reset_index()
        
        team_df['Team_Comp'] = team_df['Clean_Uma'].apply(lambda x: ", ".join(x))
        
        # 2. Aggregation
        comp_stats = team_df.groupby('Team_Comp').agg({
            'Is_Winner': ['count', 'sum']
        }).reset_index()
        comp_stats.columns = ['Team', 'Entries', 'Wins']
        
        comp_stats['Win_Rate'] = (comp_stats['Wins'] / comp_stats['Entries']) * 100
        
        # Filter: Only winners
        comp_stats = comp_stats[comp_stats['Wins'] >= 1]
        comp_stats = comp_stats.sort_values(by=['Wins', 'Win_Rate'], ascending=False).head(15)
        
        # 3. Visualization
        # We use a combined text label for clarity
        comp_stats['Label'] = comp_stats.apply(lambda x: f"<b>{int(x['Win_Rate'])}%</b> ({int(x['Wins'])}/{int(x['Entries'])})", axis=1)
        
        fig = px.bar(
            comp_stats, 
            x='Wins', # Use raw wins for bar length to emphasize Impact
            y='Team', 
            orientation='h',
            text='Label',
            title="Top Winning Teams (Sorted by Total Wins)",
            template='plotly_dark', 
            color='Win_Rate', 
            color_continuous_scale='Plasma',
            labels={'Wins': 'Total Wins', 'Team': 'Composition', 'Win_Rate': 'Win Rate %'}
        )
        fig.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(style_fig(fig), width='stretch', config=PLOT_CONFIG)

    # --- TAB 3: SKILL LIFT ---
    with tab3:
        st.subheader("⚡ Skill Lift Analysis")
        st.markdown("""
        **Champions vs. The Field**
        Compares skill usage between **Finals Winners** and the **Prelims Baseline (Non-Winners)**.
        - **Lift:** Positive means the skill is used *more* by champions.
        - **⚠️ Warning:** Skills with a Baseline of 0% (Infinite Lift) are highlighted.
        """)
        
        if finals_ocr.empty or prelims_baseline.empty:
            st.warning("Need both Finals OCR and Prelims OCR data (with valid IGNs) to calculate lift.")
        else:
            # 1. Filters
            c1, c2 = st.columns(2)
            with c1:
                # Filter Winners (Aces Only) from Finals OCR
                winners_ocr = finals_ocr[finals_ocr['Is_Winner'] == 1].copy()
                if 'Clean_Role' in winners_ocr.columns:
                    winners_ocr = winners_ocr[winners_ocr['Clean_Role'].str.contains('Ace', case=False, na=False)]
                
                # Available Umas: Union of Winners and Baseline
                all_umas = sorted(list(set(winners_ocr['Match_Uma'].unique()) | set(prelims_baseline['Match_Uma'].unique()))) if 'Match_Uma' in prelims_baseline.columns else sorted(winners_ocr['Match_Uma'].unique())
                avail_umas = ["All"] + all_umas
                
                sel_uma = st.selectbox("Filter by Character:", avail_umas, key="lift_uma")
            
            with c2:
                avail_styles = ["All"] + sorted(winners_ocr['Clean_Style'].unique())
                sel_style = st.selectbox("Filter by Style:", avail_styles, key="lift_style")
            
            # 2. Apply Filters
            winners_filtered = winners_ocr.copy()
            prelims_filtered = prelims_baseline.copy()
            
            if sel_uma != "All":
                winners_filtered = winners_filtered[winners_filtered['Match_Uma'] == sel_uma]
                if 'Match_Uma' in prelims_filtered.columns:
                     prelims_filtered = prelims_filtered[prelims_filtered['Match_Uma'] == sel_uma]
            
            if sel_style != "All":
                winners_filtered = winners_filtered[winners_filtered['Clean_Style'] == sel_style]
                # Prelims usually lack style info in Parquet unless merged. Use global baseline if needed.
            
            # Significance Check
            n_winners = len(winners_filtered)
            if n_winners < 5:
                st.caption(f"⚠️ Warning: Sample size for Winners is small (N={n_winners}). Data may be noisy.")
            
            if winners_filtered.empty:
                st.warning("No winning data found for this selection.")
            else:
                # 3. Calculate Frequencies
                def get_freq(df):
                    if 'skills' not in df.columns or df.empty: return pd.Series()
                    # Clean skills
                    s = df['skills']
                    if s.dtype == object and isinstance(s.iloc[0], str):
                         s = s.astype(str).str.replace(r"[\[\]']", "", regex=True).str.split(',')
                    exploded = s.explode().str.strip()
                    exploded = exploded[exploded != ""]
                    return exploded.value_counts(normalize=True) * 100

                win_freq = get_freq(winners_filtered).rename("Winner %")
                base_freq = get_freq(prelims_filtered).rename("Baseline %")
                
                # 4. Merge & Lift
                lift_df = pd.concat([win_freq, base_freq], axis=1).fillna(0)
                lift_df['Lift'] = lift_df['Winner %'] - lift_df['Baseline %']
                
                # 5. Handling 0% Baseline (Infinite Lift visual cue)
                lift_df['Is_New_Tech'] = lift_df['Baseline %'] == 0
                
                # Filter noise (Must be in at least 10% of winners to matter)
                lift_df = lift_df[lift_df['Winner %'] > 10]
                
                # Top Positive Lift
                top_lift = lift_df.sort_values('Lift', ascending=False).head(20)
                
                # Color logic: Highlight "New Tech" (0 baseline) vs regular Lift
                top_lift['Color'] = top_lift['Is_New_Tech'].apply(lambda x: '#FFD700' if x else '#00CC96') # Gold for New, Green for Lift
                
                fig_lift = px.bar(
                    top_lift, x='Lift', y=top_lift.index, orientation='h',
                    title=f"Skill Lift: Winners (N={n_winners}) vs Baseline (N={len(prelims_filtered)})",
                    labels={'index': 'Skill', 'Lift': 'Usage Increase (%)'},
                    color='Is_New_Tech', 
                    color_discrete_map={True: '#FFD700', False: '#00CC96'},
                    template='plotly_dark',
                    hover_data=['Winner %', 'Baseline %']
                )
                
                # Custom tooltip to explain the 0 baseline
                fig_lift.update_traces(hovertemplate="<b>%{y}</b><br>Lift: %{x:.1f}%<br>Winner: %{customdata[0]:.1f}%<br>Baseline: %{customdata[1]:.1f}%<extra></extra>")
                
                fig_lift.update_layout(
                    yaxis={'categoryorder':'total ascending'}, 
                    showlegend=True, 
                    legend_title_text="Is New Tech? (0% Baseline)"
                )
                st.plotly_chart(style_fig(fig_lift), width='stretch', config=PLOT_CONFIG)

    # --- TAB 4: CHAMPION STATS ---
    with tab4:
        st.subheader("🏆 Champion Stat Distribution")
        st.markdown("""
        **Benchmarks: Champions vs. The Field**
        - **Green (Champions):** Stats of Umas that **WON** the Finals.
        - **Red (The Field):** Stats of Umas from the **Prelims** (excluding the Champions).
        """)
        
        if not finals_ocr.empty and not prelims_baseline.empty:
            # Filters
            c1, c2 = st.columns(2)
            with c1:
                # Union of available names
                all_umas_stat = sorted(list(set(finals_ocr['Match_Uma'].unique()) | set(prelims_baseline['Match_Uma'].unique()))) if 'Match_Uma' in prelims_baseline.columns else sorted(finals_ocr['Match_Uma'].unique())
                sel_uma_stat = st.selectbox("Filter by Character:", ["All"] + all_umas_stat, key="stat_uma")
            with c2:
                all_styles_stat = sorted(finals_ocr['Clean_Style'].unique())
                sel_style_stat = st.selectbox("Filter by Style:", ["All"] + all_styles_stat, key="stat_style")
            
            # Prepare Dataframes
            # Group A: Finals Winners
            winners_df = finals_ocr[finals_ocr['Is_Winner'] == 1].copy()
            winners_df['Group'] = 'Champions (Finals Winners)'
            
            # Group B: Prelims Baseline (The Field)
            # We must ensure columns match for concatenation
            field_df = prelims_baseline.copy()
            field_df['Group'] = 'The Field (Prelims Non-Winners)'
            
            # Align Columns for Melting
            stat_cols = ['Speed', 'Stamina', 'Power', 'Guts', 'Wit']
            
            # Apply Filters
            if sel_uma_stat != "All":
                winners_df = winners_df[winners_df['Match_Uma'] == sel_uma_stat]
                if 'Match_Uma' in field_df.columns:
                    field_df = field_df[field_df['Match_Uma'] == sel_uma_stat]
            
            if sel_style_stat != "All":
                winners_df = winners_df[winners_df['Clean_Style'] == sel_style_stat]
                # Prelims might not have style, so we might keep all or try to match if column exists
                if 'Clean_Style' in field_df.columns:
                     field_df = field_df[field_df['Clean_Style'] == sel_style_stat]

            # Combine
            # Ensure both have the stat cols
            valid_cols = [c for c in stat_cols if c in winners_df.columns and c in field_df.columns]
            
            if valid_cols and not winners_df.empty and not field_df.empty:
                combined_stats = pd.concat([
                    winners_df[valid_cols + ['Group']], 
                    field_df[valid_cols + ['Group']]
                ])
                
                melted = combined_stats.melt(id_vars=['Group'], value_vars=valid_cols, var_name='Stat', value_name='Value')
                
                fig_box = px.box(
                    melted, x='Stat', y='Value', color='Group',
                    template='plotly_dark',
                    title=f"Stat Benchmark: {sel_uma_stat} ({sel_style_stat})",
                    color_discrete_map={'Champions (Finals Winners)': '#00CC96', 'The Field (Prelims Non-Winners)': '#EF553B'}
                )
                st.plotly_chart(style_fig(fig_box), width='stretch', config=PLOT_CONFIG)
            else:
                st.warning("Insufficient data for this combination (Missing stats or empty groups).")
        else:
            st.info("Missing Finals or Prelims data.")