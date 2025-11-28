import streamlit as st
import plotly.express as px
import pandas as pd
from virgo_utils import load_finals_data, style_fig, PLOT_CONFIG, load_ocr_data

def show_view(current_config):
    st.header("🏆 Finals: Comprehensive Analysis")
    
    # 1. LOAD DATA
    csv_path = current_config.get('finals_csv')
    pq_path = current_config.get('finals_parquet')
    prelims_pq = current_config.get('parquet_file') # For baseline comparison
    
    if not csv_path:
        st.info("🚫 No Finals data configured.")
        return

    with st.spinner("Crunching Finals Data..."):
        matches_df, merged_df = load_finals_data(csv_path, pq_path)
        # Load Prelims Baseline for "Lift" analysis
        prelims_df = load_ocr_data(prelims_pq)
    
    if matches_df.empty:
        st.warning("⚠️ Could not load Finals CSV.")
        return

    # --- METRICS ---
    total_entries = matches_df['Display_IGN'].nunique()
    total_winners = matches_df[matches_df['Is_Winner'] == 1]['Display_IGN'].nunique()
    
    # Calculate "Ace" percentage (Entries that aren't Debuffers)
    if 'Clean_Role' in matches_df.columns:
        ace_count = len(matches_df[matches_df['Clean_Role'].str.contains("Ace", case=False, na=False)])
        debuff_count = len(matches_df[matches_df['Clean_Role'].str.contains("Debuff", case=False, na=False)])
    else:
        ace_count, debuff_count = 0, 0

    m1, m2, m3 = st.columns(3)
    m1.metric("Finalists Analyzed", total_entries)
    m2.metric("Winners Confirmed", total_winners)
    m3.metric("Ace vs Debuff Ratio", f"{ace_count}:{debuff_count}")
    
    st.markdown("---")

    # --- TABS ---
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Meta Overview", 
        "⚔️ Team Comps", 
        "⚡ Skill Lift (Winners vs Field)", 
        "🏆 Champion Stats"
    ])

    # --- TAB 1: META OVERVIEW (Uma Tier List) ---
    with tab1:
        st.subheader("🏁 Finals Character Tier List")
        st.caption("Which Umas were brought to Finals, and which ones actually won?")
        
        # Aggregate Finals Stats
        uma_stats = matches_df.groupby('Clean_Uma').agg({
            'Is_Winner': ['count', 'sum']
        }).reset_index()
        uma_stats.columns = ['Uma', 'Entries', 'Wins']
        
        # Calculate Win Rate in Finals Context (Note: Small sample size warnings apply)
        # We define "Meta Score" as a mix of Popularity and Winning Capability
        uma_stats['Pick_Rate'] = (uma_stats['Entries'] / total_entries) * 100
        uma_stats['Win_Rate'] = (uma_stats['Wins'] / uma_stats['Entries']) * 100
        
        # Filter low sample size
        uma_stats = uma_stats[uma_stats['Entries'] >= 3]
        
        # Scatter Plot
        fig = px.scatter(
            uma_stats, 
            x='Pick_Rate', 
            y='Win_Rate',
            size='Entries',
            color='Win_Rate',
            hover_name='Uma',
            title="Finals Meta: Popularity vs Success",
            labels={'Pick_Rate': 'Pick Rate (%)', 'Win_Rate': 'Win Rate (%)'},
            template='plotly_dark',
            color_continuous_scale='Viridis'
        )
        # Add quadrants
        avg_pick = uma_stats['Pick_Rate'].mean()
        avg_win = uma_stats['Win_Rate'].mean()
        fig.add_vline(x=avg_pick, line_dash="dot", annotation_text="Avg Popularity")
        fig.add_hline(y=avg_win, line_dash="dot", annotation_text="Avg Win Rate")
        
        st.plotly_chart(style_fig(fig), use_container_width=True, config=PLOT_CONFIG)

    # --- TAB 2: TEAM COMPS ---
    with tab2:
        st.subheader("⚔️ Winning Team Compositions")
        
        # Group by Player
        team_df = matches_df.groupby(['Display_IGN', 'Result']).agg({
            'Clean_Uma': lambda x: sorted(list(x)),
            'Is_Winner': 'max'
        }).reset_index()
        
        team_df['Team_Comp'] = team_df['Clean_Uma'].apply(lambda x: ", ".join(x))
        
        # Compare Winners vs Losers Comps
        winners_comps = team_df[team_df['Is_Winner'] == 1]['Team_Comp'].value_counts().reset_index()
        winners_comps.columns = ['Team', 'Wins']
        
        fig = px.bar(
            winners_comps.head(10), 
            x='Wins', y='Team', orientation='h',
            title="Top Teams that took 1st Place",
            template='plotly_dark', color='Wins', color_continuous_scale='Plasma'
        )
        fig.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(style_fig(fig), use_container_width=True, config=PLOT_CONFIG)

    # --- TAB 3: SKILL LIFT (The "Comprehensive Insight") ---
    with tab3:
        st.subheader("⚡ Skill Lift Analysis")
        st.caption("How do **Finals Winners** differ from the **Prelims Baseline**? (Positive Lift = Winning Secret)")
        
        if merged_df.empty or prelims_df.empty:
            st.warning("Need both Finals OCR and Prelims OCR data to calculate lift.")
        else:
            # 1. Filter Winners (Aces Only)
            # Use Role if available, else assume winners are aces
            winners_ocr = merged_df[merged_df['Is_Winner'] == 1].copy()
            if 'Clean_Role' in winners_ocr.columns:
                winners_ocr = winners_ocr[winners_ocr['Clean_Role'].str.contains('Ace', case=False, na=False)]
            
            # 2. Select Style
            styles = sorted(winners_ocr['Clean_Style'].unique())
            target_style = st.selectbox("Select Style to Analyze:", styles)
            
            winners_style = winners_ocr[winners_ocr['Clean_Style'] == target_style]
            
            # 3. Calculate Frequencies
            def get_freq(df):
                if 'skills' not in df.columns or df.empty: return pd.Series()
                # Clean strings
                if df['skills'].dtype == object and isinstance(df['skills'].iloc[0], str):
                     df['skills'] = df['skills'].astype(str).str.replace(r"[\[\]']", "", regex=True).str.split(',')
                
                exploded = df.explode('skills')
                exploded['skills'] = exploded['skills'].str.strip()
                return exploded['skills'].value_counts(normalize=True) * 100

            win_freq = get_freq(winners_style).rename("Winner %")
            base_freq = get_freq(prelims_df).rename("Baseline %")
            
            # 4. Merge & Lift
            lift_df = pd.concat([win_freq, base_freq], axis=1).fillna(0)
            lift_df['Lift'] = lift_df['Winner %'] - lift_df['Baseline %']
            
            # Filter noise
            lift_df = lift_df[lift_df['Winner %'] > 5]
            
            # Top Positive Lift
            top_lift = lift_df.sort_values('Lift', ascending=False).head(15)
            
            fig_lift = px.bar(
                top_lift, x='Lift', y=top_lift.index, orientation='h',
                title=f"Top 15 High-Value Skills for {target_style} (vs General Population)",
                labels={'index': 'Skill', 'Lift': 'Usage Increase (%)'},
                color='Lift', color_continuous_scale='Tealgrn', template='plotly_dark',
                hover_data=['Winner %', 'Baseline %']
            )
            fig_lift.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(style_fig(fig_lift), use_container_width=True, config=PLOT_CONFIG)

    # --- TAB 4: CHAMPION STATS ---
    with tab4:
        st.subheader("🏆 Champion Stat Distribution")
        
        if not merged_df.empty:
            winners_ocr = merged_df[merged_df['Is_Winner'] == 1].copy()
            
            # Filter by Style
            styles = ["All"] + sorted(winners_ocr['Clean_Style'].unique())
            sel_style = st.selectbox("Stats for Style:", styles, key="stat_style")
            
            plot_data = winners_ocr
            if sel_style != "All":
                plot_data = winners_ocr[winners_ocr['Clean_Style'] == sel_style]
                
            stat_cols = ['Speed', 'Stamina', 'Power', 'Guts', 'Wit']
            valid_cols = [c for c in stat_cols if c in plot_data.columns]
            
            # Compare Winners vs Losers (in Finals)
            plot_data['Result_Group'] = 'Winner'
            
            # Add Losers for comparison?
            losers_ocr = merged_df[merged_df['Is_Winner'] == 0].copy()
            if not losers_ocr.empty:
                if sel_style != "All":
                    losers_ocr = losers_ocr[losers_ocr['Clean_Style'] == sel_style]
                losers_ocr['Result_Group'] = 'Non-Winner'
                combined = pd.concat([plot_data, losers_ocr])
            else:
                combined = plot_data

            melted = combined.melt(id_vars=['Result_Group'], value_vars=valid_cols, var_name='Stat', value_name='Value')
            
            fig_box = px.box(
                melted, x='Stat', y='Value', color='Result_Group',
                template='plotly_dark',
                title=f"Stat Benchmark: Winners vs Non-Winners",
                color_discrete_map={'Winner': '#00CC96', 'Non-Winner': '#EF553B'}
            )
            st.plotly_chart(style_fig(fig_box), use_container_width=True, config=PLOT_CONFIG)