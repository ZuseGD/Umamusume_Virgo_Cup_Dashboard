import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from virgo_utils import load_finals_data, load_ocr_data, load_data, style_fig, PLOT_CONFIG, calculate_score, SHEET_URL

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
        # Load Finals (CSV + OCR Merge)
        matches_df, finals_ocr = load_finals_data(csv_path, pq_path)
        
        # Load Prelims (Baseline) - OCR Data for Stat Comparison
        prelims_raw = load_ocr_data(prelims_pq)
        
        # Load Prelims (Rounds) - Sheet Data for Race Counts
        sheet_df, _ = load_data(SHEET_URL)
    
    if matches_df.empty:
        st.warning("⚠️ Could not load Finals CSV.")
        return

    # --- 2. DATA PREPARATION: EXCLUDE WINNERS FROM BASELINE ---
    # We want "The Field" (Prelims) to NOT include the "Champions" (Finals Winners)
    
    # Identify Winning IGNs
    winning_igns = set(matches_df[matches_df['Is_Winner'] == 1]['Match_IGN'].unique())
    
    # Prepare Baseline (Prelims)
    prelims_df = prelims_raw.copy()
    if not prelims_df.empty and 'ign' in prelims_df.columns:
        prelims_df['Match_IGN'] = prelims_df['ign'].astype(str).str.lower().str.strip()
        # FILTER: Exclude Finals Winners from Prelims Data
        prelims_baseline = prelims_df[~prelims_df['Match_IGN'].isin(winning_igns)]
        excluded_count = len(prelims_df) - len(prelims_baseline)
    else:
        prelims_baseline = prelims_df
        excluded_count = 0

    # --- METRICS ---
    total_entries = matches_df['Display_IGN'].nunique()
    total_winners = matches_df[matches_df['Is_Winner'] == 1]['Display_IGN'].nunique()
    
    winners_with_scan = 0
    if not finals_ocr.empty:
        winners_with_scan = finals_ocr[finals_ocr['Is_Winner'] == 1]['Display_IGN'].nunique()

    m1, m2, m3 = st.columns(3)
    m1.metric("Finalists Analyzed", total_entries)
    m2.metric("Winners Confirmed", total_winners)
    m3.metric("Winners w/ Scan Data", f"{winners_with_scan}", 
              help=f"Only {winners_with_scan} out of {total_winners} winners have valid OCR data matched.")
    
    st.markdown("---")

    # --- TABS ---
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Meta Overview", 
        "⚔️ Team Comps", 
        "⚡ Skill Lift", 
        "🏆 Champion Stats",
        "🌐 Global Stats"
    ])

    # --- TAB 1: META OVERVIEW (Uma Tier List) ---
    with tab1:
        st.subheader("🏁 Finals Character Tier List")
        st.markdown("""
        **Meta Score vs. Win Rate**
        - **Meta Score (X-Axis):** Weighted metric of usage & performance.
        - **Win Rate (Y-Axis):** Raw probability of winning.
        - **Trend Line:** Dashed line showing the correlation between Meta Score and Win Rate.
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
        
        if not uma_stats.empty:
            # Trend Line
            slope, intercept = np.polyfit(uma_stats['Meta_Score'], uma_stats['Win_Rate'], 1)
            x_trend = np.linspace(uma_stats['Meta_Score'].min(), uma_stats['Meta_Score'].max(), 100)
            y_trend = slope * x_trend + intercept

            # Tiers
            mean_score = uma_stats['Meta_Score'].mean()
            std_score = uma_stats['Meta_Score'].std()
            max_score = uma_stats['Meta_Score'].max() * 1.1
            min_score = 0
            
            fig = px.scatter(
                uma_stats, 
                x='Meta_Score', 
                y='Win_Rate',
                size='Entries',
                color='Win_Rate',
                hover_name='Uma',
                title="Finals Meta: Impact vs Efficiency",
                labels={'Meta_Score': 'Meta Score (Impact)', 'Win_Rate': 'Win Rate (%)'},
                template='plotly_dark',
                color_continuous_scale='Viridis'
            )
            
            # Add Trend Line
            fig.add_trace(go.Scatter(
                x=x_trend, y=y_trend, mode='lines', name='Trend', 
                line=dict(color='white', width=2, dash='dash'),
                opacity=0.5
            ))

            # Add Tier Bands
            fig.add_vrect(x0=mean_score + std_score, x1=max_score, fillcolor="purple", opacity=0.15, annotation_text="S Tier")
            fig.add_vrect(x0=mean_score, x1=mean_score + std_score, fillcolor="green", opacity=0.1, annotation_text="A Tier")
            fig.add_vrect(x0=mean_score - std_score, x1=mean_score, fillcolor="yellow", opacity=0.05, annotation_text="B Tier")
            fig.add_vrect(x0=min_score, x1=mean_score - std_score, fillcolor="red", opacity=0.05, annotation_text="C Tier")

            st.plotly_chart(style_fig(fig), width='stretch', config=PLOT_CONFIG)
        else:
            st.info("Not enough data to generate tier list.")

    # --- TAB 2: TEAM COMPS ---
    with tab2:
        st.subheader("⚔️ Winning Team Compositions")
        st.markdown("**Most Effective Trios (Normalized)**")
        
        team_df = matches_df.groupby(['Display_IGN', 'Result']).agg({
            'Clean_Uma': lambda x: sorted(list(x)), 
            'Is_Winner': 'max'
        }).reset_index()
        
        team_df['Team_Comp'] = team_df['Clean_Uma'].apply(lambda x: ", ".join(x))
        
        comp_stats = team_df.groupby('Team_Comp').agg({
            'Is_Winner': ['count', 'sum']
        }).reset_index()
        comp_stats.columns = ['Team', 'Entries', 'Wins']
        
        comp_stats['Win_Rate'] = (comp_stats['Wins'] / comp_stats['Entries']) * 100
        comp_stats = comp_stats[comp_stats['Wins'] >= 1].sort_values(by=['Wins', 'Win_Rate'], ascending=False).head(15)
        comp_stats['Label'] = comp_stats.apply(lambda x: f"<b>{int(x['Win_Rate'])}%</b> ({int(x['Wins'])}/{int(x['Entries'])})", axis=1)
        
        fig = px.bar(
            comp_stats, x='Wins', y='Team', orientation='h', text='Label',
            title="Top Winning Teams (Sorted by Total Wins)",
            template='plotly_dark', color='Win_Rate', color_continuous_scale='Plasma'
        )
        fig.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(style_fig(fig), width='stretch', config=PLOT_CONFIG)

    # --- TAB 3: SKILL LIFT ---
    with tab3:
        st.subheader("⚡ Skill Lift Analysis")
        st.markdown("**Champions vs. The Field**")
        
        if finals_ocr.empty or prelims_baseline.empty:
            st.warning("⚠️ Insufficient data (Need Finals OCR + Prelims OCR).")
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
            
            winners_filtered = winners_ocr.copy()
            prelims_filtered = prelims_baseline.copy()
            
            if sel_uma != "All":
                winners_filtered = winners_filtered[winners_filtered['Match_Uma'] == sel_uma]
                if 'Match_Uma' in prelims_filtered.columns:
                     prelims_filtered = prelims_filtered[prelims_filtered['Match_Uma'] == sel_uma]
            
            if sel_style != "All":
                winners_filtered = winners_filtered[winners_filtered['Clean_Style'] == sel_style]
            
            n_winners = len(winners_filtered)
            n_baseline = len(prelims_filtered)
            
            if n_winners == 0:
                st.warning("No winning data found (Likely missing OCR data).")
            else:
                if n_winners < 10: st.caption(f"⚠️ Low Sample Size: {n_winners} winners vs {n_baseline} baseline.")

                def get_freq(df):
                    if 'skills' not in df.columns or df.empty: return pd.Series()
                    s = df['skills']
                    if s.dtype == object and isinstance(s.iloc[0], str):
                         s = s.astype(str).str.replace(r"[\[\]']", "", regex=True).str.split(',')
                    exploded = s.explode().str.strip()
                    exploded = exploded[exploded != ""]
                    return exploded.value_counts(normalize=True) * 100

                lift_df = pd.concat([get_freq(winners_filtered).rename("Winner %"), get_freq(prelims_filtered).rename("Baseline %")], axis=1).fillna(0)
                lift_df['Lift'] = lift_df['Winner %'] - lift_df['Baseline %']
                lift_df['Is_New_Tech'] = lift_df['Baseline %'] == 0
                lift_df = lift_df[lift_df['Winner %'] > 5]
                
                if lift_df.empty:
                    st.info("No significant skill differences found.")
                else:
                    top_lift = lift_df.sort_values('Lift', ascending=False).head(20)
                    top_lift['Color'] = top_lift['Is_New_Tech'].apply(lambda x: '#FFD700' if x else '#00CC96')
                    
                    fig_lift = px.bar(
                        top_lift, x='Lift', y=top_lift.index, orientation='h',
                        title=f"Skill Lift: Winners (N={n_winners}) vs Baseline (N={n_baseline})",
                        color='Is_New_Tech', color_discrete_map={True: '#FFD700', False: '#00CC96'},
                        template='plotly_dark', hover_data=['Winner %', 'Baseline %']
                    )
                    fig_lift.update_traces(hovertemplate="<b>%{y}</b><br>Lift: %{x:.1f}%<br>Winner: %{customdata[0]:.1f}%<br>Baseline: %{customdata[1]:.1f}%")
                    fig_lift.update_layout(yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(style_fig(fig_lift), width='stretch', config=PLOT_CONFIG)

    # --- TAB 4: CHAMPION STATS ---
    with tab4:
        st.subheader("🏆 Champion Stat Distribution")
        
        if not finals_ocr.empty and not prelims_baseline.empty:
            c1, c2 = st.columns(2)
            with c1:
                all_umas_stat = sorted(list(set(finals_ocr['Match_Uma'].unique()) | set(prelims_baseline['Match_Uma'].unique()))) if 'Match_Uma' in prelims_baseline.columns else sorted(finals_ocr['Match_Uma'].unique())
                sel_uma_stat = st.selectbox("Filter by Character:", ["All"] + all_umas_stat, key="stat_uma")
            with c2:
                sel_style_stat = st.selectbox("Filter by Style:", ["All"] + sorted(finals_ocr['Clean_Style'].unique()), key="stat_style")
            
            winners_df = finals_ocr[finals_ocr['Is_Winner'] == 1].copy()
            winners_df['Group'] = 'Champions (Finals Winners)'
            field_df = prelims_baseline.copy()
            field_df['Group'] = 'The Field (Prelims Non-Winners)'
            
            if sel_uma_stat != "All":
                winners_df = winners_df[winners_df['Match_Uma'] == sel_uma_stat]
                if 'Match_Uma' in field_df.columns: field_df = field_df[field_df['Match_Uma'] == sel_uma_stat]
            if sel_style_stat != "All":
                winners_df = winners_df[winners_df['Clean_Style'] == sel_style_stat]
                if 'Clean_Style' in field_df.columns: field_df = field_df[field_df['Clean_Style'] == sel_style_stat]

            valid_cols = [c for c in ['Speed', 'Stamina', 'Power', 'Guts', 'Wit'] if c in winners_df.columns and c in field_df.columns]
            
            if valid_cols and not winners_df.empty and not field_df.empty:
                combined_stats = pd.concat([winners_df[valid_cols + ['Group']], field_df[valid_cols + ['Group']]])
                melted = combined_stats.melt(id_vars=['Group'], value_vars=valid_cols, var_name='Stat', value_name='Value')
                
                fig_box = px.box(
                    melted, x='Stat', y='Value', color='Group', template='plotly_dark',
                    title=f"Stat Benchmark: {sel_uma_stat}",
                    color_discrete_map={'Champions (Finals Winners)': '#00CC96', 'The Field (Prelims Non-Winners)': '#EF553B'}
                )
                st.plotly_chart(style_fig(fig_box), width='stretch', config=PLOT_CONFIG)
            else:
                st.warning("Insufficient data.")
        else:
            st.info("Missing data.")

    # --- TAB 5: GLOBAL STATS ---
    with tab5:
        st.subheader("🌐 Global Event Statistics")
        st.markdown("""
        **Combined Analysis (Prelims + Finals)**
        - **Total Usage:** Counts actual *Races Run* (Prelims) + *Finals Entries*.
        - **Placement Distribution:** Breakdown of 1st, 2nd, and 3rd place finishes in the Finals.
        """)

        col_g1, col_g2 = st.columns(2)
        
        # --- 1. GLOBAL USAGE (Races Run) ---
        # Prelims: Sum of 'Clean_Races' from Sheet Data
        if not sheet_df.empty:
            prelim_usage = sheet_df.groupby('Clean_Uma')['Clean_Races'].sum()
        else:
            prelim_usage = pd.Series(dtype=int)
            
        # Finals: Count of Entries (1 Race per Entry)
        finals_usage = matches_df['Clean_Uma'].value_counts()
        
        # Combine
        total_usage = prelim_usage.add(finals_usage, fill_value=0).sort_values(ascending=False).head(20)
        
        with col_g1:
            st.markdown("##### 🏃 Highest Usage (Total Races Run)")
            if not total_usage.empty:
                fig_usage = px.bar(
                    total_usage, x=total_usage.values, y=total_usage.index, orientation='h',
                    title="Most Used Umas (Prelims Races + Finals Entries)",
                    labels={'x': 'Total Races Run', 'index': 'Uma'},
                    template='plotly_dark', color=total_usage.values, color_continuous_scale='Bluered'
                )
                fig_usage.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(style_fig(fig_usage, height=500), width='stretch', config=PLOT_CONFIG)
            else:
                st.warning("No usage data available.")

        # --- 2. FINALS PLACEMENT DISTRIBUTION ---
        with col_g2:
            st.markdown("##### 🏅 Finals Placement Breakdown")
            # Filter for Top Umas in Finals only (to keep chart clean)
            top_finalists = matches_df['Clean_Uma'].value_counts().head(15).index.tolist()
            filtered_matches = matches_df[matches_df['Clean_Uma'].isin(top_finalists)]
            
            # Normalize Results
            def normalize_result(res):
                res = str(res).lower()
                if '1st' in res: return '1st'
                if '2nd' in res: return '2nd'
                if '3rd' in res: return '3rd'
                return 'Other'
            
            filtered_matches['Clean_Result'] = filtered_matches['Result'].apply(normalize_result)
            
            # Calculate Percentages
            placement_counts = filtered_matches.groupby(['Clean_Uma', 'Clean_Result']).size().reset_index(name='Count')
            total_counts = filtered_matches.groupby('Clean_Uma').size().reset_index(name='Total')
            
            placement_df = pd.merge(placement_counts, total_counts, on='Clean_Uma')
            placement_df['Percentage'] = (placement_df['Count'] / placement_df['Total']) * 100
            
            # Sort by 1st Place Rate
            order_idx = placement_df[placement_df['Clean_Result'] == '1st'].sort_values('Percentage', ascending=False)['Clean_Uma']
            
            if not placement_df.empty:
                fig_place = px.bar(
                    placement_df, x='Percentage', y='Clean_Uma', color='Clean_Result',
                    orientation='h',
                    title="Placement Distribution (Top 15 Finalists)",
                    category_orders={"Clean_Result": ["1st", "2nd", "3rd", "Other"], "Clean_Uma": order_idx.tolist()},
                    color_discrete_map={"1st": "#FFD700", "2nd": "#C0C0C0", "3rd": "#CD7F32", "Other": "#333333"},
                    template='plotly_dark',
                    text_auto='.0f'
                )
                fig_place.update_layout(barmode='stack', yaxis={'categoryorder':'array', 'categoryarray': order_idx.tolist()[::-1]})
                st.plotly_chart(style_fig(fig_place, height=500), width='stretch', config=PLOT_CONFIG)
            else:
                st.warning("No placement data available.")

        # --- 3. EXTRA: TOP 3 CONSISTENCY ---
        st.markdown("---")
        st.markdown("##### 💎 The Consistency Kings")
        st.markdown("Characters with the highest rate of finishing in the **Top 3** (Podium Finish).")
        
        # Calculate Podium Rate for Finals
        podium_df = matches_df.copy()
        podium_df['Is_Podium'] = podium_df['Result'].apply(lambda x: 1 if x in ['1st', '2nd', '3rd'] else 0)
        
        podium_stats = podium_df.groupby('Clean_Uma').agg({
            'Is_Podium': 'sum',
            'Match_IGN': 'count' # Total Entries
        }).reset_index()
        podium_stats.columns = ['Uma', 'Podiums', 'Entries']
        
        # Filter for significant sample size
        podium_stats = podium_stats[podium_stats['Entries'] >= 5]
        podium_stats['Podium_Rate'] = (podium_stats['Podiums'] / podium_stats['Entries']) * 100
        podium_stats = podium_stats.sort_values('Podium_Rate', ascending=False).head(10)
        
        if not podium_stats.empty:
            fig_podium = px.bar(
                podium_stats, x='Uma', y='Podium_Rate',
                title="Top 3 Finish Rate (Min. 5 Entries)",
                labels={'Podium_Rate': 'Podium % (Top 3)'},
                color='Podium_Rate', color_continuous_scale='Teal', template='plotly_dark'
            )
            st.plotly_chart(style_fig(fig_podium), width='stretch', config=PLOT_CONFIG)