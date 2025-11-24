import streamlit as st
import plotly.express as px
from utils import style_fig, PLOT_CONFIG, dynamic_height, show_description

def show_view(df, team_df):
    st.header("⚔️ Team & Strategy")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Ideal Teams", "Running Style", "Runaway Impact", "Meta Evolution"])
    
    # Filter Teams
    comp_counts = team_df['Team_Comp'].value_counts()
    valid_comps = comp_counts[comp_counts > 7].index.tolist()
    filtered_team_df = team_df[team_df['Team_Comp'].isin(valid_comps)]

    with tab1:
        st.subheader("🏆 Meta Team Compositions")
        if not filtered_team_df.empty:
            # 1. PREPARE DATA
            comp_stats = filtered_team_df.groupby('Team_Comp').agg({
                'Calculated_WinRate': 'mean', 
                'Clean_Races': 'count'
            }).reset_index().rename(columns={'Clean_Races': 'Usage Count'})
            
            # 2. BUBBLE CHART (New!)
            st.markdown("#### 💠 Meta Quadrants (Popularity vs. Win Rate)")
            fig_bubble = px.scatter(
                comp_stats,
                x='Usage Count',
                y='Calculated_WinRate',
                size='Usage Count',             
                color='Calculated_WinRate',     
                hover_name='Team_Comp',         # <--- Keeps name in Tooltip ONLY
                color_continuous_scale='Plasma',
                template='plotly_dark',
                title="Team Tier List",
                labels={'Usage Count': 'Entries', 'Calculated_WinRate': 'Win Rate %'},
                height=500
            )
            
            # Add average lines to create quadrants
            avg_use = comp_stats['Usage Count'].mean()
            avg_wr = comp_stats['Calculated_WinRate'].mean()
            fig_bubble.add_vline(x=avg_use, line_dash="dot", annotation_text="Avg Popularity")
            fig_bubble.add_hline(y=avg_wr, line_dash="dot", annotation_text="Avg Win Rate")
            
            st.plotly_chart(style_fig(fig_bubble, height=500), width="stretch", config=PLOT_CONFIG)
            show_description("teams_bubble")
            
            st.markdown("---")

            # 3. BAR CHART (Existing - Updated for Mobile)
            st.markdown("#### 📋 Detailed Rankings")
            
            # Create Short Name for Mobile Axis
            comp_stats['Short_Comp'] = comp_stats['Team_Comp'].apply(
                lambda x: x[:25] + "..." if len(x) > 25 else x
            )
            
            # Calculate dynamic height
            n_items = len(comp_stats.head(10))
            chart_height = dynamic_height(n_items, min_height=500, per_item=50)
            
            fig_comps = px.bar(
                comp_stats.sort_values('Calculated_WinRate', ascending=True).head(15),
                x='Calculated_WinRate', 
                y='Short_Comp', 
                orientation='h', 
                color='Calculated_WinRate',
                color_continuous_scale='Plasma', 
                text='Usage Count', 
                template='plotly_dark', 
                height=chart_height,
                hover_name='Team_Comp'
            )
            fig_comps.update_layout(yaxis_title="Team Composition", xaxis_title="Avg Win Rate (%)")
            fig_comps.update_traces(texttemplate='%{text} Entries', textposition='inside')
            
            st.plotly_chart(style_fig(fig_comps, height=chart_height), width="stretch", config=PLOT_CONFIG)
            show_description("teams_meta")
            
        else:
            st.info("Not enough data. (Need >7 entries per team to display)")

    with tab2:
        st.subheader("🏃 Performance by Running Style")
        def standardize_style(style):
            s = str(style).lower().strip()
            if 'oonige' in s or 'escape' in s or 'runaway' in s: return 'Runaway'
            if 'runner' in s and 'front' not in s: return 'Runaway'
            if 'front' in s or 'leader' in s: return 'Front Runner'
            if 'pace' in s or 'betweener' in s: return 'Pace Chaser'
            if 'late' in s: return 'Late Surger'
            if 'end' in s or 'closer' in s: return 'End Closer'
            return 'Unknown'
        
        def get_style_comp(style_list):
            # 1. Standardize each style in the list
            # 2. Sort them (Critical for "Pace, End" == "End, Pace")
            # 3. Join into a string
            standardized = [standardize_style(s) for s in style_list]
            standardized.sort() 
            return ", ".join(standardized)

        # --- CHART 1: TEAM STYLE COMBINATIONS (Bubble) ---
        st.markdown("#### 💠 Meta Style Combinations")
        
        # Create a working copy to avoid warnings
        style_team_df = team_df.copy()
        
        # Apply the sorting logic to create the "Composition" string
        style_team_df['Style_Comp'] = style_team_df['Clean_Style'].apply(get_style_comp)
        
        # Aggregate Stats by Composition
        comp_stats = style_team_df.groupby('Style_Comp').agg({
            'Calculated_WinRate': 'mean', 
            'Clean_Races': 'count'
        }).reset_index().rename(columns={'Clean_Races': 'Entries'})
        
        # Filter: Only show comps with at least 5 entries to reduce noise
        valid_comps = comp_stats[comp_stats['Entries'] >= 5]

        if not valid_comps.empty:
            fig_style_bubble = px.scatter(
                valid_comps,
                x='Entries',
                y='Calculated_WinRate',
                size='Entries',
                color='Style_Comp', 
                hover_name='Style_Comp',
                title="Winning Style Combinations (Popularity vs Performance)",
                template='plotly_dark',
                labels={'Entries': 'Popularity (Entries)', 'Calculated_WinRate': 'Win Rate %'},
                height=500
            )
            
            # Add averages
            avg_wr = valid_comps['Calculated_WinRate'].mean()
            avg_pop = valid_comps['Entries'].mean()
            fig_style_bubble.add_hline(y=avg_wr, line_dash="dot", annotation_text="Avg Win Rate")
            fig_style_bubble.add_vline(x=avg_pop, line_dash="dot", annotation_text="Avg Popularity")

            st.plotly_chart(style_fig(fig_style_bubble, height=500), width="stretch", config=PLOT_CONFIG)
            show_description("teams_meta") # Reusing team meta description
        else:
            st.info("Not enough data to show style combinations.")

        st.markdown("---")

        # 3. BAR CHART (Existing)
        st.markdown("#### 📋 Detailed Rankings")
        desired_order = ['Runaway', 'Front Runner', 'Pace Chaser', 'Late Surger', 'End Closer']
        
        fig_style = px.bar(
            style_stats, 
            x='Calculated_WinRate', 
            y='Standard_Style', 
            orientation='h', 
            color='Calculated_WinRate',
            template='plotly_dark', 
            text='Calculated_WinRate', 
            color_continuous_scale='Viridis', 
            height=400,
            hover_data={'Clean_Races': True}
        )
        
        fig_style.update_layout(
            yaxis={'categoryorder':'array', 'categoryarray': desired_order[::-1]}, 
            xaxis_title="Avg Win Rate (%)", 
            yaxis_title=None
        )
        fig_style.update_traces(
            texttemplate='%{text:.1f}%', 
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>Win Rate: %{x:.1f}%<br>Entries: %{customdata[0]}<extra></extra>'
        )
        st.plotly_chart(style_fig(fig_style, height=400), width="stretch", config=PLOT_CONFIG)
        show_description("style")

    with tab3:
        st.subheader("⚠️ Impact of Runaways")
        def check_for_runaway(style_list):
            target_terms = ['Runaway', 'Runner', 'Escape', 'Oonige', 'Great Escape']
            for s in style_list:
                s_clean = str(s).strip()
                s_lower = s_clean.lower()
                if any(t.lower() in s_lower for t in target_terms):
                    if "front" in s_lower: continue 
                    return True
            return False
        
        team_df['Has_Runaway'] = team_df['Clean_Style'].apply(check_for_runaway)
        runner_stats = team_df.groupby('Has_Runaway')['Calculated_WinRate'].mean().reset_index()
        runner_stats['Strategy'] = runner_stats['Has_Runaway'].map({True: 'With Runaway', False: 'No Runaway'})
        
        fig_runner = px.bar(
            runner_stats, x='Strategy', y='Calculated_WinRate', color='Strategy',
            template='plotly_dark', text='Calculated_WinRate',
            color_discrete_sequence=['#00CC96', '#EF553B'], height=500
        )
        fig_runner.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig_runner.update_layout(xaxis_title=None, showlegend=False)
        st.plotly_chart(style_fig(fig_runner, height=500), width="stretch", config=PLOT_CONFIG)
        show_description("runaway")

    with tab4:
        st.subheader("📈 Meta Evolution over Time")
        
        # Get Top 10 Teams
        top_teams = team_df['Team_Comp'].value_counts().head(7).index.tolist()
        
        if top_teams:
            # Filter & Group
            evo_df = team_df[team_df['Team_Comp'].isin(top_teams)]
            evo_stats = evo_df.groupby(['Round', 'Day', 'Team_Comp']).size().reset_index(name='Count')
            evo_stats['Session'] = evo_stats['Round'] + ' ' + evo_stats['Day']
            
            fig_evo = px.line(
                evo_stats, x='Session', y='Count', color='Team_Comp',
                title="Top 5 Meta Teams: Popularity over Time",
                markers=True, template='plotly_dark'
            )
            fig_evo.update_layout(hovermode="x unified")
            st.plotly_chart(style_fig(fig_evo, height=500), width="stretch", config=PLOT_CONFIG)
            show_description("evolution")
        else:
            st.info("Not enough data to track evolution.")