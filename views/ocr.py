import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np
from virgo_utils import style_fig, PLOT_CONFIG, load_ocr_data, load_data, dynamic_height, parse_uma_details

def show_view(current_config):

    st.warning("⚠️ This OCR Analysis feature is still in beta and only includes ROUNDS DATA. Results may vary based on OCR accuracy and data quality. Please verify findings independently.")

    # 1. Get Config & Load Data
    event_name = current_config.get('id', 'Event').replace('_', ' ').title()
    parquet_file = current_config.get('parquet_file', '')
    sheet_url = current_config.get('sheet_url', '')

    st.header(f"🔮 Meta Analysis: {event_name}")

    with st.spinner("Loading and Merging Datasets..."):
        # Load Raw OCR Data
        ocr_df = load_ocr_data(parquet_file)
        
        # Load Match Data (CSV)
        match_df, _ = load_data(sheet_url)

    if ocr_df.empty:
        st.error(f"❌ OCR Data not found: {parquet_file}")
        return
    if match_df.empty:
        st.error("❌ Match Data not found.")
        return

    # --- 2. DATA MERGING & CLEANING ---
    # We need to link the Build (OCR) to the Win Rate (CSV)
    
    # A. Normalize Names for Matching
    # Clean OCR IGNs
    ocr_df['Match_IGN'] = ocr_df['ign'].astype(str).str.lower().str.strip()
    # Clean CSV IGNs
    match_df['Match_IGN'] = match_df['Clean_IGN'].astype(str).str.lower().str.strip()
    
    # Clean OCR Uma Names to match CSV format (e.g., "Oguri Cap")
    ocr_df['Match_Uma'] = parse_uma_details(ocr_df['name'])
    
    # B. Calculate Win Rates per Trainer+Uma in the CSV
    # We aggregate first to get the average performance of that Trainer's Oguri
    performance_df = match_df.groupby(['Match_IGN', 'Clean_Uma', 'Clean_Style']).agg({
        'Calculated_WinRate': 'mean',
        'Clean_Races': 'sum'
    }).reset_index().rename(columns={'Clean_Uma': 'Match_Uma'})

    # C. MERGE
    # Inner Join: We only want builds that actually have match data
    merged_df = pd.merge(
        ocr_df, 
        performance_df, 
        on=['Match_IGN', 'Match_Uma'], 
        how='inner'
    )
    
    st.success(f"✅ Successfully linked {len(merged_df)} builds to race results!")

    # --- 3. DASHBOARD TABS ---
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Best Stats & Distribution", 
        "⚡ Best Skills", 
        "🧬 Aptitude Impact (S vs A)",
        "🔎 Raw Data"
    ])

    # --- TAB 1: STATS ANALYSIS ---
    with tab1:
        st.subheader("🏆 Optimal Stat Distribution by Style")
        
        # 1. Filter by Style
        styles = sorted(merged_df['Clean_Style'].unique())
        target_style = st.selectbox("Select Running Style:", styles)
        
        style_data = merged_df[merged_df['Clean_Style'] == target_style]
        
        if not style_data.empty:
            # 2. Define "Winners" vs "Others"
            # High WR = Top 25% of performers
            wr_threshold = style_data['Calculated_WinRate'].quantile(0.75)
            winners = style_data[style_data['Calculated_WinRate'] >= wr_threshold]
            
            st.markdown(f"**Analysis of {len(style_data)} {target_style}s** (High WR Threshold: >{wr_threshold:.1f}%)")
            
            # 3. Compare Means
            stats = ['Speed', 'Stamina', 'Power', 'Guts', 'Wit']
            
            # Check if columns exist (handle missing Guts/Wit if old scenario)
            valid_stats = [s for s in stats if s in style_data.columns]
            
            if not winners.empty:
                avg_winner = winners[valid_stats].mean().rename("High Win Rate Avg")
                avg_all = style_data[valid_stats].mean().rename("Global Avg")
                
                comp_df = pd.concat([avg_winner, avg_all], axis=1)
                comp_df['Delta'] = comp_df['High Win Rate Avg'] - comp_df['Global Avg']
                
                # Display Metrics
                cols = st.columns(len(valid_stats))
                for i, stat in enumerate(valid_stats):
                    val = avg_winner[stat]
                    delta = comp_df.loc[stat, 'Delta']
                    cols[i].metric(stat, f"{val:.0f}", f"{delta:+.0f}")
                
                # 4. Box Plots for Distribution
                st.markdown("#### Stat Distribution: High WR vs Low WR")
                # Melt for plotting
                style_data['Tier'] = np.where(style_data['Calculated_WinRate'] >= wr_threshold, 'High WR', 'Low WR')
                melted = style_data.melt(id_vars=['Tier'], value_vars=valid_stats, var_name='Stat', value_name='Value')
                
                fig_box = px.box(
                    melted, x='Stat', y='Value', color='Tier',
                    template='plotly_dark',
                    color_discrete_map={'High WR': '#00CC96', 'Low WR': '#EF553B'},
                    title=f"Stat Ranges for {target_style} (High vs Low Win Rate)"
                )
                st.plotly_chart(style_fig(fig_box), use_container_width=True, config=PLOT_CONFIG)
            else:
                st.warning("Not enough data to calculate top performers.")

    # --- TAB 2: SKILLS ANALYSIS ---
    with tab2:
        st.subheader("⚡ Skill Meta Analysis")
        
        # Filter by Uma (Optional)
        all_umas = ["All"] + sorted(merged_df['Match_Uma'].unique())
        target_uma = st.selectbox("Filter by Uma:", all_umas)
        
        skill_source = merged_df if target_uma == "All" else merged_df[merged_df['Match_Uma'] == target_uma]
        
        if 'skills' in skill_source.columns and not skill_source.empty:
            # Clean and Explode Skills
            # Handle string representation of lists if necessary
            s_df = skill_source[['Calculated_WinRate', 'skills']].dropna().copy()
            
            try:
                # If likely string "['SkillA', 'SkillB']", clean it
                if s_df['skills'].dtype == object:
                     s_df['skills'] = s_df['skills'].astype(str).str.replace(r"[\[\]']", "", regex=True).str.split(',')
                
                exploded = s_df.explode('skills')
                exploded['skills'] = exploded['skills'].str.strip()
                exploded = exploded[exploded['skills'] != ""]
                
                # Compare Top 25% WR vs Bottom 50% WR
                high_thresh = exploded['Calculated_WinRate'].quantile(0.75)
                low_thresh = exploded['Calculated_WinRate'].quantile(0.50)
                
                high_tier = exploded[exploded['Calculated_WinRate'] >= high_thresh]
                low_tier = exploded[exploded['Calculated_WinRate'] <= low_thresh]
                
                # Calculate Frequencies
                top_freq = high_tier['skills'].value_counts(normalize=True).rename("Top_Freq")
                low_freq = low_tier['skills'].value_counts(normalize=True).rename("Low_Freq")
                
                # Merge and Calculate Lift
                lift_df = pd.concat([top_freq, low_freq], axis=1).fillna(0)
                # Filter noise (must appear in at least 1% of top builds)
                lift_df = lift_df[lift_df['Top_Freq'] > 0.01]
                
                # Lift = (Top% - Low%) * 100
                lift_df['Lift'] = (lift_df['Top_Freq'] - lift_df['Low_Freq']) * 100
                lift_df = lift_df.sort_values('Lift', ascending=False).head(20)
                
                fig_lift = px.bar(
                    lift_df, x='Lift', y=lift_df.index, orientation='h',
                    title=f"Skill 'Lift' (Difference in Usage % between Winners and Losers)",
                    template='plotly_dark',
                    labels={'index': 'Skill', 'Lift': 'Usage Difference (%)'},
                    color='Lift', color_continuous_scale='Viridis'
                )
                st.plotly_chart(style_fig(fig_lift, height=600), use_container_width=True, config=PLOT_CONFIG)
                
                st.info("Skills with positive Lift are correlated with higher Win Rates.")
                
            except Exception as e:
                st.error(f"Error parsing skills: {e}")

    # --- TAB 3: APTITUDES (S vs A) ---
    with tab3:
        st.subheader("🧬 Does S Rank Matter?")
        st.markdown("Comparing average Win Rates for builds with **S** vs **A** aptitude.")

        # Map Match Styles to Parquet Columns
        # Parquet has: 'Front', 'Pace', 'Late', 'End' (and Turf/Mile)
        # We need to map standard styles to these columns
        style_map = {
            'Front Runner': 'Front',   # Leader
            'Pace Chaser': 'Pace',     # Betweener
            'Late Surger': 'Late',     # ??? (Sometimes Betweener/Closer split)
            'End Closer': 'End',       # Closer
            'Runaway': 'Front'         # Fallback (Runners often share Front aptitude or column is missing)
        }
        
        c1, c2, c3 = st.columns(3)
        
        # 1. TURF ANALYSIS
        with c1:
            if 'Turf' in merged_df.columns:
                st.markdown("#### 🌱 Turf Aptitude")
                turf_stats = merged_df.groupby('Turf')['Calculated_WinRate'].mean().reset_index()
                # Filter for S and A only
                turf_stats = turf_stats[turf_stats['Turf'].isin(['S', 'A'])]
                
                if not turf_stats.empty:
                    fig_turf = px.bar(turf_stats, x='Turf', y='Calculated_WinRate', color='Turf', template='plotly_dark', title="Turf S vs A")
                    fig_turf.update_layout(showlegend=False, yaxis_title="Win Rate %")
                    st.plotly_chart(style_fig(fig_turf, height=300), use_container_width=True, config=PLOT_CONFIG)

        # 2. DISTANCE ANALYSIS (Mile/Medium/etc)
        with c2:
            # Detect distance col (Mile, Medium, etc.) based on event?
            # For Virgo it's Mile.
            target_dist = 'Mile' 
            if target_dist in merged_df.columns:
                st.markdown(f"#### 📏 {target_dist} Aptitude")
                dist_stats = merged_df.groupby(target_dist)['Calculated_WinRate'].mean().reset_index()
                dist_stats = dist_stats[dist_stats[target_dist].isin(['S', 'A'])]
                
                if not dist_stats.empty:
                    fig_dist = px.bar(dist_stats, x=target_dist, y='Calculated_WinRate', color=target_dist, template='plotly_dark', title=f"{target_dist} S vs A")
                    fig_dist.update_layout(showlegend=False, yaxis_title=None)
                    st.plotly_chart(style_fig(fig_dist, height=300), use_container_width=True, config=PLOT_CONFIG)
        
        # 3. STYLE ANALYSIS
        with c3:
            st.markdown("#### 🏃 Running Style Aptitude")
            # We look at the specific aptitude column required for the runner's chosen style
            # e.g. If they ran 'Front Runner', we check their 'Front' aptitude
            
            valid_rows = []
            for _, row in merged_df.iterrows():
                style = row['Clean_Style']
                col = style_map.get(style)
                if col and col in merged_df.columns:
                    aptitude = row[col]
                    if aptitude in ['S', 'A']:
                        valid_rows.append({'Aptitude': aptitude, 'WinRate': row['Calculated_WinRate']})
            
            if valid_rows:
                style_apt_df = pd.DataFrame(valid_rows)
                style_stats = style_apt_df.groupby('Aptitude')['WinRate'].mean().reset_index()
                
                fig_style = px.bar(style_stats, x='Aptitude', y='WinRate', color='Aptitude', template='plotly_dark', title="Relevant Style S vs A")
                fig_style.update_layout(showlegend=False, yaxis_title=None)
                st.plotly_chart(style_fig(fig_style, height=300), use_container_width=True, config=PLOT_CONFIG)
            else:
                st.info("Could not map styles to aptitude columns.")

    # --- TAB 4: RAW DATA ---
    with tab4:
        st.dataframe(merged_df)