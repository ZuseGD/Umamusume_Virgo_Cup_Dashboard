import streamlit as st
import plotly.express as px
from uma_utils import style_fig, PLOT_CONFIG, dynamic_height, show_description, analyze_significant_roles, add_img_chart

def show_view(df, team_df):
    st.set_page_config(page_title="Uma Performance Dashboard", layout="wide")
    st.header("🐴 Individual Uma Performance")
    st.warning("⚠️ **NOTE:** Win Rates are based on **TEAM Performance** when this Uma is present. It does NOT track individual race wins. Use this data to analyze overall Uma effectiveness within team compositions.")
    
    # Calculate Total Entries for Percentage Maths
    total_entries = len(df)

    # --- 1. UMA INSPECTOR ---
    st.subheader("🔎 Uma Inspector (NEW)")
    all_umas = sorted(df['Clean_Uma'].unique())
    target_uma = st.selectbox("Select Uma:", [""] + all_umas)

    if target_uma:
        uma_data = df[df['Clean_Uma'] == target_uma]
        avg_wr = uma_data['Calculated_WinRate'].mean()
        unique_players = uma_data['Clean_IGN'].nunique()
        total_uma_entries = len(uma_data) # Calculate raw count of entries
        
        # Calculate Global Pick Rate for this specific Uma
        uma_pick_rate = (total_uma_entries / total_entries) * 100
        
        # --- UPDATE: Added c4 for Total Count ---
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Win Rate", f"{avg_wr:.1f}%")
        c2.metric("Pick Rate", f"{uma_pick_rate:.1f}%")
        c3.metric("Unique Users", int(unique_players))
        c4.metric("Total Entries", int(total_uma_entries)) # Display Count
        
        # --- NEW: Role Impact Analysis for this Uma ---
        # Checks if specific roles (Ace, Debuffer) on THIS Uma change the win rate
        role_res = analyze_significant_roles(uma_data, role_col='Clean_Role', threshold=2.0)
        st.warning("The following roles for this Uma have a significant impact on Win Rate (>2% difference):, if there is no data shown, it means no roles had significant impact.")
        if role_res:
            sig_df, g_avg = role_res
            st.markdown(f"**🎭 Significant Role Impact** (vs Average: {g_avg:.1f}%)")
            
            sig_df.rename(columns={'Clean_Role': 'User Inputted Role of Uma', 'Win_Rate': 'Win Rate', 'Diff_vs_Avg': 'Difference vs Average (%)'}, inplace=True)
            st.dataframe(
                sig_df.style.format({'Win Rate': '{:.1f}%', 'Difference vs Average (%)': '{:+.1f}%'}),
                width='stretch',
                hide_index=True
            )
        # -----------------------------------------------

        # 1. PREPARE DATA: Aggregate by Summing Races (True Volume)
        strat_stats = uma_data.groupby('Clean_Style').agg({
            'Calculated_WinRate': 'mean',
            'Clean_Races': 'sum' 
        }).reset_index()
        strat_stats.columns = ['Strategy', 'Win_Rate', 'Race_Volume']
        
        total_vol = strat_stats['Race_Volume'].sum()
        strat_stats['Style_Dist'] = (strat_stats['Race_Volume'] / total_vol) * 100

        # 2. CHART: Strategy Breakdown
        fig_drill = px.bar(
            strat_stats, 
            x='Win_Rate', 
            y='Strategy', 
            orientation='h', 
            title=f"Strategy Breakdown for {target_uma}", 
            template='plotly_dark', 
            height=400,
            hover_data={'Race_Volume': True, 'Win_Rate': ':.1f', 'Style_Dist': ':.1f', 'Strategy': False}
        )
        
        fig_drill.update_traces(
            texttemplate='%{x:.1f}%', 
            textposition='inside',
            hovertemplate='<b>%{y}</b><br>Win Rate: %{x:.1f}%<br>Number of Races: %{customdata[0]}<extra></extra>'
        )
        
        fig_drill.update_layout(xaxis_title="Win Rate (%)", yaxis_title=None)
        st.plotly_chart(style_fig(fig_drill, height=400), width="stretch", config=PLOT_CONFIG)
        show_description("drilldown")

    st.markdown("---")
    
    # --- 2. TIER LIST SECTION ---
    st.subheader("Uma Tier List")
    
    # Aggregate Stats
    uma_stats = df.groupby('Clean_Uma').agg({
        'Calculated_WinRate': 'mean', 
        'Clean_Races': 'count'
    }).reset_index()
    
    # Calculate Global Pick Rate
    uma_stats['Pick Rate %'] = (uma_stats['Clean_Races'] / total_entries) * 300
    
    # Filter: Hide very low sample size (less than 10 entries)
    uma_stats = uma_stats[uma_stats['Clean_Races'] >= 10]
    
    # Prepare Top 15 for Bar Chart
    top_umas = uma_stats.sort_values('Calculated_WinRate', ascending=False).head(15).copy()
    uma_stats['Win Rate %'] = uma_stats['Calculated_WinRate']
    uma_stats['Runs'] = uma_stats['Clean_Races']
    top_umas['Short_Name'] = top_umas['Clean_Uma'].apply(
        lambda x: x[:18] + ".." if len(x) > 18 else x
    )

    # Dynamic Height Calculation
    n_items = len(top_umas)
    chart_height = dynamic_height(n_items, min_height=600, per_item=45)

    # SCATTER PLOT (Quadrants)
    st.markdown("####  Popularity vs. Performance (Quadrants)")
    fig_scatter = px.scatter(
        uma_stats, 
        x='Pick Rate %',              
        y='Calculated_WinRate',
        size='Pick Rate %',           # Size by pick rate
        color='Calculated_WinRate',
        color_continuous_scale='Viridis',
        title="Uma Tier List: Pick Rate vs Performance",
        template='plotly_dark',
        hover_name='Clean_Uma',
        labels={'Pick Rate %': 'Pick Rate (%)', 'Calculated_WinRate': 'Win Rate (%)', 'Clean_Races': 'Number of Entries'},
        hover_data={'Clean_Races': True, 'Pick Rate %': ':.1f', 'Calculated_WinRate': ':.1f'},
        size_max=120
    )

    add_img_chart(uma_stats, fig_scatter)
    
    # Add Average Reference Lines
    avg_wr = uma_stats['Calculated_WinRate'].mean()
    avg_pick = uma_stats['Pick Rate %'].mean()
    
    fig_scatter.add_hline(y=avg_wr, line_dash="dot", annotation_text="Avg WR", annotation_position="bottom left")
    fig_scatter.add_vline(x=avg_pick, line_dash="dot", annotation_text="Avg Pick Rate", annotation_position="top right")

    fig_scatter.update_layout(coloraxis_colorbar=dict(title=None, orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    
    st.plotly_chart(style_fig(fig_scatter, height=600), width="stretch", config=PLOT_CONFIG)
    show_description("scatter_tier")
    
    # BAR CHART (Rankings)
    st.markdown("#### 🏆 Detailed Rankings")
    st.warning("⚠️ **NOTE:** Win Rates are based on **TEAM Performance** when this Uma is present. It does NOT track individual race wins. Also note that lower pick rate Umas may have less reliable Win Rate data due to smaller sample sizes.")

    fig_uma = px.bar(
        top_umas,
        x='Short_Name', 
        y='Calculated_WinRate',            
        orientation='v', 
        color='Calculated_WinRate', 
        color_continuous_scale='Viridis', 
        text='Pick Rate %',          
        template='plotly_dark', 
        # Pass extra data for tooltip
        hover_data={'Clean_Uma': False, 'Short_Name': False, 'Clean_Races': False, 'Pick Rate %': ':.2f', 'Calculated_WinRate': False},
        labels={'Calculated_WinRate': 'Win Rate (%)', 'Short_Name': 'Uma', 'Pick Rate %': 'Pick Rate (%)'},
        height=chart_height
    )
    
    fig_uma.update_layout(
        yaxis={'categoryorder':'total ascending'}, 
        yaxis_title="Avg Win Rate (%)", 
        xaxis_title="Character",
        coloraxis_colorbar=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    # Customize Text and Tooltip
    fig_uma.update_traces(
        texttemplate='Pick: %{text:.1f}%', 
        textposition='outside',
    )
    
    st.plotly_chart(style_fig(fig_uma, height=chart_height), width="stretch", config=PLOT_CONFIG)
    show_description("uma_bar")