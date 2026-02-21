import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from textwrap import dedent
from collections import Counter
from uma_utils import BUBBLE_CONFIG, get_card_rarity_map, render_visual_card_list, get_type_icon_src, get_uma_base64, get_stat_icon_base64, add_img_chart
from uma_utils import load_finals_data

STAT_CHECKPOINTS = {
    'Speed':   { 600: "We be sandbagging", 800: "GOTTA GO FAST", 1000: "VROOOOOOM", 1200: "Speed Cap"},
    'Stamina': {370: "ARE YOU BAKUSHINING TEAM TRIALS?", 600: "TT Mile Runner", 800: "Much stamina, much good", 1000: "So much untapped power", 1200: "WOW, SO MUCH STAMINA"},
    'Power':   {400: "How we getting up the hill bro?", 600: "is this a long?", 800 : "John Power", 1000: "I tap my power and I win the game", 1200: "Power Cap"},
    'Guts':    {0: "You have to read berserk", 500: "Unc Guts", 800: "Why don't skeletons fight each other?", 1000: "Meta Guts", 1000: "GUTS MAXXING", 1200: "GIGACHAD GUTS ENJOYER"},
    'Wit':     {300: "STUDY MORE BECOME DOCTOR", 400: "Perfection", 600: "Megamind", 800: "3 Wit cards, how original", 1000: "SURRRELLLY EVERY SKILL PROCS", 1200: "Wit CAAPPPPPPPPPPPPPPPPPP"},
}

def get_checkpoint_text(stat_name, value):
    thresholds = STAT_CHECKPOINTS.get(stat_name, {})
    # Find the highest threshold met
    met = [msg for lim, msg in thresholds.items() if value >= lim]
    return met[-1] if met else ""

def render_stat_row(stat, uma_val, global_val, color):
    icon_src = get_stat_icon_base64(stat)

    # Bar Widths (Max 1200 adjustable based on scenario)
    max_val = 1200 
    uma_pct = min(uma_val / max_val * 100, 100)  
    global_pct = min(global_val / max_val * 100, 100)
    
    # Checkpoint Logic
    checkpoint_msg = get_checkpoint_text(stat, uma_val)
    if uma_pct >= global_pct:
        checkpoint_html = f'<span style="color: #FFD700; font-size: 0.7em; margin-left: 6px;">★ {checkpoint_msg}</span>' if checkpoint_msg else ""
    else:
        checkpoint_html = f'<span style="color: #FFD700; font-size: 0.7em; margin-left: 6px;">{checkpoint_msg}</span>' if checkpoint_msg else ""
    
    
    
    # Icon HTML: Use <img> if found, else Text
    if icon_src:
        icon_html = f'<img src="{icon_src}" style="width: 24px; vertical-align: middle; margin-right: 8px;">'
    else:
        icon_html = f'<span style="margin-right: 8px;">{stat[:3].upper()}</span>'

    return f"""
<div style="margin-bottom: 8px;">
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px;">
<div style="display: flex; align-items: center; color: {color}; font-weight: bold;">
{icon_html} {int(uma_val)} {checkpoint_html}
</div>
<div style="font-size: 0.75em; color: #888;"> Global Average: {int(global_val)}</div>
</div>
<div style="position: relative; width: 100%; height: 8px; background: rgba(255,255,255,0.1); border-radius: 4px;">
<div style="position: absolute; left: {global_pct}%; top: -2px; bottom: -2px; width: 2px; background: rgba(255,255,255,0.5); z-index: 1;"></div>
<div style="width: {uma_pct}%; height: 100%; background: {color}; border-radius: 4px; opacity: 0.9;"></div>
</div>
</div>"""

def set_uma_filter(name):
    st.session_state.selected_uma_filter = name

def render_build_guide(uma_df):
    """
    Renders a specific build guide for the selected Uma.
    - Uses Base64 icons for Deck Archetypes.
    """
    
    
    st.markdown("### 🛠️ Build Guide")
    
    # 1. Filter Winners
    winners = uma_df[uma_df['Is_Winner'] == 1].copy()
    if winners.empty:
        st.info("No winning data available to generate a build guide.")
        return

    # 2. Style Filter
    available_styles = sorted(winners['Clean_Style'].dropna().unique())
    if len(available_styles) > 1:
        default_style = winners['Clean_Style'].value_counts().idxmax()
        c_filter, _ = st.columns([1, 2])
        with c_filter:
            selected_build_style = st.selectbox(
                "Select Strategy:", 
                available_styles, 
                index=available_styles.index(default_style),
                key="build_guide_style_filter"
            )
        winners = winners[winners['Clean_Style'] == selected_build_style]
        st.caption(f"Analyzing: **{selected_build_style}**")

    # --- METRICS ---
    col_A, col_B = st.columns([1, 1])
    
    # 3. ARCHETYPE (Visual Update with Base64)
    with col_A:
        st.markdown("#### 📐 Recommended Deck")
        
        archetypes = []
        for _, row in winners.iterrows():
            current_types = []
            for i in range(1, 7):
                c_type = row.get(f'card{i}_type')
                if pd.notna(c_type) and str(c_type).lower() not in ['nan', 'none', '', 'unknown']:
                    current_types.append(str(c_type).capitalize())
            
            if current_types:
                counts = Counter(current_types)
                sorted_tc = tuple(sorted(counts.items(), key=lambda x: (-x[1], x[0])))
                archetypes.append(sorted_tc)
        
        if archetypes:
            common_archs = Counter(archetypes).most_common(5)
            top_arch, top_count = common_archs[0]
            
            # Helper to render archetype HTML with Base64 Icons
            def render_arch_html(arch_tuple, count=None, is_main=False):
                html_parts = []
                for type_name, qty in arch_tuple:
                    icon_src = get_type_icon_src(type_name)
                    
                    block = f"""
                    <div style="display: inline-flex; align-items: center; margin-right: 12px; background: rgba(255,255,255,0.05); padding: 4px 8px; border-radius: 6px;">
                        <span style="font-weight: bold; margin-right: 4px; font-size: {'1.1em' if is_main else '0.9em'};">{qty}x</span>
                        <img src="{icon_src}" style="width: {'24px' if is_main else '18px'}; height: {'24px' if is_main else '18px'}; vertical-align: middle;">
                    </div>
                    """
                    html_parts.append(block)
                
                inner_html = "".join(html_parts)
                
                if count:
                    usage_html = f"<div style='margin-top: 4px; font-size: 0.8em; color: #888;'>Used by {count} winners</div>"
                    return f"<div>{inner_html}</div>{usage_html}"
                return f"<div>{inner_html}</div>"

            # Render Meta Build
            st.success("✅ **Meta Standard**")
            st.markdown(f"""
                            <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.1);">
                                {render_arch_html(top_arch, count=top_count, is_main=True)}
                                <span style="font-size: 0.9em; color: #AAA;"></span>
                            </div>
                            """, unsafe_allow_html=True)
            
            
            # Render Alternatives
            if len(common_archs) > 1:
                st.markdown("##### 🔀 Alternatives")
                with st.container():
                    for arch, count in common_archs[1:]:
                        st.markdown(
                            f"""
                            <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.1);">
                                {render_arch_html(arch, is_main=False)}
                                <span style="font-size: 0.9em; color: #AAA;">{count} runs</span>
                            </div>
                            """, 
                            unsafe_allow_html=True
                        )

    # 4. INVESTMENT (No changes needed)
    with col_B:
        st.markdown("#### 💰 Cost Analysis")
        rarity_map = get_card_rarity_map()
        
        ssr_counts = []
        for _, row in winners.iterrows():
            high_level_ssrs = 0
            for i in range(1, 7):
                c_id = row.get(f'card{i}_id')
                raw_lvl = row.get(f'card{i}_level')
                
                is_ssr = rarity_map.get(c_id, False)
                lvl = 0
                try:
                    val = str(raw_lvl).upper()
                    if "MLB" in val: lvl = 50
                    elif "LB" in val: lvl = int(float(val.replace("LB","")))
                    else: lvl = int(float(val))
                except: pass
                
                if is_ssr and lvl >= 45:
                    high_level_ssrs += 1
            ssr_counts.append(high_level_ssrs)
        
        if ssr_counts:
            avg_whale_score = sum(ssr_counts) / len(ssr_counts)
            st.metric("Avg Maxed SSRs", f"{avg_whale_score:.1f} / 6")
            
            if avg_whale_score > 3.5:
                st.warning("⚠️ **Expensive** (Requires 4+ Maxed SSRs)")
            elif avg_whale_score > 1.5:
                st.info("⚖️ **Moderate** (2-3 SSRs + Borrow)")
            else:
                st.success("✅ **Budget Friendly** (SR Heavy)")

    st.markdown("---")
    
    # 5. CORE CARDS (Visual Grid)
    if not winners.empty:
        uma_cards = []
        for _, row in winners.iterrows():
            for i in range(1, 7):
                c_name = row.get(f'card{i}_name')
                c_type = row.get(f'card{i}_type')
                c_id = row.get(f'card{i}_id')
                
                if pd.notna(c_name) and str(c_name).strip() not in ["", "None", "nan"]:
                    uma_cards.append({
                        "Name": c_name,
                        "Type": str(c_type).capitalize(),
                        "ID": c_id
                    })
                    
        if uma_cards:
            card_df = pd.DataFrame(uma_cards)
            # Safe aggregation
            stats = card_df.groupby('ID').agg({
                'Name': 'first',
                'Type': 'first',
                'ID': 'count'
            }).rename(columns={'ID': 'Count'}).reset_index()
            
            stats['Usage %'] = (stats['Count'] / len(winners) * 100)
            
            render_visual_card_list(
                stats, 
                title=f"🃏 Core Cards for {winners['Clean_Uma'].iloc[0]} ({winners['Clean_Style'].iloc[0]})",
                limit=12
            )
            
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
    
    st.warning("this page is under construction and may not function as intended.")
    st.header(f"📊 {config_item['id']} - Championship Analysis")
    
    # Load Data
    df, _ = load_finals_data(config_item) # Ignore raw_dfs
    
    if df.empty:
        st.warning("No analysis data available yet.")
        return

    # --- GLOBAL FINALS FILTERS ---
    st.markdown("### 🎯 Analysis Filters")
    col1, col2 = st.columns(2)
    with col1:
        # 1. LEAGUE FILTER (Graded / Open)
        # This comes first because A/B groups exist inside both leagues
        if 'League' in df.columns:
            # Determine available options dynamically
            available_leagues = sorted(df['League'].dropna().unique())
            
            # Default to Graded if it exists
            default_ix = available_leagues.index("Graded") if "Graded" in available_leagues else 0
            
            selected_league = st.radio("League", available_leagues, index=default_ix)
            
            # Filter the DataFrame immediately
            df_league = df[df['League'] == selected_league].copy()
        else:
            # Fallback for legacy data
            selected_league = "Graded"
            df_league = df

        if df_league.empty:
            st.warning(f"No data found for {selected_league} League.")
            return
    with col2:
        # 2. FINALS GROUP FILTER (A / B)
        # Only show groups that actually exist in the selected league
        available_groups = sorted(df_league['Finals_Group'].dropna().unique())
        
        if available_groups:
            default_idx = available_groups.index("A Finals") if "A Finals" in available_groups else 0
            selected_group = st.radio("Finals Group", available_groups, index=default_idx)
            df_group = df_league[df_league['Finals_Group'] == selected_group].copy()
            df_group = df_group[df_group['Clean_Style'] != 'Unknown']
        else:
            st.warning("No groups found for this league.")
            df_group = pd.DataFrame()

        if df_group.empty:
            st.warning("No data matching filters.")
            return

    # 2. Uma Filter
    all_umas = ["All Umas"] + sorted(df_group['Clean_Uma'].dropna().unique())
    #Initialize the state if it doesn't exist
    if "selected_uma_filter" not in st.session_state:
        st.session_state.selected_uma_key = "All Umas"
    selected_uma = st.selectbox("Filter by Uma", all_umas, key="selected_uma_filter")
    
    # 3. Style Filter
    all_styles = ["All Styles"] + sorted(df_group['Clean_Style'].dropna().unique())
    selected_style = st.selectbox("Filter by Strategy", all_styles)

    # --- APPLY FILTERS ---
    df_filtered = df_group.copy()
    if selected_uma != "All Umas":
        df_filtered = df_filtered[df_filtered['Clean_Uma'] == selected_uma].copy()
    if selected_style != "All Styles":
        df_filtered = df_filtered[df_filtered['Clean_Style'] == selected_style].copy()

    # Baseline DF (Respects Style ONLY - for Comparisons)
    df_baseline = df_group.copy()
    if selected_style != "All Styles":
        df_baseline = df_baseline[df_baseline['Clean_Style'] == selected_style]

    # --- METRICS ---
    # Calculate strictly based on filters
    winners_df = df_filtered[df_filtered['Is_Winner'] == 1]

    st.info("👆 **Select a specific Uma from the Top** and click on the Champion Profile tab to see their detailed Profile with Skills and Builds for the character.")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Runs", len(df_filtered))
    c2.metric("Total Winners + Opponents", len(winners_df))
    if selected_uma != "All Umas":
        win_rate = (len(winners_df) / len(df_filtered) * 100) if len(df_filtered) > 0 else 0
        c3.metric(f"{selected_uma} WR%", f"{win_rate:.1f}%")
    else:
        c3.metric("Avg Win Rate", f"{(len(winners_df)/len(df_filtered)*100):.1f}%" if len(df_filtered) else "0%")

    st.markdown("---")

    # --- TABS ---
    tab_overview, tab_stats, tab_meta, tab_records, tab_impact = st.tabs([
        "🏆 Champion Profile", 
        "💪 Stats & Aptitude", 
        "🌍 Meta Trends",
        "🥛 Hall of Milk",
        "👑 Meta Impact"
    ])

    # =========================================================
    # TAB 1: CHAMPION PROFILE (Replaces Oshi Viewer)
    # =========================================================
    with tab_overview:
        if selected_uma == "All Umas":
            st.subheader(f"🏆 {selected_league} Leaderboard")
            if selected_style != "All Styles":
                st.caption(f"Showing rankings for **{selected_style}** strategy only.")

            # 1. Prepare Data
            df_user_only = df_filtered[df_filtered['is_user'] == 1].copy()
            leaderboard = df_user_only.groupby('Clean_Uma').agg(
                Entries=('Clean_Uma', 'count'),
                Wins=('Is_Winner', 'sum')
            ).reset_index()
            
            total_entries = leaderboard['Entries'].sum()
            leaderboard['Win Rate'] = leaderboard['Wins'] / leaderboard['Entries'] *100
            total_wins = leaderboard['Wins'].sum()
            leaderboard['Win Share'] = (leaderboard['Wins'] / total_wins * 100)
            leaderboard['Normalized Win Share'] = ((leaderboard['Win Share'] - leaderboard['Win Share'].min()) / \
                                     (leaderboard['Win Share'].max() - leaderboard['Win Share'].min())) * 100
            
            # Sort by Wins (Meta) or Win Rate (Performance)
            leaderboard = leaderboard.sort_values(['Normalized Win Share','Win Rate'], ascending=[False, False]).head(20)
            
            
            for rank, row in leaderboard.iterrows():
                uma_name = row['Clean_Uma']
                win_per = row['Normalized Win Share']
                count = row['Wins']
                entries = row['Entries']
                win_rate = row['Win Rate']
                
                # 1. Get Image
                img_src = get_uma_base64(uma_name)
                if not img_src:
                    img_tag = f"<div style='width: 45px; height: 45px; background: #333; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 20px;'>🐴</div>"
                else:
                    img_tag = f"<img src='{img_src}' style='width: 45px; height: 45px; object-fit: cover; border-radius: 50%; border: 2px solid #555;'>"

                bar_width = min(win_per, 100)

                # 2. Create Layout: [ Card Visual (90%) ] [ Button (10%) ]
                c_card, c_btn = st.columns([0.90, 0.10])

                # 3. Render the Visual Card in the left column
                with c_card:
                    # We removed the bottom-margin from the HTML so it aligns better with the button
                    html_block = dedent(f"""
                        <div style="display: flex; align-items: center; background: rgba(255,255,255,0.05); padding: 8px; border-radius: 10px; height: 100%;">
                            <div style="margin-right: 12px;">{img_tag}</div>
                            <div style="flex-grow: 1;">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                                    <span style="font-weight: bold; font-size: 1em;">{uma_name}</span>
                                    <span style="font-weight: bold; color: #00CC96;">{win_rate:.1f}%</span>
                                </div>
                                <div style="width: 100%; height: 6px; background: #333; border-radius: 3px; overflow: hidden;">
                                    <div style="width: {bar_width}%; height: 100%; background: linear-gradient(90deg, #00CC96, #00b887);"></div>
                                </div>
                                <div style="font-size: 0.75em; color: #888; margin-top: 2px;">
                                    {count} User Wins / {entries} User Submitted {uma_name} Races
                                </div>
                            </div>
                        </div>
                    """)
                    st.markdown(html_block, unsafe_allow_html=True)

                # 4. Render the Action Button in the right column
                with c_btn:
                    # vertical whitespace to align the button with the card center
                    st.write("") 
                    st.button(
                        "🔍", 
                        key=f"btn_select_{uma_name}", 
                        help=f"Filter to {uma_name}'s Profile",
                        on_click=set_uma_filter,
                        args=(uma_name,)
                    )
                # a tiny spacer between rows
                st.write("")

        else:
            # --- DETAILED OSHI VIEW (Specific Character) ---
            st.subheader(f"🌟 {selected_uma} Analysis")
            
            st.info(f"Analysis based on **{selected_league}** data. Note that Stats, Skills, and Cards are sourced from user submitted OCR data merged with manual entries.")
            if winners_df.empty:
                st.warning(f"No significant recorded wins for {selected_uma} in {selected_league} yet.")
            
            if not winners_df.empty:
                # Get the Image Source (Base64)
                img_src = get_uma_base64(selected_uma)

                # 2. Comparison Logic (Same as before)
                stats = ['Speed', 'Stamina', 'Power', 'Guts', 'Wit']
                if all(s in winners_df.columns for s in stats):
                        uma_stats = winners_df[stats].mean().fillna(0).tolist()
                        if uma_stats is not None and sum(uma_stats) > 0:
                            # FIX: Baseline uses df_baseline (All Winners matching Strategy)
                            # This ensures "Runaway Oguri" is compared to "Avg Runaway Winner", not "Avg Any Winner"
                            baseline_winners = df_baseline[df_baseline['Is_Winner'] == 1]
                            if not baseline_winners.empty:
                                all_winner_stats = baseline_winners[stats].mean().values.tolist()
                                baseline_name = f"Global Avg ({selected_style})" if selected_style != "All Styles" else "Global Avg Winner"
                            else:
                                all_winner_stats = [0]*5
                                baseline_name = "Global Avg (No Data)"
                            
                            
                            if 'current_data' not in st.session_state:
                                st.session_state.current_data = False


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
                                    radialaxis=dict(visible=True, range=[0, 1200]),
                                    angularaxis=dict(rotation=90, direction="clockwise")
                                ),
                                showlegend=True
                            )
                            fig.add_layout_image(
                                dict(
                                    source=img_src,
                                    xanchor="center", 
                                    yanchor="middle",
                                    layer='above',      
                                    opacity=0.2,       
                                    xref='paper',
                                    yref='paper',
                                    visible=True,
                                    sizing='contain',   
                                    x=0.5, y=0.5,      
                                    sizex=0.6, sizey=0.6,
                                )
                            )
                            c_radar, c_df = st.columns([0.60, 0.40])
                            with c_radar:
                                radar_options = ['All Umas', f'{selected_uma}']
                                radar_selection = st.segmented_control(
                                    'Toggle Visibility', radar_options, selection_mode='multi', default=['All Umas', f'{selected_uma}']
                                )



                                if radar_selection == ['All Umas', f'{selected_uma}'] or radar_selection == [f'{selected_uma}', 'All Umas']:
                                    st.plotly_chart(style_fig(fig, f"Stat Comparison: {selected_uma}"), width='stretch')
                                else:
                                    def make_fig(data, name, color = '#00CC96', title= f"Stat Comparison: {selected_uma}", image = False):
                                        selected_fig = go.Figure(
                                            data=[go.Scatterpolar(
                                            r=data, 
                                            theta=stats, fill='toself', 
                                            name= name, 
                                            line_color= color)
                                                
                                            ]
                                        )
                                        selected_fig.update_layout(
                                            polar=dict(
                                            radialaxis=dict(visible=True, range=[0, 1200]),
                                            angularaxis=dict(rotation=90, direction="clockwise")
                                            ),
                                            showlegend=True
                                        )
                                        if image:
                                            selected_fig.add_layout_image(
                                                dict(
                                                    source=img_src,
                                                    xanchor="center", 
                                                    yanchor="middle",
                                                    layer='above',      
                                                    opacity=0.2,       
                                                    xref='paper',
                                                    yref='paper',
                                                    visible=True,
                                                    sizing='contain',   
                                                    x=0.5, y=0.5,      
                                                    sizex=0.6, sizey=0.6,
                                                )
                                            ) 
                                        st.plotly_chart(style_fig(selected_fig, title), width='stretch')

                                    if radar_selection == ['All Umas']:
                                        make_fig(all_winner_stats, 'Average Stats', color= "#D8EBE6", title = 'Average of All Umas')
                                    elif radar_selection == [f'{selected_uma}']:
                                        make_fig(uma_stats, f'{selected_uma} stats', title=f'Average of {selected_uma}', image = True) 
                                        
                                    
                                    
                            with c_df:
                                st.markdown(f"##### Mean Build Stats ({selected_uma})")
            
                                # Prepare Data
                                stats_list = ['Speed', 'Stamina', 'Power', 'Guts', 'Wit']
                                uma_means = winners_df[stats_list].mean().fillna(0)
                                
                                # Global Baseline Data
                                baseline_subset = df_baseline[df_baseline['Is_Winner'] == 1]
                                if not baseline_subset.empty:
                                    global_means = baseline_subset[stats_list].mean().fillna(0)
                                else:
                                    global_means = pd.Series([0]*5, index=stats_list)

                                stat_colors = {
                                                    'Speed': '#3B82F6',   # Blue
                                                    'Stamina': '#EF4444', # Red
                                                    'Power': '#F59E0B',   # Orange/Yellow
                                                    'Guts': '#EC4899',    # Pink
                                                    'Wit': '#10B981'      # Green
                                                }

                                # Render List
                                html_stack = ""
                                for stat in stats_list:
                                    html_stack += render_stat_row(
                                        stat, 
                                        uma_means[stat], 
                                        global_means[stat],
                                        stat_colors[stat]
                                    )
                                
                                # Wrap in a container for cleaner styling
                                st.markdown(dedent(f"""
                                <div style="background: rgba(0,0,0,0.2); padding: 15px; border-radius: 10px;">
                                    {html_stack}
                                </div>
                                """), unsafe_allow_html=True)
                else:
                    st.info("Insufficient stat data for radar chart.")
                            

                # # --- B. TOP SUPPORT CARDS (Small Visual) ---
                # with c_cards:  
                #     st.markdown("#### 🃏 Top Cards")
                #     uma_cards_list = []
                #     for _, row in winners_df.iterrows():
                #         for i in range(1, 7):
                #             c_name = row.get(f'card{i}_name')
                #             c_type = row.get(f'card{i}_type')
                #             c_id = row.get(f'card{i}_id')
                #             if pd.notna(c_name) and str(c_name) not in ['nan', 'Unknown']:
                #                 uma_cards_list.append({'Name': c_name, 'Type': c_type, 'ID': c_id})
                    
                #     if uma_cards_list:
                #         from uma_utils import render_visual_card_list
                #         c_df = pd.DataFrame(uma_cards_list)
                #         stats = c_df.groupby('ID').agg({'Name':'first','Type':'first','ID':'count'}).rename(columns={'ID':'Count'}).reset_index()
                #         stats['Usage %'] = (stats['Count'] / len(winners_df) * 100)
                #         render_visual_card_list(stats, title="", limit=6)
                
                render_build_guide(df_filtered)

    # =========================================================
    # TAB 2: STATS & BUILD (Aggregate)
    # =========================================================
    with tab_stats:

        
        
        if winners_df.empty:
            st.warning("No winners to analyze.")
        else:
            # --- 1. APTITUDE ANALYSIS (NEW) ---
            st.markdown("### 🧬 Aptitude Analysis")
            st.caption("Percentage of winners with **S-Rank** aptitude in relevant categories.")
            
           # Helper to plot donut chart
            def plot_aptitude(col, title, container):
                counts = winners_df[col].value_counts().reset_index()
                counts.columns = ['Rank', 'Count']
                
                # Sort Order
                rank_order = ['S', 'A', 'B', 'C', 'D', 'E', 'F', 'G']
                counts['Rank'] = pd.Categorical(counts['Rank'], categories=rank_order, ordered=True)
                counts = counts.sort_values('Rank')
                
                # Calculate S-Rate
                total = counts['Count'].sum()
                s_count = counts[counts['Rank'] == 'S']['Count'].sum()
                s_rate = (s_count / total * 100) if total > 0 else 0
                
                with container:
                    st.metric(f"{title} S-Rank %", f"{s_rate:.1f}%")
                    fig = px.pie(counts, values='Count', names='Rank', 
                                 color='Rank',
                                 color_discrete_map={'S': '#FFD700', 'A': '#C0C0C0', 'B': '#CD7F32'},
                                 hole=0.4)
                    fig.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0), height=120)
                    
                    # FIX: Added unique key based on column name
                    st.plotly_chart(style_fig(fig, 'Aptitude Impact'), width='stretch', key=f"apt_{col}")

            # Columns for the 3 metrics
            c_apt1, c_apt2 = st.columns(2, border=True)
            
            # Get Labels from Config
            dist_label = config_item.get('aptitude_dist', 'Distance')
            surf_label = config_item.get('aptitude_surf', 'Surface')

            # Plot if columns exist
            if 'Aptitude_Dist' in winners_df.columns:
                # e.g. "Distance (Long) S-Rank"
                plot_aptitude('Aptitude_Dist', f"Distance ({dist_label})", c_apt1)
                
            if 'Aptitude_Surface' in winners_df.columns:
                # e.g. "Surface (Turf) S-Rank"
                plot_aptitude('Aptitude_Surface', f"Surface ({surf_label})", c_apt2)
                
            
            st.markdown("---")

            st.subheader("💪 Stat Distributions (Winners Only)")
            # --- 1. BOX PLOTS (Stat Spread) ---
            stat_cols = ['Speed', 'Stamina', 'Power', 'Guts', 'Wit']
            # Melt for Faceted Box Plot
            melted_stats = winners_df[stat_cols].melt(var_name='Stat', value_name='Value')
            
            fig_box = px.box(melted_stats, x='Stat', y='Value', color='Stat', 
                             points="all", # Show individual dots
                             color_discrete_sequence=px.colors.qualitative.Bold)
            fig_box.update_layout(legend=dict(title=None, orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            st.plotly_chart(style_fig(fig_box, "Stat Spread of Winners"), width='stretch')
            
            st.markdown("---")
            
            # --- 2. SKILL COUNT HISTOGRAM ---
            valid_counts = winners_df[winners_df['Skill_Count'] > 0]
            if 'Skill_Count' in winners_df.columns:
                fig_hist = px.histogram(valid_counts, x='Skill_Count', nbins=15, 
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
                                   color='Clean_Style', color_discrete_sequence=px.colors.qualitative.Pastel, orientation='v', hover_data=['Runs'])
                fig_style.update_layout(legend=dict(title=None, orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
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
                                  labels={'x': 'Gate Number', 'y': 'Number of Wins'}, orientation='v')
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
        title_scope = f" {selected_uma}" if selected_uma != "All Umas" else "All Umas"
        st.subheader(f"🥛 Hall of Milk ({title_scope})")
        
        # 1. Base copy
        rec_df = winners_df.copy()

        rec_df['Clean_IGN'] = rec_df['Clean_IGN'].fillna("Unknown Trainer") 
        rec_df = rec_df[rec_df['Clean_Style'] != 'nan']
        rec_df['Skill_Count'] = rec_df['Skill_Count'].fillna(0).astype(int) 
        
        if rec_df.empty:
            st.warning(f"No winners found for {selected_uma}. Cannot determine records.")
        else:
            # 2. Calculate Totals
            # Fill NaNs with 0 to prevent crashes, but we will filter them out next
            stat_cols = ['Speed','Stamina','Power','Guts','Wit']
            rec_df[stat_cols] = rec_df[stat_cols].fillna(0)
            rec_df['Total_Stats'] = rec_df[stat_cols].sum(axis=1)
            
            # 3. Create a "Valid Stats" Subset for Records
            # This filters out Manual CSV entries that have no stats (Total = 0)
            # so they don't incorrectly show up as "Underdog" or "Lowest Speed"
            valid_stats_df = rec_df[rec_df['Total_Stats'] > 1].copy()

            valid_stats_df['Clean_Style'] = valid_stats_df['Clean_Style'].fillna("Opponent Uma")
            
            # --- CUSTOM HTML CARD FUNCTION ---
            def record_card(label, value, row, color="#FFD700"):
                # 1. Stats String
                stats_txt = f"<b style='color:#ccc'>Stats:</b> {row.get('Speed',0)} / {row.get('Stamina',0)} / {row.get('Power',0)} / {row.get('Guts',0)} / {row.get('Wit',0)}"
                
                # 2. Skills String (Show ALL skills)
                skills = row.get('Skill_List', [])
                if isinstance(skills, list) and skills:
                    skills_str = ", ".join(skills)
                else:
                    skills_str = "No skills recorded (No OCR submission)"

                # Check for explicit 0 (Opponent) or explicit False
                val = row.get('is_user_val')
                is_opponent = False
                
                # Check numeric/boolean False
                if val is not None:
                     try:
                         if int(val) == 0: is_opponent = True
                     except:
                         pass
                
                disclaimer = ""
                if is_opponent:
                    disclaimer = "<br><span style='color:#EF553B; font-size:0.8em; font-style:italic;'>⚠️ Opponent Data (Not User)</span>"
                
                # 3. HTML Structure
                card_html = f"""
                <div style="
                    height: 100%;
                    display: flex;
                    flex-direction: column;
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
                        {disclaimer}  </div>
                    <div style="font-size:0.85em; color:#DDD; margin-bottom:8px; font-family:monospace; flex-grow: 1;">
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
                # REPLACED: Fastest Time -> Hardest Opponent
                # Find the opponent (is_user=0) with the highest Total Stats
                if not valid_stats_df.empty:
                    # Filter for opponents specifically
                    opponents = valid_stats_df[valid_stats_df['is_user'] == 0]
                    
                    if not opponents.empty:
                        hardest_idx = opponents['Total_Stats'].idxmax()
                        hardest = opponents.loc[hardest_idx]
                        record_card("💀 Hardest Opponent", f"{float(str(hardest['Total_Stats']))} Total Stats", hardest, "#FF4B4B")
                    else:
                        st.info("No opponent data with stats available.")
                else:
                    st.info("Insufficient stat data.")
            
            with c2:
                if 'Skill_Count' in rec_df.columns:
                    valid = rec_df[rec_df['Skill_Count'] > 0]
                    if not valid.empty:
                        min_skill = valid.loc[valid['Skill_Count'].idxmin()]
                        # For Minimalist, value is "X Skills"
                        record_card("📉 Minimalist Build (Lowest Number of Skills)", f"{min_skill['Skill_Count']} Skills", min_skill, "#AB63FA")
            
            with c3:
                # Rarest Champion (Logic remains the same, uses full rec_df)
                if selected_uma == "All Umas":
                    win_counts = winners_df['Clean_Uma'].value_counts()
                    entry_counts = df_filtered['Clean_Uma'].value_counts()
                    unique_winners = winners_df['Clean_Uma'].unique()
                    
                    if len(unique_winners) > 0:
                        data = [{'Uma': u, 'Wins': win_counts.get(u,0), 'Entries': entry_counts.get(u,0)} for u in unique_winners]
                        cand_df = pd.DataFrame(data).sort_values(by=['Wins', 'Entries'], ascending=[True, True])
                        cand_df = cand_df[cand_df['Entries'] > 0]  # Ensure at least 1 entry to avoid division by zero
                        cand_df = cand_df.dropna(subset=['Uma'])
                        
                        rarest_uma = cand_df.iloc[0]['Uma']
                        rarest_wins = cand_df.iloc[0]['Wins']
                        rarest_entries = cand_df.iloc[0]['Entries']
                        rarest_matches = winners_df[winners_df['Clean_Uma'] == rarest_uma]
                        
                        if not rarest_matches.empty:
                            rarest_row = rarest_matches.iloc[0]
                            record_card("🦄 Rarest Champion (Least Wins/Entries)", f"{rarest_wins} Wins / {rarest_entries} Runs", rarest_row, "#FFD700")
                        else:
                            st.info("Insufficient data to determine Rarest Champion.")
                else:
                    style_counts = df_filtered['Clean_Style'].value_counts()
                    rec_df['Style_Pop'] = rec_df['Clean_Style'].map(style_counts)
                    if not rec_df['Style_Pop'].isnull().all():
                        rarest = rec_df.loc[rec_df['Style_Pop'].idxmin()]
                        record_card("🦄 Rare Strategy", f"{rarest['Clean_Style']}", rarest, "#FFD700")
                    else:
                        st.info("Insufficient data to determine Rare Strategy.")
            
            # --- ROW 2: STATS ---
            c4, c5, c6 = st.columns(3)
            # Only show these if we actually have valid stat data
            if not valid_stats_df.empty:
                with c4:
                    underdog = valid_stats_df.loc[valid_stats_df['Total_Stats'].idxmin()]
                    record_card("🐕 Underdog (Lowest Total Stats)", underdog['Total_Stats'], underdog, "#EF553B")
                with c5:
                    min_spd = valid_stats_df.loc[valid_stats_df['Speed'].idxmin()]
                    record_card("🐌 Lowest Speed", min_spd['Speed'], min_spd, "#FFA15A")
                with c6:
                    min_pwr = valid_stats_df.loc[valid_stats_df['Power'].idxmin()]
                    record_card("💪 Lowest Power", min_pwr['Power'], min_pwr, "#19D3F3")

            c7, c8, c9 = st.columns(3)
            # Only show these if we actually have valid stat data
            if not valid_stats_df.empty:
                with c7:
                    min_sta = valid_stats_df.loc[valid_stats_df['Stamina'].idxmin()]
                    record_card("😴 Lowest Stamina", min_sta['Stamina'], min_sta, "#FF6692")
                with c8:
                    max_guts = valid_stats_df.loc[valid_stats_df['Guts'].idxmax()]
                    record_card("🏃 Highest Guts", max_guts['Guts'], max_guts, "#B6E880")
                with c9:
                    min_wit = valid_stats_df.loc[valid_stats_df['Wit'].idxmin()]
                    record_card("🧠 Lowest Wit", min_wit['Wit'], min_wit, "#FF97FF")

            # --- NICHE GALLERY ---
            st.markdown("### 📜 Niche Hall of Fame")
            # 1. Identify Niche Winners
            if selected_uma == "All Umas":
                st.caption("Winners with < 10 Total Entries in this Group.")
                entry_counts = df_filtered['Clean_Uma'].value_counts()
                niche_winners = rec_df[rec_df['Clean_Uma'].map(entry_counts) < 10].copy()
            else:
                st.caption(f"Winners using off-meta strategies for {selected_uma}.")
                style_map = df_filtered.groupby('Clean_Uma')['Clean_Style'].value_counts(normalize=True)
                niche_indices = []
                for idx, row in rec_df.iterrows():
                    try:
                        if style_map[row['Clean_Uma']][row['Clean_Style']] < 0.15:
                            niche_indices.append(idx)
                    except: continue
                niche_winners = rec_df.loc[niche_indices]

            # 2. Clean & Deduplicate
            if not niche_winners.empty:
                # Filter out rows with empty stats (optional, keeps list clean)
                niche_winners = niche_winners[niche_winners['Total_Stats'] > 0]
                
                # Deduplicate based on IGN and Character Name
                niche_winners = niche_winners.drop_duplicates(subset=['Clean_IGN', 'Clean_Uma'])
                
                disp = niche_winners[['Clean_IGN', 'Clean_Uma', 'Clean_Style', 'Speed', 'Stamina', 'Power', 'Guts', 'Wit', 'Skill_Count']]
                st.dataframe(disp, width='stretch', hide_index=True, column_config={
                    "Clean_IGN": st.column_config.TextColumn("Player"),
                    "Clean_Uma": st.column_config.TextColumn("Uma"),
                    "Clean_Style": st.column_config.TextColumn("Running Style"),
                    "Skill_Count": st.column_config.NumberColumn("Number of Skills")
                })
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
                title=None
            )
            add_img_chart(meta_df, fig_scatter)
                    
            
            # Quadrant Lines (Median)
            avg_wr = meta_df['Win Rate %'].mean()
            avg_pick = meta_df['Pick Rate %'].mean()
            
            fig_scatter.add_hline(y=avg_wr, line_dash="dot", line_color="gray", annotation_text="Avg Win Rate")
            fig_scatter.add_vline(x=avg_pick, line_dash="dot", line_color="gray", annotation_text="Avg Pick Rate")
            
            fig_scatter.update_layout(legend=dict(title=None, orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            fig_scatter.update_traces(textposition='top center')
            st.plotly_chart(style_fig(fig_scatter, title=f'{selected_league} Finals Bubble Chart'), width='stretch', config=BUBBLE_CONFIG)
            
            st.caption("""
            - **Top Right:** Meta Kings (High Use, High Wins)
            - **Top Left:** Specialists / Sleepers (Low Use, High Wins)
            - **Bottom Right:** Popular Bait (High Use, Low Wins)
            """)