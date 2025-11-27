import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np
import re
from virgo_utils import style_fig, PLOT_CONFIG, load_ocr_data, load_data, show_description

# --- CONFIGURATION ---

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
    """
    Tries to find the best match in the CSV list (Variant > Base > Fallback).
    """
    if pd.isna(raw_name): return "Unknown"
    raw_name = str(raw_name)

    # 1. Extract Base Name & Title
    base_match = re.search(r'\]\s*(.*)', raw_name)
    title_match = re.search(r'\[(.*?)\]', raw_name)
    
    base_name = base_match.group(1).strip() if base_match else raw_name.strip()
    title_text = title_match.group(1) if title_match else ""

    # 2. Detect Variant Suffix
    variant_suffix = None
    for keyword, suffix in VARIANT_MAP.items():
        if keyword.lower() in title_text.lower():
            variant_suffix = suffix
            break
    
    # 3. Construct Potential Names
    candidates = []
    if variant_suffix:
        candidates.append(f"{base_name} ({variant_suffix})")
        candidates.append(f"{variant_suffix} {base_name}")
    candidates.append(base_name)
    
    # 4. Check against Valid CSV Names
    for cand in candidates:
        match = next((valid for valid in valid_csv_names if valid.lower() == cand.lower()), None)
        if match: return match
            
    # 5. Fallback
    if base_name in ORIGINAL_UMAS: return base_name
    return base_name 

def show_view(current_config):
    # 1. Get Config & Load Data
    event_name = current_config.get('id', 'Event').replace('_', ' ').title()
    parquet_file = current_config.get('parquet_file', '')
    sheet_url = current_config.get('sheet_url', '')

    st.header(f"🔮 Meta Analysis: {event_name}")

    with st.spinner("Loading and Merging Datasets..."):
        ocr_df = load_ocr_data(parquet_file)
        match_df, _ = load_data(sheet_url)

    if ocr_df.empty:
        st.error(f"❌ OCR Data not found: {parquet_file}")
        return
    if match_df.empty:
        st.error("❌ Match Data not found.")
        return

    # --- 2. DATA MERGING & CLEANING ---
    valid_csv_names = match_df['Clean_Uma'].dropna().unique().tolist()
    ocr_df['Match_Uma'] = ocr_df['name'].apply(lambda x: smart_match_name(x, valid_csv_names))
    
    # Keys
    ocr_df['Match_IGN'] = ocr_df['ign'].astype(str).str.lower().str.strip()
    match_df['Match_IGN'] = match_df['Clean_IGN'].astype(str).str.lower().str.strip()
    match_df['Match_Uma'] = match_df['Clean_Uma'].astype(str).str.strip()

    # Aggregate Win Rates (Trainer + Uma + Style)
    performance_df = match_df.groupby(['Match_IGN', 'Match_Uma', 'Clean_Style']).agg({
        'Calculated_WinRate': 'mean',
        'Clean_Races': 'sum'
    }).reset_index()

    # Merge
    merged_df = pd.merge(ocr_df, performance_df, on=['Match_IGN', 'Match_Uma'], how='inner')
    
    if merged_df.empty:
        st.error("⚠️ 0 Matches Found! Names do not match.")
        st.write("OCR Names:", ocr_df['Match_Uma'].unique()[:5])
        st.write("CSV Names:", valid_csv_names[:5])
        return

    st.success(f"✅ Successfully linked {len(merged_df)} builds to race results!")

    # --- 3. DASHBOARD TABS ---
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Best Stats", 
        "⚡ Best Skills", 
        "🐎 Taiki Impact",
        "🧬 Aptitude (S vs A)",
        "🆙 Unique Level"
    ])

    # --- TAB 1: STATS ANALYSIS (UPDATED WITH DUAL FILTERS) ---
    with tab1:
        st.subheader("🏆 Optimal Stat Distribution")
        st.caption("Filter by **Character** and **Style** to find the winning stat spread.")
        
        c1, c2 = st.columns(2)
        with c1:
            # Character Filter
            all_umas = ["All"] + sorted(merged_df['Match_Uma'].unique())
            target_uma = st.selectbox("Select Character:", all_umas, key="stats_uma")
        with c2:
            # Style Filter
            styles = ["All"] + sorted(merged_df['Clean_Style'].unique())
            target_style = st.selectbox("Select Running Style:", styles, key="stats_style")
            
        # Apply Filters
        style_data = merged_df.copy()
        if target_uma != "All":
            style_data = style_data[style_data['Match_Uma'] == target_uma]
        if target_style != "All":
            style_data = style_data[style_data['Clean_Style'] == target_style]
            
        if not style_data.empty:
            wr_threshold = style_data['Calculated_WinRate'].quantile(0.75)
            winners = style_data[style_data['Calculated_WinRate'] >= wr_threshold]
            
            stat_cols = ['Speed', 'Stamina', 'Power', 'Guts', 'Wit']
            valid_stats = [s for s in stat_cols if s in style_data.columns]
            
            if not winners.empty:
                avg_winner = winners[valid_stats].mean()
                avg_all = style_data[valid_stats].mean()
                
                st.markdown(f"**Winners (WR > {wr_threshold:.1f}%)** vs **Average**")
                cols = st.columns(len(valid_stats))
                for i, stat in enumerate(valid_stats):
                    delta = avg_winner[stat] - avg_all[stat]
                    cols[i].metric(stat, f"{avg_winner[stat]:.0f}", f"{delta:+.0f}")
            
            # Distribution Plot
            st.markdown("#### Stat Ranges")
            style_data['Performance'] = np.where(style_data['Calculated_WinRate'] >= wr_threshold, 'High WR', 'Low WR')
            melted = style_data.melt(id_vars=['Performance'], value_vars=valid_stats, var_name='Stat', value_name='Value')
            
            fig_box = px.box(
                melted, x='Stat', y='Value', color='Performance',
                template='plotly_dark',
                color_discrete_map={'High WR': '#00CC96', 'Low WR': '#EF553B'},
                title=f"Stat Ranges: Winners vs Losers"
            )
            st.plotly_chart(style_fig(fig_box), width='stretch', config=PLOT_CONFIG)
            show_description("ocr_stats")
        else:
            st.warning("No data matches this combination of Character and Style.")

    # --- TAB 2: SKILLS ANALYSIS ---
    with tab2:
        st.subheader("⚡ Skill Meta Analysis")
        st.caption("Identify skills that appear significantly more often in Winning Builds.")

        c1, c2 = st.columns(2)
        with c1:
            all_umas = ["All"] + sorted(merged_df['Match_Uma'].unique())
            target_uma = st.selectbox("Filter by Character:", all_umas, key="skills_uma")
        with c2:
            all_styles = ["All"] + sorted(merged_df['Clean_Style'].unique())
            target_style = st.selectbox("Filter by Style:", all_styles, key="skills_style")
        
        # Apply Logic
        skill_source = merged_df.copy()
        if target_uma != "All":
            skill_source = skill_source[skill_source['Match_Uma'] == target_uma]
        if target_style != "All":
            skill_source = skill_source[skill_source['Clean_Style'] == target_style]
        
        if 'skills' in skill_source.columns and not skill_source.empty:
            s_df = skill_source[['Calculated_WinRate', 'skills']].dropna().copy()
            if s_df['skills'].dtype == object:
                 s_df['skills'] = s_df['skills'].astype(str).str.replace(r"[\[\]']", "", regex=True).str.split(',')
            
            exploded = s_df.explode('skills')
            exploded['skills'] = exploded['skills'].str.strip()
            exploded = exploded[exploded['skills'] != ""]
            
            if not exploded.empty:
                high_thresh = exploded['Calculated_WinRate'].quantile(0.75)
                low_thresh = exploded['Calculated_WinRate'].quantile(0.50)
                
                high_tier = exploded[exploded['Calculated_WinRate'] >= high_thresh]
                low_tier = exploded[exploded['Calculated_WinRate'] <= low_thresh]
                
                if not high_tier.empty and not low_tier.empty:
                    top_freq = high_tier['skills'].value_counts(normalize=True).rename("Top_Freq")
                    low_freq = low_tier['skills'].value_counts(normalize=True).rename("Low_Freq")
                    
                    lift_df = pd.concat([top_freq, low_freq], axis=1).fillna(0)
                    lift_df = lift_df[lift_df['Top_Freq'] > 0.01]
                    lift_df['Lift'] = (lift_df['Top_Freq'] - lift_df['Low_Freq']) * 100
                    lift_df = lift_df.sort_values('Lift', ascending=False).head(20)
                    
                    fig_lift = px.bar(
                        lift_df, x='Lift', y=lift_df.index, orientation='h',
                        title=f"Skill Lift (Usage Difference %)",
                        template='plotly_dark',
                        labels={'index': 'Skill', 'Lift': 'Usage Diff (%)'},
                        color='Lift', color_continuous_scale='Viridis'
                    )
                    fig_lift.update_layout(yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(style_fig(fig_lift, height=600), width='stretch', config=PLOT_CONFIG)
                    show_description("ocr_skills")
                else:
                    st.warning("Not enough data variance to calculate lift.")
        else:
            st.info("No skill data available for current selection.")

    # --- TAB 3: TAIKI IMPACT (NEW) ---
    with tab3:
        st.subheader("🐎 Taiki Shuttle Impact Analysis")
        st.markdown("Quantifying the **'Taiki Boost'**: How much better is Taiki Shuttle compared to the field?")
        
        # 1. Filter for Taiki
        taiki_mask = merged_df['Match_Uma'].str.contains("Taiki", case=False)
        taiki_df = merged_df[taiki_mask]
        other_df = merged_df[~taiki_mask]
        
        if not taiki_df.empty:
            # 2. Calculate Metrics
            taiki_wr = taiki_df['Calculated_WinRate'].mean()
            global_wr = other_df['Calculated_WinRate'].mean()
            wr_delta = taiki_wr - global_wr
            
            # 3. Display KPIs
            c1, c2, c3 = st.columns(3)
            c1.metric("Taiki Win Rate", f"{taiki_wr:.1f}%", f"{wr_delta:+.1f}% vs Global")
            c2.metric("Sample Size", f"{len(taiki_df)} Builds")
            c3.metric("Global Average WR", f"{global_wr:.1f}%")
            
            st.markdown("---")
            
            # 4. Comparative Distribution
            st.markdown("#### Win Rate Distribution: Taiki vs The Field")
            
            # Combine for plotting
            taiki_df_plot = taiki_df[['Calculated_WinRate']].copy()
            taiki_df_plot['Group'] = 'Taiki Shuttle'
            
            other_df_plot = other_df[['Calculated_WinRate']].copy()
            other_df_plot['Group'] = 'Rest of Field'
            
            # Sample down 'Other' to make histogram readable if needed, or just plot all
            combined_plot = pd.concat([taiki_df_plot, other_df_plot])
            
            fig_hist = px.histogram(
                combined_plot, 
                x='Calculated_WinRate', 
                color='Group',
                barmode='overlay',
                nbins=20,
                opacity=0.7,
                template='plotly_dark',
                title="Win Rate Histogram Comparison",
                color_discrete_map={'Taiki Shuttle': '#00CC96', 'Rest of Field': '#636EFA'}
            )
            st.plotly_chart(style_fig(fig_hist), width='stretch', config=PLOT_CONFIG)
            
            show_description("taiki_impact")
            
        else:
            st.warning("No Taiki Shuttle data found in the linked dataset.")

    # --- TAB 4: APTITUDE ANALYSIS ---
    with tab4:
        st.subheader("🧬 Aptitude Impact (S vs A)")
        c1, c2 = st.columns(2)
        target_dist = 'Mile' 
        
        if target_dist in merged_df.columns:
            with c1:
                dist_stats = merged_df.groupby(target_dist)['Calculated_WinRate'].mean().reset_index()
                dist_stats = dist_stats[dist_stats[target_dist].isin(['S', 'A'])]
                if not dist_stats.empty:
                    fig_dist = px.bar(dist_stats, x=target_dist, y='Calculated_WinRate', color=target_dist, template='plotly_dark', title=f"{target_dist} S vs A", text='Calculated_WinRate')
                    fig_dist.update_traces(texttemplate='%{text:.1f}%')
                    st.plotly_chart(style_fig(fig_dist, height=400), width='stretch', config=PLOT_CONFIG)

        if 'Turf' in merged_df.columns:
            with c2:
                turf_stats = merged_df.groupby('Turf')['Calculated_WinRate'].mean().reset_index()
                turf_stats = turf_stats[turf_stats['Turf'].isin(['S', 'A'])]
                if not turf_stats.empty:
                    fig_turf = px.bar(turf_stats, x='Turf', y='Calculated_WinRate', color='Turf', template='plotly_dark', title="Turf S vs A", text='Calculated_WinRate')
                    fig_turf.update_traces(texttemplate='%{text:.1f}%')
                    st.plotly_chart(style_fig(fig_turf, height=400), width='stretch', config=PLOT_CONFIG)

    # --- TAB 5: UNIQUE LEVEL ANALYSIS ---
    with tab5:
        st.subheader("🆙 Unique Skill Level Impact")
        st.markdown("Does grinding for **Unique Skill Level (1-6)** significantly impact Win Rate?")
        
        if 'ultimate_level' in merged_df.columns:
            lvl_stats = merged_df.groupby('ultimate_level')['Calculated_WinRate'].agg(['mean', 'count']).reset_index()
            lvl_stats.columns = ['Level', 'WinRate', 'Count']
            lvl_stats = lvl_stats[lvl_stats['Count'] >= 3] 
            
            if not lvl_stats.empty:
                fig_lvl = px.bar(
                    lvl_stats, 
                    x='Level', 
                    y='WinRate', 
                    color='WinRate',
                    template='plotly_dark',
                    title="Average Win Rate by Unique Skill Level",
                    text='WinRate',
                    color_continuous_scale='Bluered'
                )
                fig_lvl.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
                fig_lvl.update_layout(xaxis=dict(tickmode='linear', dtick=1))
                st.plotly_chart(style_fig(fig_lvl), width='stretch', config=PLOT_CONFIG)
                show_description("ocr_unique")
            else:
                st.warning("Not enough data on Unique Levels.")
        else:
            st.error("Column 'ultimate_level' not found in OCR data.")