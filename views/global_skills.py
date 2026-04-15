import streamlit as st
import pandas as pd
from uma_utils import load_finals_data

@st.cache_data
def get_mega_skill_dataframe(all_configs):
    """
    Iterates through all past CM configurations, extracts the skill lists, 
    and combines them into a single massive dataframe with Track/Distance metadata.
    """
    data_frames = []
    
    for cm_id, config in all_configs.items():
        is_multipart = config.get('is_multipart_parquet', False)
        
        if is_multipart:
            parts = config.get('finals_parts', {})
            # If the required parquet paths are None/Missing, skip this CM
            if not parts.get("statsheet") or not parts.get("podium"):
                continue
        else:
            # If it's a CSV based CM and the path is None, skip it
            if not config.get('finals_csv'):
                continue
        df, _ = load_finals_data(config)
        
        if not df.empty and 'Skill_List' in df.columns:
            # Keep only what is strictly necessary
            subset = df[['Clean_Uma', 'Clean_Style', 'Skill_List', 'Is_Winner']].copy()
            
            # metadata from the config
            subset['Track'] = config.get('aptitude_surf', 'Unknown')
            subset['Distance'] = config.get('aptitude_dist', 'Unknown')
            subset['CM_Name'] = cm_id
            
            data_frames.append(subset)
            
    if data_frames:
        return pd.concat(data_frames, ignore_index=True)
    return pd.DataFrame()


def show_view(all_configs):
    st.set_page_config(page_title="Global Skill Database", layout="wide")
    st.warning("⚠️ This page can be slow to load due to the large amount of data being processed. Please allow some time for the skill database to populate. Thank you for your patience!")
    st.header("🔮 Global Skill Database")
    st.markdown("An aggregation of all past Champion's Meetings to find the optimal skills for every character. The #1 most used skill (usually the Unique) is automatically hidden.")
    
    mega_df = get_mega_skill_dataframe(all_configs)
    
    if mega_df.empty:
        st.warning("No data available across CM configs.")
        return
    st.warning("This view is a work in progress based on historical data and does not account for new skills or changes in the meta. Use it as a reference, but always consider current trends and updates!")
    # Filters
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        umas = sorted(mega_df['Clean_Uma'].dropna().unique())
        selected_uma = st.selectbox("Trainer (Uma)", umas)
        
    # restrict subsequent options based on the chosen Uma
    uma_df = mega_df[mega_df['Clean_Uma'] == selected_uma]
    
    with c2:
        styles = ["All"] + sorted(uma_df['Clean_Style'].dropna().unique())
        selected_style = st.selectbox("Strategy", styles)
        
    with c3:
        tracks = ["All"] + sorted(uma_df['Track'].dropna().unique())
        selected_track = st.selectbox("Track (Turf/Dirt)", tracks)
        
    with c4:
        distances = ["All"] + sorted(uma_df['Distance'].dropna().unique())
        selected_dist = st.selectbox("Distance", distances)

    # filters
    filtered_df = uma_df.copy()
    if selected_style != "All": filtered_df = filtered_df[filtered_df['Clean_Style'] == selected_style]
    if selected_track != "All": filtered_df = filtered_df[filtered_df['Track'] == selected_track]
    if selected_dist != "All": filtered_df = filtered_df[filtered_df['Distance'] == selected_dist]

    # basic metrics
    # Ensure Is_Winner is an integer
    filtered_df['Is_Winner'] = filtered_df['Is_Winner'].fillna(0).astype(int)
    
    total_builds = len(filtered_df)
    total_winners = filtered_df['Is_Winner'].sum()

    st.metric("Total Valid Builds Analyzed", total_builds)

    if total_builds == 0:
        st.info("No builds match this specific combination of filters.")
        return

    # wr extraction and calculation
    # Explode ALL skills (Winners and Losers) so we can calculate true Win Rates
    skills_exploded = filtered_df.explode('Skill_List')
    skills_exploded = skills_exploded.dropna(subset=['Skill_List'])
    skills_exploded['Skill_List'] = skills_exploded['Skill_List'].astype(str).str.strip()
    skills_exploded = skills_exploded[skills_exploded['Skill_List'] != ""]

    # Group by skill to get Total Uses and Total Wins
    skill_stats = skills_exploded.groupby('Skill_List').agg(
        Total_Uses=('Is_Winner', 'count'),
        Wins=('Is_Winner', 'sum')
    ).reset_index().rename(columns={'Skill_List': 'Skill'})

    # Calculate Global Win Rate for the skill
    skill_stats['Win Rate %'] = (skill_stats['Wins'] / skill_stats['Total_Uses']) * 100

    # show only finals winners
    show_winners = st.checkbox("🏆 View Meta Based on Finals Winners Only", value=True)

    if show_winners:
        if total_winners == 0:
            st.warning("No winners found for these filters.")
            return
            
        # Usage is based on how many WINNERS had the skill
        skill_stats['Usage %'] = (skill_stats['Wins'] / total_winners) * 100
        skill_stats = skill_stats[skill_stats['Wins'] > 0] # Hide skills that never won
        
        # Sort by Meta relevance (Most Wins)
        skill_stats = skill_stats.sort_values(by=['Wins', 'Win Rate %'], ascending=[False, False])
    else:
        # Usage is based on EVERYONE who had the skill
        skill_stats['Usage %'] = (skill_stats['Total_Uses'] / total_builds) * 100
        
        # Sort by Popularity (Most Uses)
        skill_stats = skill_stats.sort_values(by=['Total_Uses', 'Win Rate %'], ascending=[False, False])

    # drop the unique skill if it's at the top (usually the unique skill with 100% usage among winners)
    if len(skill_stats) > 0:
        # The #1 most frequent skill sits at index 0
        dropped_skill = skill_stats.iloc[0]['Skill']
        dropped_rate = skill_stats.iloc[0]['Usage %']
        
        # Keep everything from index 1 downwards
        skill_stats = skill_stats.iloc[1:].reset_index(drop=True)
        st.caption(f"*(Auto-hid **{dropped_skill}** ({dropped_rate:.1f}% usage) as the presumed Unique Skill)*")

    # dataframe with custom formatting
    st.dataframe(
        skill_stats[['Skill', 'Usage %', 'Win Rate %', 'Wins', 'Total_Uses']], 
        column_config={
            "Skill": st.column_config.TextColumn("Skill Name", width="large"),
            "Usage %": st.column_config.ProgressColumn("Usage Rate", format="%.1f%%", min_value=0, max_value=100),
            "Win Rate %": st.column_config.NumberColumn("Win Rate", format="%.1f%%"),
            "Wins": st.column_config.NumberColumn("Wins"),
            "Total_Uses": st.column_config.NumberColumn("Total Uses")
        },
        hide_index=True,
        width='stretch'
    )