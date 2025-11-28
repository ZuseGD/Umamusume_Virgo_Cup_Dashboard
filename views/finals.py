import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from virgo_utils import load_finals_data, load_ocr_data, load_data, style_fig, PLOT_CONFIG, calculate_score, SHEET_URL

def show_view(current_config):
    st.header("🏆 Finals: Comprehensive Analysis")
    st.markdown("""
    **Deep Dive into the Finals Meta.** This section analyzes the "Real" meta—what actually won in the A-Finals. 
    It compares the *Winning Aces* against the general population to identify the specific stats, skills, and team compositions that made the difference.
    """)
    
    csv_path = current_config.get('finals_csv')
    pq_path = current_config.get('finals_parquet')
    prelims_pq = current_config.get('parquet_file') 
    
    if not csv_path:
        st.info("🚫 No Finals data configured.")
        return

    with st.spinner("Crunching Finals Data..."):
        prelims_raw = load_ocr_data(prelims_pq)
        # Now returns global_stats as 3rd arg
        matches_df, finals_ocr, global_stats = load_finals_data(csv_path, pq_path, main_ocr_df=prelims_raw)
        sheet_df, _ = load_data(SHEET_URL)
    
    if matches_df.empty:
        st.warning("⚠️ Could not load Finals CSV.")
        return

    # --- METRICS ---
    total_entries = global_stats['Total Entries'].sum() if not global_stats.empty else 0
    total_winners = global_stats['Wins'].sum() if not global_stats.empty else 0
    winners_with_scan = finals_ocr[finals_ocr['Is_Specific_Winner'] == 1]['Display_IGN'].nunique() if not finals_ocr.empty else 0

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Slots Tracked", f"{total_entries}", help="All Umas in lobby (Own + Opponents)")
    m2.metric("Lobby Winners Tracked", f"{total_winners}")
    m3.metric("Winners w/ Scan Data", f"{winners_with_scan}", help="Specific winners with stats available.")
    
    st.markdown("---")

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Meta Overview", 
        "⚔️ Team Comps", 
        "⚡ Skill Lift", 
        "🏆 Champion Stats",
        "🌐 Global Stats",
        "💸 Economics & Cards"
    ])

    # --- TAB 1: META OVERVIEW ---
    with tab1:
        st.subheader("🏁 Character Tier List (Cumulative)")
        st.markdown("**Meta Score vs. Individual Win Rate (Prelims + Finals)**")
        
        if not sheet_df.empty and not global_stats.empty:
            prelim_stats = sheet_df.groupby('Clean_Uma')[['Clean_Wins', 'Clean_Races']].sum()
            
            # Use GLOBAL STATS for Finals contribution (Most Accurate)
            # global_stats has 'Uma Name', 'Total Entries', 'Wins'
            finals_stats = global_stats.set_index('Uma Name')[['Wins', 'Total Entries']].rename(columns={'Wins': 'Clean_Wins', 'Total Entries': 'Clean_Races'})
            
            cum_stats = prelim_stats.add(finals_stats, fill_value=0)
            cum_stats = cum_stats[cum_stats['Clean_Races'] > 0]
            
            cum_stats['Win_Rate'] = (cum_stats['Clean_Wins'] / cum_stats['Clean_Races']) * 100
            cum_stats['Meta_Score'] = cum_stats.apply(lambda x: calculate_score(x['Clean_Wins'], x['Clean_Races']), axis=1)
            
            tier_data = cum_stats[cum_stats['Clean_Races'] >= 5].reset_index().rename(columns={'index': 'Uma'})
            
            if not tier_data.empty:
                slope, intercept = np.polyfit(tier_data['Meta_Score'], tier_data['Win_Rate'], 1)
                x_trend = np.linspace(tier_data['Meta_Score'].min(), tier_data['Meta_Score'].max(), 100)
                y_trend = slope * x_trend + intercept

                mean_s = tier_data['Meta_Score'].mean()
                std_s = tier_data['Meta_Score'].std()
                max_s = tier_data['Meta_Score'].max() * 1.1
                min_s = 0

                fig = px.scatter(
                    tier_data, x='Meta_Score', y='Win_Rate', size='Clean_Races', color='Win_Rate',
                    hover_name='Clean_Uma', title="Cumulative Meta: Impact vs Efficiency",
                    template='plotly_dark', color_continuous_scale='Viridis',
                    labels={'Meta_Score': 'Meta Score', 'Win_Rate': 'Win Rate (%)', 'Clean_Races': 'Total Races'}
                )
                fig.add_trace(go.Scatter(x=x_trend, y=y_trend, mode='lines', name='Trend', line=dict(color='white', width=2, dash='dash'), opacity=0.5))
                
                fig.add_vrect(x0=mean_s + std_s, x1=max_s, fillcolor="purple", opacity=0.15, annotation_text="S Tier")
                fig.add_vrect(x0=mean_s, x1=mean_s + std_s, fillcolor="green", opacity=0.1, annotation_text="A Tier")
                fig.add_vrect(x0=mean_s - std_s, x1=mean_s, fillcolor="yellow", opacity=0.05, annotation_text="B Tier")
                fig.add_vrect(x0=min_s, x1=mean_s - std_s, fillcolor="red", opacity=0.05, annotation_text="C Tier")

                st.plotly_chart(style_fig(fig), use_container_width=True, config=PLOT_CONFIG)
            else:
                st.info("Not enough data.")
        else:
            st.info("Missing stats.")

    # --- TAB 2: TEAM COMPS ---
    with tab2:
        st.subheader("⚔️ Winning Team Compositions")
        
        team_df = matches_df.groupby(['Display_IGN', 'Result']).agg({
            'Clean_Uma': lambda x: sorted(list(x)), 
            'Is_Winner': 'max'
        }).reset_index()
        team_df['Team_Comp'] = team_df['Clean_Uma'].apply(lambda x: ", ".join(x))
        
        comp_stats = team_df.groupby('Team_Comp').agg({'Is_Winner': ['count', 'sum']}).reset_index()
        comp_stats.columns = ['Team', 'Entries', 'Wins']
        comp_stats['Win_Rate'] = (comp_stats['Wins'] / comp_stats['Entries']) * 100
        comp_stats = comp_stats[comp_stats['Wins'] >= 1].sort_values(by=['Wins', 'Win_Rate'], ascending=False).head(15).copy()
        
        comp_stats['Label'] = comp_stats.apply(lambda x: f"<b>{int(x['Win_Rate'])}%</b> ({int(x['Wins'])}/{int(x['Entries'])})", axis=1)
        
        fig = px.bar(
            comp_stats, x='Wins', y='Team', orientation='h', text='Label',
            title="Top Winning Teams (Win Count)", template='plotly_dark', color='Win_Rate', color_continuous_scale='Plasma'
        )
        fig.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(style_fig(fig), use_container_width=True, config=PLOT_CONFIG)

    # --- TAB 3: SKILL LIFT ---
    with tab3:
        st.subheader("⚡ Skill Lift Analysis")
        if finals_ocr.empty:
            st.warning("Need Finals OCR data.")
        else:
            c1, c2 = st.columns(2)
            winners_ocr = finals_ocr[finals_ocr['Is_Specific_Winner'] == 1].copy()
            
            with c1:
                sel_uma = st.selectbox("Character:", ["All"] + sorted(winners_ocr['Match_Uma'].unique()), key="lift_uma")
            with c2:
                sel_style = st.selectbox("Style:", ["All"] + sorted(winners_ocr['Clean_Style'].unique()), key="lift_style")
            
            w_filt = winners_ocr.copy()
            p_filt = prelims_raw.copy()
            
            if sel_uma != "All":
                w_filt = w_filt[w_filt['Match_Uma'] == sel_uma]
                p_filt = p_filt[p_filt['Match_Uma'] == sel_uma] if 'Match_Uma' in p_filt.columns else p_filt
            if sel_style != "All":
                w_filt = w_filt[w_filt['Clean_Style'] == sel_style]

            def get_freq(df):
                if 'skills' not in df.columns or df.empty: return pd.Series()
                s = df['skills'].astype(str).str.replace(r"[\[\]']", "", regex=True).str.split(',')
                return s.explode().str.strip().replace("", np.nan).dropna().value_counts(normalize=True) * 100

            lift = pd.concat([get_freq(w_filt).rename("Winner %"), get_freq(p_filt).rename("Baseline %")], axis=1).fillna(0)
            lift['Lift'] = lift['Winner %'] - lift['Baseline %']
            lift['New'] = lift['Baseline %'] == 0
            lift = lift[lift['Winner %'] > 5].copy()
            
            top = lift.sort_values('Lift', ascending=False).head(20).copy()
            if not top.empty:
                fig = px.bar(top, x='Lift', y=top.index, orientation='h', color='New',
                             title=f"Skill Lift (Specific Winners N={len(w_filt)})", template='plotly_dark',
                             color_discrete_map={True: '#FFD700', False: '#00CC96'})
                fig.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(style_fig(fig), use_container_width=True, config=PLOT_CONFIG)
            else:
                st.info("No data.")

    # --- TAB 4: CHAMPION STATS ---
    with tab4:
        st.subheader("🏆 Champion Stat Distribution")
        if not finals_ocr.empty:
            c1, c2 = st.columns(2)
            with c1:
                sel_uma_stat = st.selectbox("Character:", ["All"] + sorted(finals_ocr['Match_Uma'].unique()), key="stat_uma")
            with c2:
                sel_style_stat = st.selectbox("Style:", ["All"] + sorted(finals_ocr['Clean_Style'].unique()), key="stat_style")
            
            w_df = finals_ocr[finals_ocr['Is_Specific_Winner'] == 1].copy()
            w_df['Group'] = 'Champions'
            f_df = prelims_raw.copy()
            f_df['Group'] = 'The Field'
            
            if sel_uma_stat != "All":
                w_df = w_df[w_df['Match_Uma'] == sel_uma_stat]
                f_df = f_df[f_df['Match_Uma'] == sel_uma_stat] if 'Match_Uma' in f_df.columns else f_df
            if sel_style_stat != "All":
                w_df = w_df[w_df['Clean_Style'] == sel_style_stat]
                f_df = f_df[f_df['Clean_Style'] == sel_style_stat] if 'Clean_Style' in f_df.columns else f_df

            cols = [c for c in ['Speed', 'Stamina', 'Power', 'Guts', 'Wit'] if c in w_df.columns and c in f_df.columns]
            if cols and not w_df.empty:
                melt = pd.concat([w_df[cols+['Group']], f_df[cols+['Group']]]).melt(id_vars='Group', value_vars=cols)
                fig = px.box(melt, x='variable', y='value', color='Group', template='plotly_dark',
                             color_discrete_map={'Champions': '#00CC96', 'The Field': '#EF553B'})
                st.plotly_chart(style_fig(fig), use_container_width=True, config=PLOT_CONFIG)
            else:
                st.warning("Insufficient stats.")

    # --- TAB 5: GLOBAL STATS ---
    with tab5:
        st.subheader("🌐 Global Event Statistics")
        
        if global_stats.empty:
            st.warning("No global stats available.")
        else:
            col_g1, col_g2 = st.columns(2)

            # 1. Fraud Award
            with col_g1:
                st.markdown("##### 🤡 The 'Fraud' Award")
                st.caption("Highest usage (>200) with **lowest** Individual Win Rates.")
                fraud_stats = global_stats[global_stats['Total Entries'] > 200].sort_values('Win Rate %', ascending=True).head(10)
                
                if not fraud_stats.empty:
                    fig_fraud = px.bar(fraud_stats, x='Win Rate %', y='Uma Name', orientation='h', text='Total Entries',
                        title="Lowest Win Rates (Min 200 Entries)", template='plotly_dark', color='Win Rate %', color_continuous_scale='Redor_r')
                    fig_fraud.update_traces(texttemplate='%{text} Entries', textposition='outside')
                    fig_fraud.update_yaxes(categoryorder='total descending') 
                    st.plotly_chart(style_fig(fig_fraud, height=400), use_container_width=True, config=PLOT_CONFIG)
                else:
                    st.info("No data.")

            # 2. Oshi Strugglers
            with col_g2:
                st.markdown("##### 💔 Oshi Strugglers")
                st.caption("Niche picks (20 < Entries < 200) with **lowest** Win Rates.")
                struggle_stats = global_stats[(global_stats['Total Entries'] < 200) & (global_stats['Total Entries'] > 20)].sort_values('Win Rate %', ascending=True).head(10)
                
                if not struggle_stats.empty:
                    fig_struggle = px.bar(struggle_stats, x='Win Rate %', y='Uma Name', orientation='h', text='Total Entries',
                        title="Lowest Win Rates (20 < Entries < 200)", template='plotly_dark', color='Win Rate %', color_continuous_scale='Redor_r')
                    fig_struggle.update_traces(texttemplate='%{text} Entries', textposition='outside')
                    fig_struggle.update_yaxes(categoryorder='total descending')
                    st.plotly_chart(style_fig(fig_struggle, height=400), use_container_width=True, config=PLOT_CONFIG)
                else:
                    st.info("No data.")

            st.markdown("---")
            
            # Row 2: Oshi Winners
            col_g3, col_g4 = st.columns(2)
            with col_g3:
                st.markdown("##### 💎 Oshi Winners (Hidden Gems)")
                st.caption("Niche picks (20 < Entries < 200) with **highest** Win Rates.")
                oshi_winners = global_stats[(global_stats['Total Entries'] < 200) & (global_stats['Total Entries'] > 20)].sort_values('Win Rate %', ascending=False).head(10)
                
                if not oshi_winners.empty:
                    fig_oshi = px.bar(oshi_winners, x='Win Rate %', y='Uma Name', orientation='h', text='Total Entries',
                        title="Highest Win Rates (20 < Entries < 200)", template='plotly_dark', color='Win Rate %', color_continuous_scale='Greens')
                    fig_oshi.update_traces(texttemplate='%{text} Entries', textposition='outside')
                    fig_oshi.update_yaxes(categoryorder='total ascending')
                    st.plotly_chart(style_fig(fig_oshi, height=400), use_container_width=True, config=PLOT_CONFIG)
            
            with col_g4:
                st.info("ℹ️ **Methodology:** Stats are derived from **all 9 slots** in the finals lobby (Own + Opponents). 'Win Rate' represents the individual probability of a specific horse winning the race.")

            # 3. Placement Charts (Using global_stats)
            st.markdown("##### 🏅 Finals Placement Breakdown")
            # global_stats has 'Wins' and 'Total Entries'. We can derive "Didn't Win".
            
            # Filter Top 20 by Popularity
            top_20 = global_stats.sort_values('Total Entries', ascending=False).head(20).copy()
            top_20['Didn\'t Win'] = top_20['Total Entries'] - top_20['Wins']
            
            # Melt for Stacked Bar
            place_long = top_20.melt(id_vars='Uma Name', value_vars=['Wins', 'Didn\'t Win'], var_name='Result', value_name='Count')
            
            fig_place = px.bar(place_long, x='Count', y='Uma Name', color='Result', orientation='h',
                title="Placement Counts (Top 20 Most Popular)", template='plotly_dark',
                color_discrete_map={'Wins': '#FFD700', 'Didn\'t Win': '#333333'}
            )
            fig_place.update_layout(yaxis={'categoryorder':'total ascending'}, barmode='stack')
            st.plotly_chart(style_fig(fig_place), use_container_width=True, config=PLOT_CONFIG)
            
            # Percentage Chart
            top_20['Win %'] = (top_20['Wins'] / top_20['Total Entries']) * 100
            top_20['Lose %'] = 100 - top_20['Win %']
            
            place_pct_long = top_20.melt(id_vars='Uma Name', value_vars=['Win %', 'Lose %'], var_name='Result', value_name='Pct')
            
            # Sort by Win %
            # We need to manually sort the dataframe to control order in the chart since we want it sorted by Win %
            top_20_sorted = top_20.sort_values('Win %', ascending=True)
            
            fig_place_pct = px.bar(place_pct_long, x='Pct', y='Uma Name', color='Result', orientation='h',
                title="Placement Shares (Sorted by Win %)", template='plotly_dark',
                color_discrete_map={'Win %': '#FFD700', 'Lose %': '#333333'}
            )
            fig_place_pct.update_yaxes(categoryorder='array', categoryarray=top_20_sorted['Uma Name'])
            st.plotly_chart(style_fig(fig_place_pct), use_container_width=True, config=PLOT_CONFIG)

    # --- TAB 6: ECONOMICS ---
    with tab6:
        st.subheader("💸 Economics & Investment")
        econ_df = matches_df[matches_df['Spending_Text'] != 'Unknown'].copy()
        if not econ_df.empty:
            spend_stats = econ_df.groupby('Spending_Text').agg({'Is_Specific_Winner': ['mean', 'count'], 'Sort_Money': 'mean'}).reset_index()
            spend_stats.columns = ['Tier', 'Win_Rate', 'Entries', 'Sort_Val']
            spend_stats['Win_Rate'] *= 100
            spend_stats = spend_stats.sort_values('Sort_Val')
            
            fig_spend = px.bar(spend_stats, x='Tier', y='Win_Rate', text='Entries', title="Spending vs Individual Win Rate", template='plotly_dark', color='Win_Rate', color_continuous_scale='Greens')
            fig_spend.update_traces(texttemplate='%{text} Entries', textposition='outside')
            st.plotly_chart(style_fig(fig_spend), use_container_width=True, config=PLOT_CONFIG)