import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from collections import Counter

def style_fig(fig, title=None):
    """Applies a colorful, dark-mode friendly theme to Plotly charts."""
    fig.update_layout(
        template="plotly_dark",
        title=dict(text=title, font=dict(size=20, color="#FAFAFA")) if title else None,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        hoverlabel=dict(bgcolor="#333333", font_size=12, font_family="Arial"),
        font=dict(color="#E0E0E0"),
        margin=dict(l=20, r=20, t=50, b=20),
        xaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.2)'),
        yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.2)'),
    )
    return fig

def show_view(config_item):
    from virgo_utils import load_finals_data
    
    st.header(f"📊 {config_item['id']} - Championship Analysis")
    
    # Load Data
    df, _ = load_finals_data(config_item) # Ignore raw_dfs
    
    if df.empty:
        st.warning("No analysis data available yet.")
        return

    # --- GLOBAL SIDEBAR FILTERS ---
    st.markdown("### 🎯 Analysis Filters")
    
    # 1. Finals Group Filter (A/B)
    available_groups = sorted(df['Finals_Group'].dropna().unique())
    default_idx = available_groups.index("A Finals") if "A Finals" in available_groups else 0
    selected_group = st.sidebar.radio("Finals Group", available_groups, index=default_idx)
    
    df_group = df[df['Finals_Group'] == selected_group]

    # 2. Uma Filter
    all_umas = ["All Umas"] + sorted(df_group['Clean_Uma'].dropna().unique())
    selected_uma = st.selectbox("Filter by Uma", all_umas)
    
    # 3. Style Filter
    all_styles = ["All Styles"] + sorted(df_group['Clean_Style'].dropna().unique())
    selected_style = st.selectbox("Filter by Strategy", all_styles)

    # --- APPLY FILTERS ---
    df_filtered = df_group.copy()
    if selected_uma != "All Umas":
        df_filtered = df_filtered[df_filtered['Clean_Uma'] == selected_uma]
    if selected_style != "All Styles":
        df_filtered = df_filtered[df_filtered['Clean_Style'] == selected_style]

    # Baseline DF (Respects Style ONLY - for Comparisons)
    df_baseline = df_group.copy()
    if selected_style != "All Styles":
        df_baseline = df_baseline[df_baseline['Clean_Style'] == selected_style]

    # --- METRICS ---
    # Calculate strictly based on filters
    winners_df = df_filtered[df_filtered['Is_Winner'] == 1]

    st.info("👆 **Select a specific Uma from the Top** to see their detailed Profile.")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Runs", len(df_filtered))
    c2.metric("Winners Analyzed", len(winners_df))
    if selected_uma != "All Umas":
        win_rate = (len(winners_df) / len(df_filtered) * 100) if len(df_filtered) > 0 else 0
        c3.metric(f"{selected_uma} WR%", f"{win_rate:.1f}%")
    else:
        c3.metric("Avg Win Rate", f"{(len(winners_df)/len(df_filtered)*100):.1f}%" if len(df_filtered) else "0%")

    st.markdown("---")

    # --- TABS ---
    tab_overview, tab_stats, tab_meta, tab_records, tab_impact = st.tabs([
        "🏆 Champion Profile", 
        "💪 Stats & Build", 
        "🌍 Meta Trends",
        "🥛 Hall of Milk",
        "👑 Meta Impact"
    ])

    # =========================================================
    # TAB 1: CHAMPION PROFILE (Replaces Oshi Viewer)
    # =========================================================
    with tab_overview:
        if selected_uma == "All Umas":
            
            
            # Show Leaderboard if no specific Uma selected
            st.subheader(f"🏆 {selected_group} Leaderboard")
            if selected_style != "All Styles":
                st.caption(f"Showing rankings for **{selected_style}** strategy only.")

            # FIX: Use df_filtered to respect Strategy filter
            leaderboard = df_filtered.groupby('Clean_Uma').agg(
                Entries=('Clean_Uma', 'count'),
                Wins=('Is_Winner', 'sum')
            ).reset_index()
            leaderboard['Win Rate %'] = (leaderboard['Wins'] / leaderboard['Entries'] * 100).round(1)
            leaderboard = leaderboard.sort_values(['Wins', 'Win Rate %'], ascending=[False, False]).reset_index(drop=True)
            leaderboard.index += 1
            
            st.dataframe(
                leaderboard, 
                width='stretch',
                column_config={
                    "Win Rate %": st.column_config.ProgressColumn("Win Rate", format="%.1f%%", min_value=0, max_value=100),
                    "Clean_Uma": st.column_config.TextColumn("Uma Name"),
                    "Entries": st.column_config.NumberColumn("Total Entries")
                },
                column_order=["Clean_Uma", "Wins","Entries","Win Rate %"]
            )
        else:
            # --- DETAILED OSHI VIEW ---
            st.subheader(f"🌟 {selected_uma} Analysis")
            
            if winners_df.empty:
                st.warning(f"No significant recorded wins for {selected_uma} in {selected_group} yet.")
            else:
                c_radar, c_cards = st.columns([1, 1])
                
                # --- A. RADAR CHART (Comparison) ---
                with c_radar:
                    stats = ['Speed', 'Stamina', 'Power', 'Guts', 'Wit']
                    if all(s in winners_df.columns for s in stats):
                        uma_stats = winners_df[stats].mean().values.tolist()
                        
                        # FIX: Baseline uses df_baseline (All Winners matching Strategy)
                        # This ensures "Runaway Oguri" is compared to "Avg Runaway Winner", not "Avg Any Winner"
                        baseline_winners = df_baseline[df_baseline['Is_Winner'] == 1]
                        if not baseline_winners.empty:
                            all_winner_stats = baseline_winners[stats].mean().values.tolist()
                            baseline_name = f"Global Avg ({selected_style})" if selected_style != "All Styles" else "Global Avg Winner"
                        else:
                            all_winner_stats = [0]*5
                            baseline_name = "Global Avg (No Data)"

                        fig = go.Figure()
                        
                        fig.add_trace(go.Scatterpolar(
                            r=all_winner_stats, theta=stats, fill='toself', 
                            name=baseline_name, line_color='rgba(128, 128, 128, 0.5)'
                        ))
                        fig.add_trace(go.Scatterpolar(
                            r=uma_stats, theta=stats, fill='toself', 
                            name=f'{selected_uma} Avg', line_color='#00CC96'
                        ))
                        
                        fig.update_layout(
                            polar=dict(
                                radialaxis=dict(visible=True, range=[0, 1800]),
                                angularaxis=dict(rotation=90, direction="clockwise")
                            ), 
                            showlegend=True
                        )
                        st.plotly_chart(style_fig(fig, f"Stat Comparison: {selected_uma}"), width='stretch')

                # --- B. TOP SUPPORT CARDS ---
                with c_cards:
                    card_cols = [c for c in winners_df.columns if 'card' in c.lower() and 'name' in c.lower()]
                    all_cards = []
                    for col in card_cols:
                        all_cards.extend(winners_df[col].dropna().tolist())
                    
                    if all_cards:
                        card_counts = pd.DataFrame(Counter(all_cards).items(), columns=['Card', 'Count'])
                        card_counts = card_counts.sort_values('Count', ascending=True).tail(10)
                        
                        fig_cards = px.bar(card_counts, x='Count', y='Card', orientation='h', text='Count',
                                           color_discrete_sequence=['#AB63FA'])
                        st.plotly_chart(style_fig(fig_cards, "Most Used Support Cards (Winners)"), width='stretch')

                # --- C. WINNING SKILLS ---
                st.markdown("#### ⚡ Top Skills on Winning Runs")
                if 'Skill_List' in winners_df.columns:
                    all_skills = []
                    for skills in winners_df['Skill_List']:
                        if isinstance(skills, list): all_skills.extend(skills)
                    
                    if all_skills:
                        skill_counts = pd.DataFrame(Counter(all_skills).items(), columns=['Skill', 'Count'])
                        skill_counts = skill_counts.sort_values('Count', ascending=True).tail(15)
                        
                        fig_skills = px.bar(skill_counts, x='Count', y='Skill', orientation='h', text='Count',
                                            color='Count', color_continuous_scale='Viridis')
                        st.plotly_chart(style_fig(fig_skills, f"Top Skills For {selected_uma} Winners"), width='stretch')

    # =========================================================
    # TAB 2: STATS & BUILD (Aggregate)
    # =========================================================
    with tab_stats:
        st.subheader("💪 Stat Distributions (Winners Only)")
        
        if winners_df.empty:
            st.warning("No winners to analyze.")
        else:
            # --- 1. BOX PLOTS (Stat Spread) ---
            stat_cols = ['Speed', 'Stamina', 'Power', 'Guts', 'Wit']
            # Melt for Faceted Box Plot
            melted_stats = winners_df[stat_cols].melt(var_name='Stat', value_name='Value')
            
            fig_box = px.box(melted_stats, x='Stat', y='Value', color='Stat', 
                             points="all", # Show individual dots
                             color_discrete_sequence=px.colors.qualitative.Bold)
            st.plotly_chart(style_fig(fig_box, "Stat Spread of Winners"), width='stretch')
            
            st.markdown("---")
            
            # --- 2. SKILL COUNT HISTOGRAM ---
            if 'Skill_Count' in winners_df.columns:
                fig_hist = px.histogram(winners_df, x='Skill_Count', nbins=15, 
                                        color_discrete_sequence=['#EF553B'], opacity=0.8, labels={'Skill_Count': 'Number of Skills', 'count': 'Number of Winners'})
                fig_hist.update_layout(bargap=0.1)
                st.plotly_chart(style_fig(fig_hist, "Number of Skills per Winner"), width='stretch')

    # =========================================================
    # TAB 3: META TRENDS
    # =========================================================
    with tab_meta:
        st.subheader("🌍 Meta Environment")
        
        # --- 1. WIN RATE BY RUNNING STYLE ---
        if 'Clean_Style' in df_group.columns:
            # Group by Style
            style_stats = df_group.groupby('Clean_Style').agg(
                Runs=('Clean_Style', 'count'),
                Wins=('Is_Winner', 'sum')
            ).reset_index()
            style_stats['Win Rate %'] = (style_stats['Wins'] / style_stats['Runs'] * 100).round(1)
            style_stats = style_stats[style_stats['Runs'] > 5] # Filter noise
            
            if not style_stats.empty:
                fig_style = px.bar(style_stats, x='Clean_Style', y='Win Rate %', text='Win Rate %', labels={'Clean_Style': 'Running Strategy', 'Win Rate %': 'Win Rate (%)'},
                                   color='Clean_Style', color_discrete_sequence=px.colors.qualitative.Pastel)
                st.plotly_chart(style_fig(fig_style, "Win Rate by Running Strategy"), width='stretch')
            else:
                st.info("Insufficient data for Style analysis.")

        st.markdown("---")

        # --- 2. WINNING GATE (POST) BIAS ---
        if 'Post' in winners_df.columns:
            post_counts = winners_df['Post'].value_counts().sort_index()
            
            # Error Handler: Check if empty to prevent PX ValueError
            if not post_counts.empty:
                fig_post = px.bar(x=post_counts.index, y=post_counts.values, 
                                  color_discrete_sequence=['#00CC96'],
                                  labels={'x': 'Gate Number', 'y': 'Number of Wins'})
                fig_post.update_xaxes(dtick=1)
                st.plotly_chart(style_fig(fig_post, "Gate Bias (Post Position)"), width='stretch')
            else:
                st.info("Insufficient data for Gate analysis.")

        st.markdown("---")

        # --- 3. WINNING TIME DISTRIBUTION ---
        if 'Run_Time' in winners_df.columns:
            times = winners_df['Run_Time'].dropna()
            times = times[times > 60] # Basic filter
            
            if not times.empty:
                fig_time = px.histogram(times, nbins=30, color_discrete_sequence=['#FFA15A'], labels={'value': 'Time (seconds)', 'count': 'Number of Wins'})
                fig_time.update_layout(bargap=0.05)
                st.plotly_chart(style_fig(fig_time, "Distribution of Winning Times"), width='stretch')
            else:
                st.info("Insufficient data for Time analysis.")

    with tab_records:
        title_scope = f" {selected_uma}" if selected_uma != "All Umas" else "Global"
        st.subheader(f"🥛 Hall of Milk ({title_scope})")
        st.info("Showcasing unique and niche records from championship winners.")
        
        # Use filtered data (Specific Uma if selected, else All)
        rec_df = winners_df.copy()
        
        if rec_df.empty:
            st.warning(f"No winners found for {selected_uma}. Cannot determine records.")
        else:
            rec_df['Total_Stats'] = rec_df[['Speed','Stamina','Power','Guts','Wit']].sum(axis=1)
            
            # --- CUSTOM HTML CARD FUNCTION ---
            def record_card(label, value, row, color="#FFD700"):
                # 1. Stats String
                stats_txt = f"<b style='color:#ccc'>Stats:</b> {row.get('Speed',0)} / {row.get('Stamina',0)} / {row.get('Power',0)} / {row.get('Guts',0)} / {row.get('Wit',0)}"
                
                # 2. Skills String (Show ALL skills)
                skills = row.get('Skill_List', [])
                if isinstance(skills, list) and skills:
                    skills_str = ", ".join(skills)
                else:
                    skills_str = "No skills recorded (Manual Data?)"
                
                # 3. HTML Structure
                card_html = f"""
                <div style="
                    border: 1px solid rgba(255,255,255,0.15); 
                    border-radius: 10px; 
                    padding: 15px; 
                    background-color: rgba(30, 30, 40, 0.6); 
                    margin-bottom: 20px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                ">
                    <div style="color:{color}; font-weight:bold; font-size:1.1em; margin-bottom:5px; text-transform:uppercase; letter-spacing:1px;">
                        {label}
                    </div>
                    <div style="font-size:1.6em; font-weight:bold; margin-bottom:8px; color:#FAFAFA;">
                        {value}
                    </div>
                    <div style="font-size:1em; color:#00CC96; margin-bottom:10px; font-weight:500;">
                        🏆 {row['Clean_Uma']} <span style='color:#888; font-size:0.8em'>({row['Clean_Style']})</span> <br>
                        👤 {row['Clean_IGN']}
                    </div>
                    <div style="font-size:0.85em; color:#DDD; margin-bottom:8px; font-family:monospace;">
                        {stats_txt}
                    </div>
                    <div style="font-size:0.8em; color:#AAA; line-height:1.4; border-top:1px solid rgba(255,255,255,0.1); padding-top:8px;">
                        <span style="color:#888; font-weight:bold;">BUILD:</span> {skills_str}
                    </div>
                </div>
                """
                st.markdown(card_html, unsafe_allow_html=True)

            # --- ROW 1: PERFORMANCE ---
            c1, c2, c3 = st.columns(3)
            with c1:
                if 'Run_Time' in rec_df.columns:
                    fastest = rec_df.loc[rec_df['Run_Time'].idxmin()]
                    record_card("⚡ Fastest Time", fastest['Run_Time_Str'], fastest, "#00CC96")
            
            with c2:
                if 'Skill_Count' in rec_df.columns:
                    valid = rec_df[rec_df['Skill_Count'] > 0]
                    if not valid.empty:
                        min_skill = valid.loc[valid['Skill_Count'].idxmin()]
                        # For Minimalist, value is "X Skills"
                        record_card("📉 Minimalist Build (Lowest Number of Skills)", f"{min_skill['Skill_Count']} Skills", min_skill, "#AB63FA")
            
            with c3:
                # NICHE PICK LOGIC
                # --- UPDATED: RAREST CHAMPION LOGIC (Least Wins -> Least Entries) ---
                if selected_uma == "All Umas":
                    # 1. Count Wins in CURRENT FILTERED VIEW
                    win_counts = winners_df['Clean_Uma'].value_counts()
                    # 2. Count Entries in CURRENT FILTERED VIEW
                    entry_counts = df_filtered['Clean_Uma'].value_counts()
                    
                    # 3. Find unique winners and sort
                    unique_winners = winners_df['Clean_Uma'].unique()
                    if len(unique_winners) > 0:
                        data = [{'Uma': u, 'Wins': win_counts.get(u,0), 'Entries': entry_counts.get(u,0)} for u in unique_winners]
                        cand_df = pd.DataFrame(data).sort_values(by=['Wins', 'Entries'], ascending=[True, True])
                        
                        rarest_uma = cand_df.iloc[0]['Uma']
                        rarest_wins = cand_df.iloc[0]['Wins']
                        rarest_entries = cand_df.iloc[0]['Entries']
                        
                        rarest_row = winners_df[winners_df['Clean_Uma'] == rarest_uma].iloc[0]
                        record_card("🦄 Rarest Champion (Least Wins/Entries)", f"{rarest_wins} Wins / {rarest_entries} Runs", rarest_row, "#FFD700")
                else:
                    style_counts = df_filtered['Clean_Style'].value_counts()
                    rec_df['Style_Pop'] = rec_df['Clean_Style'].map(style_counts)
                    rarest = rec_df.loc[rec_df['Style_Pop'].idxmin()]
                    record_card("🦄 Rare Strategy", f"{rarest['Clean_Style']}", rarest, "#FFD700")
            
            # --- ROW 2: STATS ---
            c4, c5, c6 = st.columns(3)
            with c4:
                underdog = rec_df.loc[rec_df['Total_Stats'].idxmin()]
                record_card("🐕 Underdog (Lowest Total Stats)", underdog['Total_Stats'], underdog, "#EF553B")
            with c5:
                min_spd = rec_df.loc[rec_df['Speed'].idxmin()]
                record_card("🐌 Lowest Speed", min_spd['Speed'], min_spd, "#FFA15A")
            with c6:
                min_pwr = rec_df.loc[rec_df['Power'].idxmin()]
                record_card("💪 Lowest Power", min_pwr['Power'], min_pwr, "#19D3F3")

            c7, c8, c9 = st.columns(3)
            with c7:
                min_sta = rec_df.loc[rec_df['Stamina'].idxmin()]
                record_card("😴 Lowest Stamina", min_sta['Stamina'], min_sta, "#FF6692")
            with c8:
                max_guts = rec_df.loc[rec_df['Guts'].idxmax()]
                record_card("🏃 Highest Guts", max_guts['Guts'], max_guts, "#B6E880")
            with c9:
                min_wit = rec_df.loc[rec_df['Wit'].idxmin()]
                record_card("🧠 Lowest Wit", min_wit['Wit'], min_wit, "#FF97FF")

            # --- NICHE GALLERY ---
            st.markdown("### 📜 Niche Hall of Fame")
            if selected_uma == "All Umas":
                st.caption("Winners with < 10 Umas in the Finals.")
                global_counts = df_group['Clean_Uma'].value_counts()
                niche_winners = rec_df[rec_df['Clean_Uma'].map(global_counts) < 10].copy()
            else:
                st.caption(f"Winners using off-meta strategies for {selected_uma}.")
                style_map = df_group.groupby('Clean_Uma')['Clean_Style'].value_counts(normalize=True)
                niche_indices = []
                for idx, row in rec_df.iterrows():
                    try:
                        if style_map[row['Clean_Uma']][row['Clean_Style']] < 0.15:
                            niche_indices.append(idx)
                    except: continue
                niche_winners = rec_df.loc[niche_indices]

            if not niche_winners.empty:
                disp = niche_winners[['Clean_IGN', 'Clean_Uma', 'Clean_Style', 'Speed', 'Power', 'Wit', 'Skill_Count', 'Run_Time_Str']]
                st.dataframe(disp, width='stretch', hide_index=True, column_config={"Clean_IGN": "IGN", "Clean_Uma": "Uma Name", "Clean_Style": "Running Style", "Speed": "Speed", "Power": "Power", "Wit": "Wit", "Skill_Count": "Skills", "Run_Time_Str": "Run Time"})
            else:
                st.info("No niche winners found matching criteria.")

    with tab_impact:
        st.subheader("👑 Meta Impact Tier List")
        st.markdown("Visualizing the relationship between **Popularity (Pick Rate)** and **Performance (Win Rate)**.")
        
        # 1. Aggregate Data
        meta_df = df_group.groupby('Clean_Uma').agg(
            Runs=('Clean_Uma', 'count'),
            Wins=('Is_Winner', 'sum')
        ).reset_index()
        
        # 2. Calculations
        total_pop = meta_df['Runs'].sum()
        meta_df['Pick Rate %'] = (meta_df['Runs'] / total_pop * 100).round(2)
        meta_df['Win Rate %'] = (meta_df['Wins'] / meta_df['Runs'] * 100).round(2)
        
        # Filter noise
        meta_df = meta_df[meta_df['Runs'] >= 5]
        
        if meta_df.empty:
            st.warning("Not enough data to generate Tier List.")
        else:
            # 3. Scatter Plot
            fig_scatter = px.scatter(
                meta_df, 
                x='Pick Rate %', 
                y='Win Rate %', 
                size='Runs', 
                color='Win Rate %',
                hover_name='Clean_Uma',
                color_continuous_scale='RdYlGn',
                size_max=100,
                title=f"Meta Landscape ({selected_group})"
            )
            
            # Quadrant Lines (Median)
            avg_wr = meta_df['Win Rate %'].mean()
            avg_pick = meta_df['Pick Rate %'].mean()
            
            fig_scatter.add_hline(y=avg_wr, line_dash="dot", line_color="gray", annotation_text="Avg Win Rate")
            fig_scatter.add_vline(x=avg_pick, line_dash="dot", line_color="gray", annotation_text="Avg Pick Rate")
            
            fig_scatter.update_traces(textposition='top center')
            st.plotly_chart(style_fig(fig_scatter), width='stretch')
            
            st.caption("""
            - **Top Right:** Meta Kings (High Use, High Wins)
            - **Top Left:** Specialists / Sleepers (Low Use, High Wins)
            - **Bottom Right:** Popular Bait (High Use, Low Wins)
            """)