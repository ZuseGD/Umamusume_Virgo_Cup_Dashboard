import streamlit as st
import plotly.express as px
import pandas as pd
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
        matches_df, merged_df = load_finals_data(csv_path, pq_path)
        # Load Prelims Baseline for "Lift" analysis
        prelims_df = load_ocr_data(prelims_pq)
    
    if matches_df.empty:
        st.warning("⚠️ Could not load Finals CSV.")
        return

    # --- METRICS ---
    total_entries = matches_df['Display_IGN'].nunique()
    total_winners = matches_df[matches_df['Is_Winner'] == 1]['Display_IGN'].nunique()
    
    # Calculate "Ace" percentage (Entries that aren't Debuffers)
    if 'Clean_Role' in matches_df.columns:
        ace_count = len(matches_df[matches_df['Clean_Role'].str.contains("Ace", case=False, na=False)])
        debuff_count = len(matches_df[matches_df['Clean_Role'].str.contains("Debuff", case=False, na=False)])
    else:
        ace_count, debuff_count = 0, 0

    m1, m2, m3 = st.columns(3)
    m1.metric("Finalists Analyzed", total_entries)
    m2.metric("Winners Confirmed", total_winners)
    m3.metric("Ace vs Debuff Ratio", f"{ace_count}:{debuff_count}")
    
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
        - **X-Axis (Meta Score):** A weighted metric derived from *Usage Frequency* and *Winning Performance*. Higher score = The defining characters of the cup.
        - **Y-Axis (Avg Win Rate):** The raw probability of this character winning when fielded.
        - **Bubble Size:** Total number of entries (Popularity).
        """)
        
        # Aggregate Finals Stats
        uma_stats = matches_df.groupby('Clean_Uma').agg({
            'Is_Winner': ['count', 'sum']
        }).reset_index()
        uma_stats.columns = ['Uma', 'Entries', 'Wins']
        
        # Calculate Metrics
        uma_stats['Win_Rate'] = (uma_stats['Wins'] / uma_stats['Entries']) * 100
        # Meta Score: We use the utility function or derived logic
        uma_stats['Meta_Score'] = uma_stats.apply(lambda x: calculate_score(x['Wins'], x['Entries']), axis=1)
        
        # Filter low sample size
        uma_stats = uma_stats[uma_stats['Entries'] >= 3]
        
        # Scatter Plot
        fig = px.scatter(
            uma_stats, 
            x='Meta_Score', 
            y='Win_Rate',
            size='Entries',
            color='Win_Rate',
            hover_name='Uma',
            text='Uma',
            title="Finals Meta: Meta Score vs Win Rate",
            labels={'Meta_Score': 'Meta Score (Impact)', 'Win_Rate': 'Win Rate (%)'},
            template='plotly_dark',
            color_continuous_scale='Viridis'
        )
        # Add quadrants
        avg_score = uma_stats['Meta_Score'].mean()
        avg_win = uma_stats['Win_Rate'].mean()
        fig.add_vline(x=avg_score, line_dash="dot", annotation_text="Avg Impact")
        fig.add_hline(y=avg_win, line_dash="dot", annotation_text="Avg Win Rate")
        fig.update_traces(textposition='top center')
        
        st.plotly_chart(style_fig(fig), use_container_width=True, config=PLOT_CONFIG)

    # --- TAB 2: TEAM COMPS ---
    with tab2:
        st.subheader("⚔️ Winning Team Compositions")
        st.markdown("""
        **Efficiency of Top Teams**
        This chart analyzes the teams that successfully took 1st place.
        - It displays the **Win Rate** of specific team compositions.
        - The text on the bar shows the **Ratio (Wins / Entries)**.
        """)
        
        # Group by Player to reconstruct teams
        # We assume 3-uma teams. We group by Player and Result.
        # Note: matches_df is long (1 row per horse). We need to aggregate back to team level.
        team_df = matches_df.groupby(['Display_IGN', 'Result']).agg({
            'Clean_Uma': lambda x: sorted(list(x)),
            'Is_Winner': 'max'
        }).reset_index()
        
        team_df['Team_Comp'] = team_df['Clean_Uma'].apply(lambda x: ", ".join(x))
        
        # Aggregate Stats per Team Comp
        comp_stats = team_df.groupby('Team_Comp').agg({
            'Is_Winner': ['count', 'sum']
        }).reset_index()
        comp_stats.columns = ['Team', 'Entries', 'Wins']
        
        # Calculate Win Rate
        comp_stats['Win_Rate'] = (comp_stats['Wins'] / comp_stats['Entries']) * 100
        
        # Filter: Only show teams that have actually won at least once
        comp_stats = comp_stats[comp_stats['Wins'] >= 1]
        
        # Sort by Wins (Most successful teams) then Win Rate
        comp_stats = comp_stats.sort_values(by=['Wins', 'Win_Rate'], ascending=False).head(15)
        
        # Create Ratio Label
        comp_stats['Ratio_Label'] = comp_stats.apply(lambda x: f"{int(x['Wins'])}/{int(x['Entries'])}", axis=1)
        
        fig = px.bar(
            comp_stats, 
            x='Win_Rate', 
            y='Team', 
            orientation='h',
            text='Ratio_Label',
            title="Top Winning Teams: Win Rate & Efficiency",
            template='plotly_dark', 
            color='Wins', 
            color_continuous_scale='Plasma',
            labels={'Win_Rate': 'Win Rate (%)', 'Team': 'Team Composition'}
        )
        fig.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(style_fig(fig), use_container_width=True, config=PLOT_CONFIG)

    # --- TAB 3: SKILL LIFT ---
    with tab3:
        st.subheader("⚡ Skill Lift Analysis")
        st.markdown("""
        **Winning Secrets**
        This chart calculates the **"Skill Lift"**: The difference in skill usage between **Finals Winners** and the **Prelims Baseline**.
        - **Positive Lift (Green):** Skills that appear *significantly more often* in winning decks. (The Meta)
        - **Negative Lift:** Skills that are common but appear *less often* in winning decks.
        """)
        
        if merged_df.empty or prelims_df.empty:
            st.warning("Need both Finals OCR and Prelims OCR data to calculate lift.")
        else:
            # 1. Filters
            c1, c2 = st.columns(2)
            with c1:
                # Filter Winners (Aces Only)
                winners_ocr = merged_df[merged_df['Is_Winner'] == 1].copy()
                if 'Clean_Role' in winners_ocr.columns:
                    winners_ocr = winners_ocr[winners_ocr['Clean_Role'].str.contains('Ace', case=False, na=False)]
                
                avail_umas = ["All"] + sorted(winners_ocr['Match_Uma'].unique())
                sel_uma = st.selectbox("Filter by Character:", avail_umas, key="lift_uma")
            
            with c2:
                avail_styles = ["All"] + sorted(winners_ocr['Clean_Style'].unique())
                sel_style = st.selectbox("Filter by Style:", avail_styles, key="lift_style")
            
            # 2. Apply Filters
            winners_filtered = winners_ocr.copy()
            prelims_filtered = prelims_df.copy() # We try to filter baseline too if possible, but matching might be hard
            
            if sel_uma != "All":
                winners_filtered = winners_filtered[winners_filtered['Match_Uma'] == sel_uma]
                # Try to filter prelims by same name logic if column exists
                if 'Match_Uma' in prelims_filtered.columns:
                     prelims_filtered = prelims_filtered[prelims_filtered['Match_Uma'] == sel_uma]
            
            if sel_style != "All":
                winners_filtered = winners_filtered[winners_filtered['Clean_Style'] == sel_style]
                # Prelims usually lack style info in Parquet unless merged. We use Global Baseline if style not found.
            
            if winners_filtered.empty:
                st.warning("No winning data found for this selection.")
            else:
                # 3. Calculate Frequencies
                def get_freq(df):
                    if 'skills' not in df.columns or df.empty: return pd.Series()
                    if df['skills'].dtype == object and isinstance(df['skills'].iloc[0], str):
                         df['skills'] = df['skills'].astype(str).str.replace(r"[\[\]']", "", regex=True).str.split(',')
                    
                    exploded = df.explode('skills')
                    exploded['skills'] = exploded['skills'].str.strip()
                    # Filter empty
                    exploded = exploded[exploded['skills'] != ""]
                    return exploded['skills'].value_counts(normalize=True) * 100

                win_freq = get_freq(winners_filtered).rename("Winner %")
                base_freq = get_freq(prelims_filtered).rename("Baseline %")
                
                # 4. Merge & Lift
                lift_df = pd.concat([win_freq, base_freq], axis=1).fillna(0)
                lift_df['Lift'] = lift_df['Winner %'] - lift_df['Baseline %']
                
                # Filter noise (Must be in at least 5% of winners to matter)
                lift_df = lift_df[lift_df['Winner %'] > 5]
                
                # Top Positive Lift
                top_lift = lift_df.sort_values('Lift', ascending=False).head(15)
                
                fig_lift = px.bar(
                    top_lift, x='Lift', y=top_lift.index, orientation='h',
                    title=f"Top High-Value Skills (Winners vs Baseline)",
                    labels={'index': 'Skill', 'Lift': 'Usage Increase (%)'},
                    color='Lift', color_continuous_scale='Tealgrn', template='plotly_dark',
                    hover_data=['Winner %', 'Baseline %']
                )
                fig_lift.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(style_fig(fig_lift), use_container_width=True, config=PLOT_CONFIG)

    # --- TAB 4: CHAMPION STATS ---
    with tab4:
        st.subheader("🏆 Champion Stat Distribution")
        st.markdown("""
        **The Stat Benchmark**
        Compare the raw stats of **Winners** against **Non-Winners** in the Finals.
        - Use the filters to drill down into specific characters and styles.
        - **Green Boxes:** The stat distribution of builds that won 1st place.
        - **Red Boxes:** The stat distribution of builds that did not win.
        """)
        
        if not merged_df.empty:
            # Filters
            c1, c2 = st.columns(2)
            with c1:
                # Get Umas present in the merged data
                all_umas = ["All"] + sorted(merged_df['Match_Uma'].unique())
                sel_uma_stat = st.selectbox("Filter by Character:", all_umas, key="stat_uma")
            with c2:
                all_styles = ["All"] + sorted(merged_df['Clean_Style'].unique())
                sel_style_stat = st.selectbox("Filter by Style:", all_styles, key="stat_style")
            
            # Apply Filters
            filtered_df = merged_df.copy()
            if sel_uma_stat != "All":
                filtered_df = filtered_df[filtered_df['Match_Uma'] == sel_uma_stat]
            if sel_style_stat != "All":
                filtered_df = filtered_df[filtered_df['Clean_Style'] == sel_style_stat]
            
            if not filtered_df.empty:
                # Label Groups
                filtered_df['Result_Group'] = filtered_df['Is_Winner'].apply(lambda x: 'Winner' if x == 1 else 'Non-Winner')
                
                stat_cols = ['Speed', 'Stamina', 'Power', 'Guts', 'Wit']
                valid_cols = [c for c in stat_cols if c in filtered_df.columns]
                
                if valid_cols:
                    melted = filtered_df.melt(id_vars=['Result_Group'], value_vars=valid_cols, var_name='Stat', value_name='Value')
                    
                    fig_box = px.box(
                        melted, x='Stat', y='Value', color='Result_Group',
                        template='plotly_dark',
                        title=f"Stat Benchmark: Winners vs Non-Winners ({sel_uma_stat}/{sel_style_stat})",
                        color_discrete_map={'Winner': '#00CC96', 'Non-Winner': '#EF553B'}
                    )
                    st.plotly_chart(style_fig(fig_box), use_container_width=True, config=PLOT_CONFIG)
                else:
                    st.warning("No stat columns found in OCR data.")
            else:
                st.info("No data found for this combination.")