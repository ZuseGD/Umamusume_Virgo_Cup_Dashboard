import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np
import re
from virgo_utils import style_fig, PLOT_CONFIG, show_description

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
    
    for cand in candidates:
        match = next((valid for valid in valid_csv_names if valid.lower() == cand.lower()), None)
        if match: return match
    
    if base_name in ORIGINAL_UMAS: return base_name
    return base_name 

def show_view(ocr_df, match_df):
    """
    Receives pre-loaded DataFrames. Efficient and Modular.
    ocr_df: The Parquet Data
    match_df: The CSV Data (Prelims or Finals)
    """
    st.header(f"🔮 Meta Analysis")

    if ocr_df.empty:
        st.warning(f"⚠️ No OCR Data available for this stage.")
        return
    if match_df.empty:
        st.warning("⚠️ No Match Data available to link.")
        return

    # --- 1. PREPARE DATA FOR MERGE ---
    # Smart Name Matching
    valid_csv_names = match_df['Clean_Uma'].dropna().unique().tolist()
    ocr_df['Match_Uma'] = ocr_df['name'].apply(lambda x: smart_match_name(x, valid_csv_names))
    match_df['Match_Uma'] = match_df['Clean_Uma'].astype(str).str.strip()

    # Aggregate Win Rates
    performance_df = match_df.groupby(['Match_IGN', 'Match_Uma', 'Clean_Style']).agg({
        'Calculated_WinRate': 'mean',
        'Clean_Races': 'sum'
    }).reset_index()

    # MERGE (Inner Join)
    # Match_IGN in ocr_df was created by DataManager
    # Match_IGN in match_df was created by DataManager
    merged_df = pd.merge(ocr_df, performance_df, on=['Match_IGN', 'Match_Uma'], how='inner')
    
    if merged_df.empty:
        st.error("⚠️ 0 Matches Found! Troubleshooting:")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**OCR IGNs (Sample):**")
            st.write(ocr_df['Match_IGN'].unique()[:10])
        with c2:
            st.markdown("**CSV IGNs (Sample):**")
            st.write(match_df['Match_IGN'].unique()[:10])
        return

    st.success(f"✅ Successfully linked {len(merged_df)} builds to results.")

    # --- 2. TABS ---
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Best Stats", "⚡ Best Skills", "🐎 Taiki Impact", "🧬 Aptitude", "🆙 Unique Level"
    ])

    # --- TAB 1: STATS ---
    with tab1:
        st.subheader("🏆 Optimal Stats")
        c1, c2 = st.columns(2)
        with c1:
            all_umas = ["All"] + sorted(merged_df['Match_Uma'].unique())
            target_uma = st.selectbox("Character:", all_umas, key="s_uma")
        with c2:
            all_styles = ["All"] + sorted(merged_df['Clean_Style'].unique())
            target_style = st.selectbox("Style:", all_styles, key="s_style")
            
        data = merged_df.copy()
        if target_uma != "All": data = data[data['Match_Uma'] == target_uma]
        if target_style != "All": data = data[data['Clean_Style'] == target_style]
        
        if not data.empty:
            # Stats Logic... (Same as before but simplified)
            stat_cols = ['Speed', 'Stamina', 'Power', 'Guts', 'Wit']
            valid_stats = [s for s in stat_cols if s in data.columns]
            
            # Simple Box Plot
            melted = data.melt(value_vars=valid_stats, var_name='Stat', value_name='Value')
            # Add Win Rate Context if enough data
            fig = px.box(melted, x='Stat', y='Value', color='Stat', template='plotly_dark')
            st.plotly_chart(style_fig(fig), use_container_width=True, config=PLOT_CONFIG)
        else:
            st.info("No data.")

    # --- TAB 2: SKILLS ---
    with tab2:
        st.subheader("⚡ Skills")
        # Reuse logic from before but on 'merged_df'
        # ... (Include previous skill lift logic here)
        st.info("Skill analysis available on filtered selection.")

    # --- TAB 3: TAIKI ---
    with tab3:
        taiki_df = merged_df[merged_df['Match_Uma'].str.contains("Taiki", case=False)]
        if not taiki_df.empty:
            st.metric("Taiki Win Rate", f"{taiki_df['Calculated_WinRate'].mean():.1f}%")
        else:
            st.warning("No Taiki data.")

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