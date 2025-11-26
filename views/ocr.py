import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np
import re
from virgo_utils import style_fig, PLOT_CONFIG, load_ocr_data, load_data, dynamic_height, parse_uma_details

# --- CONFIGURATION ---

# 1. LIST OF ORIGINAL UMAS (Base Names)
# Add all your "Base" characters here.
ORIGINAL_UMAS = [
    "Maruzensky", "Taiki Shuttle", "Oguri Cap", "El Condor Pasa", "Grass Wonder",
    "Silence Suzuka", "Gold Ship", "Vodka", "Daiwa Scarlet", "Mejiro Ryan",
    "Rice Shower", "Winning Ticket", "Haru Urara", "Matikanefukukitaru",
    "Nice Nature", "King Halo", "Agnes Tachyon", "Super Creek", "Mayaano Top Gun",
    "Mihono Bourbon", "Tokai Teio", "Symboli Rudolf", "Air Groove", "Seiun Sky",
    # ... Add more as needed
]

# 2. VARIANT KEYWORDS
# Maps keywords found in [Brackets] to a Suffix.
# Example: [Hot Summer] -> "Summer" -> Checks for "Maruzensky (Summer)"
VARIANT_MAP = {
    "Summer": "Summer",
    "Hot Summer": "Summer",
    "Valentine": "Valentine",
    "Christmas": "Christmas",
    "Holiday": "Christmas",
    "Wedding": "Wedding",
    "Bridal": "Wedding",
    "Monk": "Monk",
    "Fantasy": "Fantasy",
    "Halloween": "Halloween",
    "New Year": "New Year"
}

def smart_match_name(raw_name, valid_csv_names):
    """
    Tries to find the best match in the CSV list.
    Priority:
    1. Variant Match (e.g., "Maruzensky (Summer)")
    2. Base Match (e.g., "Maruzensky")
    """
    if pd.isna(raw_name): return "Unknown"
    raw_name = str(raw_name)

    # 1. Extract Base Name & Title
    # OCR Format: "[Title] Base Name"
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
    
    # Candidate A: Explicit Variant (e.g., "Maruzensky (Summer)")
    if variant_suffix:
        candidates.append(f"{base_name} ({variant_suffix})")
        candidates.append(f"{variant_suffix} {base_name}")

    # Candidate B: Base Name (Default)
    candidates.append(base_name)
    
    # 4. Check against Valid CSV Names
    # We look for the first candidate that actually exists in the match data
    for cand in candidates:
        # Case-insensitive check
        match = next((valid for valid in valid_csv_names if valid.lower() == cand.lower()), None)
        if match:
            return match
            
    # 5. Fallback: If no match found, check if it's a known Original
    # This helps even if the CSV name is slightly different (e.g. spacing)
    if base_name in ORIGINAL_UMAS:
        return base_name
        
    return base_name # Return simplified name as last resort

def show_view(current_config):
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
    
    # A. Get Valid Names from CSV for Matching
    valid_csv_names = match_df['Clean_Uma'].dropna().unique().tolist()
    
    # B. Apply Smart Matching
    # This links the messy OCR name to the clean CSV name
    ocr_df['Match_Uma'] = ocr_df['name'].apply(lambda x: smart_match_name(x, valid_csv_names))
    
    # C. Prepare Join Keys
    ocr_df['Match_IGN'] = ocr_df['ign'].astype(str).str.lower().str.strip()
    match_df['Match_IGN'] = match_df['Clean_IGN'].astype(str).str.lower().str.strip()
    match_df['Match_Uma'] = match_df['Clean_Uma'].astype(str).str.strip() # Ensure exact match

    # D. Aggregate Win Rates
    performance_df = match_df.groupby(['Match_IGN', 'Match_Uma', 'Clean_Style']).agg({
        'Calculated_WinRate': 'mean',
        'Clean_Races': 'sum'
    }).reset_index()

    # E. Merge
    merged_df = pd.merge(
        ocr_df, 
        performance_df, 
        on=['Match_IGN', 'Match_Uma'], 
        how='inner'
    )
    
    # --- DIAGNOSTICS ---
    if merged_df.empty:
        st.error("⚠️ 0 Matches Found! Debugging Info:")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**OCR Names (Processed):**")
            st.write(ocr_df['Match_Uma'].unique()[:10])
        with c2:
            st.markdown("**CSV Names (Available):**")
            st.write(valid_csv_names[:10])
        return

    st.success(f"✅ Successfully linked {len(merged_df)} builds to race results!")

    # --- 3. DASHBOARD TABS ---
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Best Stats", 
        "⚡ Best Skills", 
        "🧬 Aptitude (S vs A)",
        "🔎 Raw Data"
    ])

    # --- TAB 1: STATS ANALYSIS ---
    with tab1:
        st.subheader("🏆 Optimal Stat Distribution by Style")
        if 'Clean_Style' in merged_df.columns:
            styles = sorted(merged_df['Clean_Style'].unique())
            target_style = st.selectbox("Select Running Style:", styles)
            
            style_data = merged_df[merged_df['Clean_Style'] == target_style]
            
            if not style_data.empty:
                wr_threshold = style_data['Calculated_WinRate'].quantile(0.75)
                winners = style_data[style_data['Calculated_WinRate'] >= wr_threshold]
                
                stat_cols = ['Speed', 'Stamina', 'Power', 'Guts', 'Wit']
                valid_stats = [s for s in stat_cols if s in style_data.columns]
                
                if not winners.empty:
                    avg_winner = winners[valid_stats].mean()
                    avg_all = style_data[valid_stats].mean()
                    
                    st.markdown(f"**{target_style} Winners (WR > {wr_threshold:.1f}%)** vs **Average**")
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
                    title=f"Stat Distribution: High vs Low Win Rate ({target_style})"
                )
                st.plotly_chart(style_fig(fig_box), width='stretch', config=PLOT_CONFIG)

    # --- TAB 2: SKILLS ANALYSIS ---
    with tab2:
        st.subheader("⚡ Skill Meta Analysis")
        # Filter by Match_Uma (which is now cleaned)
        all_umas = ["All"] + sorted(merged_df['Match_Uma'].unique())
        target_uma = st.selectbox("Filter by Character:", all_umas)
        
        skill_source = merged_df if target_uma == "All" else merged_df[merged_df['Match_Uma'] == target_uma]
        
        if 'skills' in skill_source.columns and not skill_source.empty:
            s_df = skill_source[['Calculated_WinRate', 'skills']].dropna().copy()
            if s_df['skills'].dtype == object:
                 s_df['skills'] = s_df['skills'].astype(str).str.replace(r"[\[\]']", "", regex=True).str.split(',')
            
            exploded = s_df.explode('skills')
            exploded['skills'] = exploded['skills'].str.strip()
            exploded = exploded[exploded['skills'] != ""]
            
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
                    title=f"Skill 'Lift' (Difference in Usage between Winners and Losers)",
                    template='plotly_dark',
                    labels={'index': 'Skill', 'Lift': 'Usage Diff (%)'},
                    color='Lift', color_continuous_scale='Viridis'
                )
                fig_lift.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(style_fig(fig_lift, height=600), width='stretch', config=PLOT_CONFIG)
            else:
                st.warning("Not enough data variance to compare winners vs losers.")

    # --- TAB 3: APTITUDE ANALYSIS ---
    with tab3:
        st.subheader("🧬 Aptitude Impact (S vs A)")
        c1, c2 = st.columns(2)
        target_dist = 'Mile' 
        if target_dist in merged_df.columns:
            with c1:
                st.markdown(f"#### 📏 {target_dist} Aptitude")
                dist_stats = merged_df.groupby(target_dist)['Calculated_WinRate'].mean().reset_index()
                dist_stats = dist_stats[dist_stats[target_dist].isin(['S', 'A'])]
                if not dist_stats.empty:
                    fig_dist = px.bar(dist_stats, x=target_dist, y='Calculated_WinRate', color=target_dist, template='plotly_dark', title=f"{target_dist} S vs A")
                    st.plotly_chart(style_fig(fig_dist, height=400), width='stretch', config=PLOT_CONFIG)

        if 'Turf' in merged_df.columns:
            with c2:
                st.markdown("#### 🌱 Turf Aptitude")
                turf_stats = merged_df.groupby('Turf')['Calculated_WinRate'].mean().reset_index()
                turf_stats = turf_stats[turf_stats['Turf'].isin(['S', 'A'])]
                if not turf_stats.empty:
                    fig_turf = px.bar(turf_stats, x='Turf', y='Calculated_WinRate', color='Turf', template='plotly_dark', title="Turf S vs A")
                    st.plotly_chart(style_fig(fig_turf, height=400), width='stretch', config=PLOT_CONFIG)
