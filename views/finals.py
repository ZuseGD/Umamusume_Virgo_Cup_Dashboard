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
    prelims_pq = current_config.get('parquet_file') 
    prelims_csv = current_config.get('sheet_url') 
    
    if not csv_path:
        st.info("🚫 No Finals data configured.")
        return

    with st.spinner("Crunching Finals Data..."):
        matches_df, finals_ocr = load_finals_data(csv_path, pq_path)
        prelims_raw = load_ocr_data(prelims_pq)
        sheet_df, _ = load_data(prelims_csv)
    
    if matches_df.empty:
        st.warning("⚠️ Could not load Finals CSV.")
        return

    # --- DATA PREP ---
    winning_igns = set(matches_df[matches_df['Is_Winner'] == 1]['Match_IGN'].unique())
    
    prelims_df = prelims_raw.copy()
    if not prelims_df.empty and 'ign' in prelims_df.columns:
        prelims_df['Match_IGN'] = prelims_df['ign'].astype(str).str.lower().str.strip()
        prelims_baseline = prelims_df[~prelims_df['Match_IGN'].isin(winning_igns)]
    else:
        prelims_baseline = prelims_df

    # --- METRICS ---
    total_entries = matches_df['Display_IGN'].nunique()
    total_winners = matches_df[matches_df['Is_Winner'] == 1]['Display_IGN'].nunique()
    winners_with_scan = finals_ocr[finals_ocr['Is_Winner'] == 1]['Display_IGN'].nunique() if not finals_ocr.empty else 0

    m1, m2, m3 = st.columns(3)
    m1.metric("Finalists Analyzed", total_entries)
    m2.metric("Winners Confirmed", total_winners)
    m3.metric("Winners w/ Scan Data", f"{winners_with_scan}")
    
    st.markdown("---")

    # --- TABS ---
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Meta Overview", 
        "⚔️ Team Comps", 
        "⚡ Skill Lift", 
        "🏆 Champion Stats",
        "🌐 Global Stats",
        "💸 Economics & Cards"
    ])

    # --- TAB 1: META OVERVIEW ---
    with tab1:
        st.subheader("🏁 Finals Character Tier List")
        uma_stats = matches_df.groupby('Clean_Uma').agg({
            'Is_Winner': ['count', 'sum']
        }).reset_index()
        uma_stats.columns = ['Uma', 'Entries', 'Wins']
        
        uma_stats['Win_Rate'] = (uma_stats['Wins'] / uma_stats['Entries']) * 100
        uma_stats['Meta_Score'] = uma_stats.apply(lambda x: calculate_score(x['Wins'], x['Entries']), axis=1)
        uma_stats = uma_stats[uma_stats['Entries'] >= 3]
        
        if not uma_stats.empty:
            slope, intercept = np.polyfit(uma_stats['Meta_Score'], uma_stats['Win_Rate'], 1)
            x_trend = np.linspace(uma_stats['Meta_Score'].min(), uma_stats['Meta_Score'].max(), 100)
            y_trend = slope * x_trend + intercept

            mean_s = uma_stats['Meta_Score'].mean()
            std_s = uma_stats['Meta_Score'].std()
            max_s = uma_stats['Meta_Score'].max() * 1.1

            fig = px.scatter(
                uma_stats, x='Meta_Score', y='Win_Rate', size='Entries', color='Win_Rate',
                hover_name='Uma', title="Finals Meta: Impact vs Efficiency",
                template='plotly_dark', color_continuous_scale='Viridis'
            )
            fig.add_trace(go.Scatter(x=x_trend, y=y_trend, mode='lines', name='Trend', line=dict(color='white', width=2, dash='dash'), opacity=0.5))
            
            # Bands
            fig.add_vrect(x0=mean_s + std_s, x1=max_s, fillcolor="purple", opacity=0.15, annotation_text="S Tier")
            fig.add_vrect(x0=mean_s, x1=mean_s + std_s, fillcolor="green", opacity=0.1, annotation_text="A Tier")
            fig.add_vrect(x0=mean_s - std_s, x1=mean_s, fillcolor="yellow", opacity=0.05, annotation_text="B Tier")
            fig.add_vrect(x0=0, x1=mean_s - std_s, fillcolor="red", opacity=0.05, annotation_text="C Tier")

            st.plotly_chart(style_fig(fig), width='stretch', config=PLOT_CONFIG)
        else:
            st.info("Not enough data.")

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
            title="Top Winning Teams", template='plotly_dark', color='Win_Rate', color_continuous_scale='Plasma'
        )
        fig.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(style_fig(fig), width='stretch', config=PLOT_CONFIG)

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

    # --- TAB 5: GLOBAL STATS (Updated with Placements) ---
    with tab5:
        st.subheader("🌐 Global Event Statistics")
        
        # 1. Placement Counts Table
        st.markdown("##### 🏅 Finals Placement Breakdown (Counts)")
        
        def norm_res(r):
            r = str(r).lower()
            if '1st' in r: return '1st'
            if '2nd' in r: return '2nd'
            if '3rd' in r: return '3rd'
            return 'Other'

        matches_df['Clean_Result'] = matches_df['Result'].apply(norm_res)
        
        place_pivot = matches_df.pivot_table(
            index='Clean_Uma', columns='Clean_Result', values='Match_IGN', aggfunc='count', fill_value=0
        )
        # Ensure columns exist
        for c in ['1st', '2nd', '3rd']:
            if c not in place_pivot.columns: place_pivot[c] = 0
            
        place_pivot['Total'] = place_pivot.sum(axis=1)
        place_pivot = place_pivot.sort_values(['1st', '2nd', '3rd'], ascending=False).head(20)
        
        # Display as a clean dataframe
        st.dataframe(place_pivot[['1st', '2nd', '3rd', 'Total']], width='stretch')
        
        # 2. Placement Chart (Percentage)
        st.markdown("##### 📊 Placement Distribution (%)")
        place_long = place_pivot.reset_index().melt(id_vars='Clean_Uma', value_vars=['1st', '2nd', '3rd'], var_name='Place', value_name='Count')
        place_long['Pct'] = place_long.apply(lambda x: (x['Count'] / place_pivot.loc[x['Clean_Uma'], 'Total']) * 100, axis=1)
        
        fig_place = px.bar(
            place_long, x='Pct', y='Clean_Uma', color='Place', orientation='h',
            title="Placement Shares (Top 20)", template='plotly_dark',
            color_discrete_map={'1st': '#FFD700', '2nd': '#C0C0C0', '3rd': '#CD7F32'}
        )
        fig_place.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(style_fig(fig_place), width='stretch', config=PLOT_CONFIG)

    # --- TAB 6: ECONOMICS & CARDS ---
    with tab6:
        st.subheader("💸 Economics & Investment Analysis")
        st.markdown("Impact of **Spending** and **Support Cards** on Finals Results.")
        
        # Filter for valid data
        econ_df = matches_df[matches_df['Spending_Text'] != 'Unknown'].copy()
        
        if econ_df.empty:
            st.warning("No spending data found in CSV.")
        else:
            c1, c2 = st.columns(2)
            
            # 1. Spending vs Win Rate
            with c1:
                st.markdown("##### 💰 Win Rate by Spending Tier")
                spend_stats = econ_df.groupby('Spending_Text').agg({
                    'Is_Winner': ['mean', 'count'],
                    'Sort_Money': 'mean' # Used for sorting
                }).reset_index()
                spend_stats.columns = ['Tier', 'Win_Rate', 'Entries', 'Sort_Val']
                spend_stats['Win_Rate'] *= 100
                spend_stats = spend_stats.sort_values('Sort_Val')
                
                fig_spend = px.bar(
                    spend_stats, x='Tier', y='Win_Rate', text='Entries',
                    title="Win Rate per Spending Bracket",
                    labels={'Tier': 'Total Spent', 'Win_Rate': 'Win Rate (%)', 'Entries': 'Entries'},
                    template='plotly_dark', color='Win_Rate', color_continuous_scale='Greens'
                )
                fig_spend.update_traces(texttemplate='%{text} Entries', textposition='outside')
                st.plotly_chart(style_fig(fig_spend), width='stretch', config=PLOT_CONFIG)
            
            # 2. Spending Distribution by Result
            with c2:
                st.markdown("##### 📉 Spending Distribution by Result")
                # Group by Team (Player) to avoid triple counting spending per horse
                player_df = econ_df.drop_duplicates(subset=['Display_IGN'])
                
                # Sort categories manually if possible, else rely on Sort_Money
                fig_box = px.box(
                    player_df, x='Clean_Result', y='Sort_Money', color='Clean_Result',
                    title="Spending Range vs Placement",
                    labels={'Sort_Money': 'Est. Spending ($)', 'Clean_Result': 'Finals Result'},
                    template='plotly_dark', 
                    category_orders={'Clean_Result': ['1st', '2nd', '3rd', 'Other']}
                )
                st.plotly_chart(style_fig(fig_box), width='stretch', config=PLOT_CONFIG)

            st.markdown("---")
            st.subheader("🃏 Support Card Impact")
            
            # 3. Kitasan Black Impact
            st.markdown("##### 🏃 Speed SSR: Kitasan Black")
            if 'Card_Kitasan' in econ_df.columns:
                kitasan_stats = econ_df.groupby('Card_Kitasan').agg({'Is_Winner': ['mean', 'count']}).reset_index()
                kitasan_stats.columns = ['Level', 'Win_Rate', 'Entries']
                kitasan_stats['Win_Rate'] *= 100
                # Filter small samples
                kitasan_stats = kitasan_stats[kitasan_stats['Entries'] > 5].sort_values('Win_Rate', ascending=False)
                
                fig_kita = px.bar(
                    kitasan_stats, x='Level', y='Win_Rate', color='Entries',
                    title="Win Rate by Kitasan Level", template='plotly_dark'
                )
                st.plotly_chart(style_fig(fig_kita, height=400), width='stretch', config=PLOT_CONFIG)
            
            # 4. Fine Motion Impact
            st.markdown("##### 🧠 Wit SSR: Fine Motion")
            if 'Card_Fine' in econ_df.columns:
                fine_stats = econ_df.groupby('Card_Fine').agg({'Is_Winner': ['mean', 'count']}).reset_index()
                fine_stats.columns = ['Level', 'Win_Rate', 'Entries']
                fine_stats['Win_Rate'] *= 100
                fine_stats = fine_stats[fine_stats['Entries'] > 5].sort_values('Win_Rate', ascending=False)
                
                fig_fine = px.bar(
                    fine_stats, x='Level', y='Win_Rate', color='Entries',
                    title="Win Rate by Fine Motion Level", template='plotly_dark'
                )
                st.plotly_chart(style_fig(fig_fine, height=400), width='stretch', config=PLOT_CONFIG)