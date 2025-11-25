import streamlit as st
import plotly.express as px
import pandas as pd
from utils import style_fig, PLOT_CONFIG, load_ocr_data, dynamic_height

def show_view(current_config):
    # 1. Get Config
    event_name = current_config.get('id', 'Event').replace('_', ' ').title()
    parquet_file = current_config.get('parquet_file', '')

    st.header(f"📸 OCR Analysis: {event_name}")

    # 2. Load Data
    with st.spinner("Loading heavy OCR data..."):
        ocr_df = load_ocr_data(parquet_file)

    if ocr_df.empty:
        st.warning(f"No OCR data found for **{event_name}**.")
        st.info(f"Please check if `{parquet_file}` exists in your folder.")
        return

    # --- DASHBOARD TABS ---
    tab1, tab2, tab3 = st.tabs(["📊 Stat Distribution", "⚡ Skill Meta", "📂 Raw Data"])

    # --- TAB 1: STATS ---
    with tab1:
        st.subheader("Stat Distribution")
        target_stat = st.selectbox("Select Stat", ['Speed', 'Stamina', 'Power', 'Guts', 'Wit', 'score'], index=0)
        
        # Histogram
        fig_dist = px.histogram(
            ocr_df, 
            x=target_stat, 
            nbins=40, 
            title=f"Distribution of {target_stat}",
            template='plotly_dark',
            color_discrete_sequence=['#00CC96']
        )
        fig_dist.update_layout(bargap=0.1)
        st.plotly_chart(style_fig(fig_dist), width="stretch", config=PLOT_CONFIG)
        
        # Score Scatter (Stats vs Score)
        if target_stat != 'score':
            st.markdown("#### Stat Efficiency")
            fig_scatter = px.scatter(
                ocr_df,
                x=target_stat,
                y='score',
                color='score',
                title=f"{target_stat} vs Evaluation Score",
                template='plotly_dark',
                hover_data=['name', 'rank']
            )
            st.plotly_chart(style_fig(fig_scatter), width="stretch", config=PLOT_CONFIG)

    # --- TAB 2: SKILLS (The New Logic) ---
    with tab2:
        st.subheader("⚡ Top Skills")
        
        if 'skills' in ocr_df.columns:
            # 1. DATA CLEANING PIPELINE
            # Check if skills are lists or strings (Parquet can store lists)
            # If it's a string like "['Skill1', 'Skill2']", we need to parse it. 
            # If it's already a list, we just explode.
            
            skill_df = ocr_df[['name', 'skills']].dropna()
            
            # Safe Explode Logic
            try:
                # If data is string representation of list, eval it (carefully)
                # or just assume it is a list if read from parquet correctly
                exploded_skills = skill_df.explode('skills')
            except:
                st.error("Could not process skills column format.")
                exploded_skills = pd.DataFrame()

            if not exploded_skills.empty:
                # Normalize: Strip whitespace
                exploded_skills['skills'] = exploded_skills['skills'].astype(str).str.strip()
                
                # 2. FREQUENCY COUNT (The Filter)
                skill_counts = exploded_skills['skills'].value_counts().reset_index()
                skill_counts.columns = ['Skill Name', 'Count']
                
                # 3. FILTER NOISE (Drop anything that appears less than X times)
                # This automatically removes OCR garbage like "Corner Recov%^"
                valid_skills = skill_counts[skill_counts['Count'] > 5]
                
                # Calculate Usage %
                total_scans = len(ocr_df)
                valid_skills['Usage %'] = (valid_skills['Count'] / total_scans) * 100
                
                # VISUALIZE
                top_n = 20
                fig_skills = px.bar(
                    valid_skills.head(top_n),
                    x='Usage %',
                    y='Skill Name',
                    orientation='h',
                    title=f"Top {top_n} Most Used Skills",
                    template='plotly_dark',
                    color='Usage %',
                    color_continuous_scale='Viridis',
                    text='Count'
                )
                
                # Sort bar chart with most popular at top
                fig_skills.update_layout(yaxis={'categoryorder':'total ascending'})
                fig_skills.update_traces(texttemplate='%{x:.1f}% (N=%{text})', textposition='inside')
                
                # Dynamic Height
                h = dynamic_height(top_n)
                st.plotly_chart(style_fig(fig_skills, height=h), width="stretch", config=PLOT_CONFIG)
                
                with st.expander("View Full Skill List (Cleaned)"):
                    st.dataframe(valid_skills)
            else:
                st.warning("No valid skill data found to analyze.")
        else:
            st.info("This dataset does not contain a 'skills' column.")

    # --- TAB 3: RAW DATA ---
    with tab3:
        st.subheader("📂 Data Explorer")
        st.dataframe(ocr_df)