import streamlit as st
import plotly.express as px
from utils import style_fig, PLOT_CONFIG

def show_view(ocr_df):
    st.header("📸 OCR Data Analysis")
    
    if ocr_df.empty:
        st.warning("No OCR data found. Please ensure 'r2d2.parquet' is in the main folder.")
        return

    # 1. TOP STATS
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Umas Scanned", len(ocr_df))
    c2.metric("Avg Speed", int(ocr_df['Speed'].mean()))
    c3.metric("Avg Score", int(ocr_df['score'].mean()))
    
    st.markdown("---")

    # 2. STAT DISTRIBUTION CHART
    st.subheader("📊 Stat Distribution")
    target_stat = st.selectbox("Select Stat to Visualize", ['Speed', 'Stamina', 'Power', 'Guts', 'Wit'])
    
    fig_dist = px.histogram(
        ocr_df, 
        x=target_stat, 
        nbins=30, 
        title=f"Distribution of {target_stat}",
        template='plotly_dark',
        color_discrete_sequence=['#00CC96']
    )
    fig_dist.update_layout(bargap=0.1)
    st.plotly_chart(style_fig(fig_dist), width="stretch", config=PLOT_CONFIG)
    
    # 3. SCATTER PLOT (Score vs Stat)
    '''
    st.subheader("💠 Score Efficiency")
    fig_scatter = px.scatter(
        ocr_df,
        x=target_stat,
        y='score',
        color='score',
        hover_data=['name', 'rank'],
        title=f"Score vs {target_stat}",
        template='plotly_dark'
    )
    st.plotly_chart(style_fig(fig_scatter), width="stretch", config=PLOT_CONFIG)
    '''

    # 4. RAW DATA TABLE
    with st.expander("📂 View Raw Data"):
        st.dataframe(ocr_df)