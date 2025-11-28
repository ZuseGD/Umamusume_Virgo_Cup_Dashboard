import streamlit as st
import plotly.express as px
import pandas as pd
from virgo_utils import load_finals_data, style_fig, PLOT_CONFIG

def show_view(current_config):
    st.header("🏆 Finals Analysis")
    
    # 1. LOAD DATA SPECIFIC TO FINALS
    csv_path = current_config.get('finals_csv')
    pq_path = current_config.get('finals_parquet')
    
    if not csv_path:
        st.info("🚫 No Finals data configured for this event.")
        return

    with st.spinner("Loading Finals Data..."):
        matches_df, merged_df = load_finals_data(csv_path, pq_path)
    
    if matches_df.empty:
        st.warning("⚠️ Could not load Finals CSV.")
        return

    # --- METRICS ---
    total_entries = matches_df['Match_IGN'].nunique()
    total_winners = matches_df[matches_df['Is_Winner'] == 1]['Match_IGN'].nunique()
    
    m1, m2 = st.columns(2)
    m1.metric("Total Finalists", total_entries)
    m2.metric("Winners Recorded", total_winners)
    
    st.markdown("---")

    # --- TABS ---
    tab1, tab2, tab3 = st.tabs(["⚔️ Meta Teams", "🐎 Winner Stats", "⚡ Winner Skills"])

    # TAB 1: META TEAMS
    with tab1:
        st.subheader("Finals Team Compositions")
        team_df = matches_df.groupby(['Display_IGN', 'Result']).agg({
            'Clean_Uma': lambda x: sorted(list(x)),
            'Is_Winner': 'max'
        }).reset_index()
        
        team_df['Team_Comp'] = team_df['Clean_Uma'].apply(lambda x: ", ".join(x))
        comp_counts = team_df['Team_Comp'].value_counts().reset_index()
        comp_counts.columns = ['Team', 'Count']
        
        fig = px.bar(comp_counts.head(15), x='Count', y='Team', orientation='h',
                     title="Most Popular Teams in Finals", template='plotly_dark', 
                     color='Count', color_continuous_scale='Plasma')
        fig.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(style_fig(fig), use_container_width=True, config=PLOT_CONFIG)

    # TAB 2: STATS
    with tab2:
        st.subheader("🏆 Winning Build Stats")
        if merged_df.empty:
            st.warning("No OCR matches found.")
        else:
            winners_df = merged_df[merged_df['Is_Winner'] == 1].copy()
            if not winners_df.empty:
                styles = ["All"] + sorted(winners_df['Clean_Style'].unique())
                sel_style = st.selectbox("Filter Winners by Style:", styles)
                
                plot_data = winners_df if sel_style == "All" else winners_df[winners_df['Clean_Style'] == sel_style]
                
                stat_cols = ['Speed', 'Stamina', 'Power', 'Guts', 'Wit']
                valid_cols = [c for c in stat_cols if c in plot_data.columns]
                
                melted = plot_data.melt(value_vars=valid_cols, var_name='Stat', value_name='Value')
                fig_box = px.box(melted, x='Stat', y='Value', color='Stat', template='plotly_dark')
                st.plotly_chart(style_fig(fig_box), use_container_width=True, config=PLOT_CONFIG)
            else:
                st.info("No winners in data.")

    # TAB 3: SKILLS
    with tab3:
        st.subheader("⚡ Skills of Champions")
        if not merged_df.empty:
            winners_df = merged_df[merged_df['Is_Winner'] == 1].copy()
            if 'skills' in winners_df.columns:
                if winners_df['skills'].dtype == object:
                     winners_df['skills'] = winners_df['skills'].astype(str).str.replace(r"[\[\]']", "", regex=True).str.split(',')
                
                exploded = winners_df.explode('skills')
                exploded['skills'] = exploded['skills'].str.strip()
                exploded = exploded[exploded['skills'] != ""]
                
                skill_counts = exploded['skills'].value_counts().head(20).reset_index()
                skill_counts.columns = ['Skill', 'Count']
                
                fig_skill = px.bar(skill_counts, x='Count', y='Skill', orientation='h', template='plotly_dark')
                fig_skill.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(style_fig(fig_skill), use_container_width=True, config=PLOT_CONFIG)