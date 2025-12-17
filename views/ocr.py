import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np
from virgo_utils import style_fig, PLOT_CONFIG, load_ocr_data, load_data, load_finals_data, show_description, smart_match_name

def show_view(current_config):
    st.set_page_config(page_title="Build Analysis Dashboard", layout="wide")
    event_name = current_config.get('id', 'Event').replace('_', ' ').title()
    parquet_file = current_config.get('parquet_file', '')
    sheet_url = current_config.get('sheet_url', '')
    finals_csv = current_config.get('finals_csv', '')
    finals_pq = current_config.get('finals_parquet', '')

    st.header(f"🔬 Build Analysis: {event_name}")
    st.caption("Detailed breakdown of Stats, Skills, and Support Cards used.")

    with st.spinner("Loading Datasets..."):
        ocr_df_cached = load_ocr_data(parquet_file)
        ocr_df = ocr_df_cached.copy() if not ocr_df_cached.empty else pd.DataFrame()
        match_df_cached, _ = load_data(sheet_url)
        match_df = match_df_cached.copy() if not match_df_cached.empty else pd.DataFrame()  
        finals_matches_cached, _ = load_finals_data(finals_csv, finals_pq)
        finals_matches = finals_matches_cached.copy() if not finals_matches_cached.empty else pd.DataFrame()
        

    if ocr_df.empty:
        st.error("❌ OCR Data not available. Cannot proceed with Build Analysis.")
        return

    # --- DATA MERGING ---
    valid_names = match_df['Clean_Uma'].dropna().unique().tolist()
    ocr_df['Match_Uma'] = ocr_df['name'].apply(lambda x: smart_match_name(x, valid_names))
    
    ocr_df['Match_IGN'] = ocr_df['ign'].astype(str).str.lower().str.strip()
    match_df['Match_IGN'] = match_df['Clean_IGN'].astype(str).str.lower().str.strip()
    match_df['Match_Uma'] = match_df['Clean_Uma'].astype(str).str.strip()

    perf_df = match_df.groupby(['Match_IGN', 'Match_Uma', 'Clean_Style']).agg({
        'Calculated_WinRate': 'mean', 'Clean_Races': 'sum'
    }).reset_index()
    merged_df = pd.merge(ocr_df, perf_df, on=['Match_IGN', 'Match_Uma'], how='inner')

    st.success(f"✅ Analyzed {len(merged_df)} builds linked to performance data.")

    # --- TABS ---
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Stats", "⚡ Skills", "🃏 Support Cards", 
        "🐎 Taiki Cumulative", "🧬 Aptitude", "🆙 Unique Level"
    ])

    # --- TAB 1: STATS ---
    with tab1:
        st.subheader("🏆 Optimal Stat Distribution")
        c1, c2 = st.columns(2)
        with c1:
            sel_uma = st.selectbox("Character", ["All"] + sorted(merged_df['Match_Uma'].unique()))
        with c2:
            sel_style = st.selectbox("Style", ["All"] + sorted(merged_df['Clean_Style'].unique()))
            
        filt_df = merged_df.copy()
        if sel_uma != "All": filt_df = filt_df[filt_df['Match_Uma'] == sel_uma]
        if sel_style != "All": filt_df = filt_df[filt_df['Clean_Style'] == sel_style]
        
        if not filt_df.empty:
            cols = ['Speed', 'Stamina', 'Power', 'Guts', 'Wit']
            valid_cols = [c for c in cols if c in filt_df.columns]
            
            # Compare High WR vs Low WR
            threshold = filt_df['Calculated_WinRate'].quantile(0.75)
            filt_df['Group'] = np.where(filt_df['Calculated_WinRate'] >= threshold, 'Winners', 'Rest')
            
            fig_box = px.box(
                filt_df.melt(id_vars='Group', value_vars=valid_cols), 
                x='variable', y='value', color='Group', 
                title="Stat Distribution: High Win Rate vs Low Win Rate",
                template='plotly_dark',
                labels={'variable': 'Stat', 'value': 'Stat Value'}
            )
            st.plotly_chart(style_fig(fig_box), width='stretch', config=PLOT_CONFIG)

    # --- TAB 2: SKILLS ---
    with tab2:
        st.subheader("⚡ Skill Frequency")
        # (Existing Logic, just simplified for brevity)
        if 'skills' in filt_df.columns:
            s_df = filt_df[['Calculated_WinRate', 'skills']].dropna().copy()
            if s_df['skills'].dtype == object:
                # Ensure pipe delimiter is handled
                s_df['skills'] = s_df['skills'].astype(str).str.replace(r"[\[\]']", "", regex=True).str.split('|')
            
            exploded = s_df.explode('skills')
            exploded = exploded[exploded['skills'].str.len() > 2]
            
            top_skills = exploded['skills'].value_counts().head(20).index
            skill_perf = exploded[exploded['skills'].isin(top_skills)].groupby('skills')['Calculated_WinRate'].mean().reset_index()
            
            fig_skill = px.bar(
                skill_perf.sort_values('Calculated_WinRate', ascending=True), 
                x='Calculated_WinRate', y='skills', orientation='h',
                title="Win Rate of Most Common Skills",
                template='plotly_dark', color='Calculated_WinRate',
                labels={'Calculated_WinRate': 'Win Rate (%)', 'skills': 'Skill Name'}
            )
            st.plotly_chart(style_fig(fig_skill, height=600), width='stretch', config=PLOT_CONFIG)

    # --- TAB 3: SUPPORT CARDS (Moved from Resources) ---
    with tab3:
        st.subheader("🃏 Support Card Impact")
        card_map = {c.split('[')[-1].replace(']', '').strip(): c for c in match_df.columns if "Card Status" in c}
        
        if card_map:
            target = st.selectbox("Select Support Card", sorted(card_map.keys()))
            col = card_map[target]
            
            card_stats = match_df.drop_duplicates(subset=['Clean_IGN', 'Round', 'Day']).groupby(col).agg({
                'Calculated_WinRate': 'mean', 'Clean_IGN': 'count'
            }).reset_index()
            
            fig_card = px.bar(
                card_stats, x=col, y='Calculated_WinRate', color='Calculated_WinRate',
                title=f"Impact of {target}", text='Calculated_WinRate', template='plotly_dark',
                hover_data={'Clean_IGN': True},
                labels={col: 'Card Status', 'Calculated_WinRate': 'Win Rate (%)'}
            )
            fig_card.update_traces(texttemplate='%{text:.1f}%')
            st.plotly_chart(style_fig(fig_card), width='stretch', config=PLOT_CONFIG)
        else:
            st.info("No support card data available.")

    # --- TAB 4: CUMULATIVE TAIKI IMPACT (New Logic) ---
    with tab4:
        st.subheader("🐎 The Taiki Shuttle Effect (Cumulative)")
        st.markdown("**Combined Data: Prelims + Finals.** Calculating the true weighted win rate across the entire event.")
        
        # 1. Prepare Prelims
        prelims_data = match_df[['Clean_Uma', 'Clean_Wins', 'Clean_Races']].copy()
        
        # 2. Prepare Finals
        if not finals_matches.empty:
            finals_data = finals_matches[['Clean_Uma', 'Is_Winner']].rename(columns={'Is_Winner': 'Clean_Wins'})
            finals_data['Clean_Races'] = 1
            combined = pd.concat([prelims_data, finals_data], ignore_index=True)
        else:
            combined = prelims_data
            st.caption("⚠️ Finals data missing, showing Prelims only.")

        # 3. Filter & Calculate
        target = "Taiki Shuttle"
        is_target = combined['Clean_Uma'].str.contains(target, case=False, na=False)
        
        t_df = combined[is_target]
        f_df = combined[~is_target]
        
        if not t_df.empty:
            t_wins = t_df['Clean_Wins'].sum()
            t_runs = t_df['Clean_Races'].sum()
            t_wr = (t_wins / t_runs * 100) if t_runs > 0 else 0
            
            f_wins = f_df['Clean_Wins'].sum()
            f_runs = f_df['Clean_Races'].sum()
            f_wr = (f_wins / f_runs * 100) if f_runs > 0 else 0
            
            c1, c2, c3 = st.columns(3)
            c1.metric(f"{target} Cumulative WR", f"{t_wr:.1f}%", f"{t_wr-f_wr:+.1f}% vs Field")
            c2.metric("The Field WR", f"{f_wr:.1f}%")
            c3.metric("Total Runs Analyzed", f"{int(t_runs + f_runs)}")
            
            # Plot
            combined['Group'] = np.where(combined['Clean_Uma'].str.contains(target, case=False, na=False), target, 'The Field')
            # Calculate row-level WR for distribution
            combined['Row_WR'] = (combined['Clean_Wins'] / combined['Clean_Races']) * 100
            
            fig_hist = px.histogram(
                combined, x='Row_WR', color='Group', barmode='overlay', nbins=20,
                title=f"Win Rate Distribution: {target} vs Field (All Rounds)",
                template='plotly_dark', opacity=0.7,
                color_discrete_map={target: '#00CC96', 'The Field': '#EF553B'},
                pattern_shape='Group',
                pattern_shape_sequence=['+', 'x'],
                labels={'Row_WR': 'Win Rate (%)', 'count': 'Number of Entries'}
            )
            st.plotly_chart(style_fig(fig_hist), width='stretch', config=PLOT_CONFIG)
        else:
            st.warning(f"No data found for {target}.")

    # --- TAB 5 & 6: APTITUDE & UNIQUES ---
    with tab5:
        if 'Mile' in merged_df.columns:
            apt_stats = merged_df.groupby('Mile')['Calculated_WinRate'].mean().reset_index()
            apt_stats = apt_stats[apt_stats['Mile'].isin(['S', 'A'])]
            fig_apt = px.bar(apt_stats, x='Mile', y='Calculated_WinRate', color='Mile', text='Calculated_WinRate', title="Mile Aptitude S vs A", template='plotly_dark', labels={'Calculated_WinRate': 'Win Rate (%)', 'Mile': 'Mile Aptitude'})
            fig_apt.update_traces(texttemplate='%{text:.1f}%')
            st.plotly_chart(style_fig(fig_apt, height=400), width='stretch', config=PLOT_CONFIG)
            
    with tab6:
        if 'ultimate_level' in merged_df.columns:
            ult_stats = merged_df.groupby('ultimate_level')['Calculated_WinRate'].mean().reset_index()
            fig_ult = px.bar(ult_stats, x='ultimate_level', y='Calculated_WinRate', text='Calculated_WinRate', title="Win Rate by Unique Level", template='plotly_dark', labels={'Calculated_WinRate': 'Win Rate (%)', 'ultimate_level': 'Unique Level'})
            fig_ult.update_traces(texttemplate='%{text:.1f}%')
            st.plotly_chart(style_fig(fig_ult, height=400), width='stretch', config=PLOT_CONFIG)