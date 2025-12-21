import streamlit as st
import plotly.express as px
from uma_utils import style_fig, PLOT_CONFIG, dynamic_height, show_description

def show_view(df, team_df):
    st.set_page_config(page_title="⚔️ Team & Strategy Dashboard", layout="wide")
    st.header("Team & Strategy")
    
    # Calculate Totals for Percentages
    total_sessions = len(team_df)
    total_umas = len(df)

    tab1, tab2, tab3, tab4 = st.tabs(["Ideal Teams", "Running Style", "Runaway Impact", "Meta Evolution"])
    
    # Filter Teams (Min 5 entries to be relevant)
    comp_counts = team_df['Team_Comp'].value_counts()
    valid_comps = comp_counts[comp_counts >= 5].index.tolist()
    filtered_team_df = team_df[team_df['Team_Comp'].isin(valid_comps)]

    # --- TAB 1: META TEAMS ---
    with tab1:
        st.subheader("🏆 Meta Team Compositions")
        if not filtered_team_df.empty:
            # 1. PREPARE DATA
            comp_stats = filtered_team_df.groupby('Team_Comp').agg({
                'Calculated_WinRate': 'mean', 
                'Clean_Races': 'count' # Count of Sessions
            }).reset_index().rename(columns={'Clean_Races': 'Entries'})
            
            # Calculate Pick Rate
            comp_stats['Pick_Rate'] = (comp_stats['Entries'] / total_sessions) * 100
            
            # 2. BUBBLE CHART (Pick Rate vs Win Rate)
            st.markdown("#### 💠 Meta Quadrants (Pick Rate vs. Win Rate)")
            fig_bubble = px.scatter(
                comp_stats,
                x='Pick_Rate',
                y='Calculated_WinRate',
                size='Pick_Rate',             
                color='Calculated_WinRate',     
                hover_name='Team_Comp',
                color_continuous_scale='Plasma',
                template='plotly_dark',
                title="Team Tier List",
                labels={'Pick_Rate': 'Pick Rate (%)', 'Calculated_WinRate': 'Win Rate %'},
                hover_data={'Entries': True, 'Pick_Rate': ':.2f', 'Calculated_WinRate': ':.1f'},
                height=500,
                size_max=80
            )
            
            # Averages
            avg_pick = comp_stats['Pick_Rate'].mean()
            avg_wr = comp_stats['Calculated_WinRate'].mean()
            fig_bubble.add_vline(x=avg_pick, line_dash="dot", annotation_text="Avg Pick Rate")
            fig_bubble.add_hline(y=avg_wr, line_dash="dot", annotation_text="Avg Win Rate")
            
            st.plotly_chart(style_fig(fig_bubble, height=500), width="stretch", config=PLOT_CONFIG)
            show_description("teams_bubble")
            
            st.markdown("---")

        

    # --- TAB 2: RUNNING STYLE ---
    with tab2:
        st.subheader("🏃 Performance by Running Style")
        
        # Helper Functions
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
            standardized = [standardize_style(s) for s in style_list]
            standardized.sort() 
            return ", ".join(standardized)

        # CHART 1: TEAM STYLE COMBINATIONS
        st.markdown("#### 💠 Meta Style Combinations")
        
        style_team_df = team_df.copy()
        style_team_df['Style_Comp'] = style_team_df['Clean_Style'].apply(get_style_comp)
        
        comp_stats = style_team_df.groupby('Style_Comp').agg({
            'Calculated_WinRate': 'mean', 
            'Clean_Races': 'count'
        }).reset_index().rename(columns={'Clean_Races': 'Entries'})
        
        # Calculate Pick Rate (Relative to Sessions)
        comp_stats['Pick_Rate'] = (comp_stats['Entries'] / total_sessions) * 100
        
        valid_comps = comp_stats[comp_stats['Entries'] >= 5]

        if not valid_comps.empty:
            fig_style_bubble = px.scatter(
                valid_comps,
                x='Pick_Rate',
                y='Calculated_WinRate',
                size='Pick_Rate',
                color='Style_Comp', 
                hover_name='Style_Comp',
                title="Winning Style Combinations",
                template='plotly_dark',
                labels={'Pick_Rate': 'Pick Rate (%)', 'Calculated_WinRate': 'Win Rate %'},
                height=500
            )
            
            avg_wr = valid_comps['Calculated_WinRate'].mean()
            avg_pick = valid_comps['Pick_Rate'].mean()
            fig_style_bubble.add_hline(y=avg_wr, line_dash="dot", annotation_text="Avg Win Rate")
            fig_style_bubble.add_vline(x=avg_pick, line_dash="dot", annotation_text="Avg Pick Rate")

            final_fig = style_fig(fig_style_bubble, height=500)
            final_fig.update_layout(
                legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5),
                margin=dict(b=80)
            )
            st.plotly_chart(final_fig, width="stretch", config=PLOT_CONFIG)
            show_description("teams_meta")
        else:
            st.info("Not enough data to show style combinations.")

        st.markdown("---")

        # CHART 2: INDIVIDUAL STYLE PERFORMANCE
        st.markdown("#### 📋 Individual Style Performance")
        
        indiv_style_df = df.copy()
        indiv_style_df['Standard_Style'] = indiv_style_df['Clean_Style'].apply(standardize_style)
        
        style_stats = indiv_style_df.groupby('Standard_Style').agg({
            'Calculated_WinRate': 'mean', 
            'Clean_Races': 'count'
        }).reset_index().rename(columns={'Clean_Races': 'Entries'})
        
        # Calculate Pick Rate (Relative to Umas)
        style_stats['Pick_Rate'] = (style_stats['Entries'] / total_umas) * 100
        
        style_stats = style_stats[(style_stats['Entries'] > 5) & (style_stats['Standard_Style'] != 'Unknown')]
        desired_order = ['Runaway', 'Front Runner', 'Pace Chaser', 'Late Surger', 'End Closer']
        
        fig_style = px.bar(
            style_stats, 
            x='Calculated_WinRate', 
            y='Standard_Style', 
            orientation='h', 
            color='Calculated_WinRate',
            template='plotly_dark', 
            text='Pick_Rate', 
            color_continuous_scale='Viridis', 
            height=400,
            hover_data={'Entries': True},
            labels={'Calculated_WinRate': 'Win Rate (%)', 'Standard_Style': 'Running Style', 'Pick_Rate': 'Pick Rate (%)'}
        )
        
        fig_style.update_layout(
            yaxis={'categoryorder':'array', 'categoryarray': desired_order[::-1]}, 
            xaxis_title="Avg Win Rate (%)", 
            yaxis_title=None
        )
        fig_style.update_traces(
            texttemplate='Pick: %{text:.1f}%', 
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>Win Rate: %{x:.1f}%<br>Pick Rate: %{text:.1f}%<br>Entries: %{customdata[0]}<extra></extra>'
        )
        st.plotly_chart(style_fig(fig_style, height=400), width="stretch", config=PLOT_CONFIG)
        show_description("style")

    # --- TAB 3: RUNAWAY IMPACT ---
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
        
        # Aggregation
        runner_stats = team_df.groupby('Has_Runaway').agg({
            'Calculated_WinRate': 'mean',
            'Clean_Races': 'count'
        }).reset_index().rename(columns={'Clean_Races': 'Entries'})
        
        runner_stats['Strategy'] = runner_stats['Has_Runaway'].map({True: 'With Runaway', False: 'No Runaway'})
        runner_stats['Pick_Rate'] = (runner_stats['Entries'] / total_sessions) * 100
        
        fig_runner = px.bar(
            runner_stats, x='Strategy', y='Calculated_WinRate', color='Strategy',
            template='plotly_dark', text='Pick_Rate',
            color_discrete_sequence=['#00CC96', '#EF553B'], height=500,
            hover_data={'Entries': True},
            labels={'Calculated_WinRate': 'Win Rate (%)', 'Pick_Rate': 'Pick Rate (%)'}
        )
        fig_runner.update_traces(
            texttemplate='Usage: %{text:.1f}%', 
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>Win Rate: %{y:.1f}%<br>Entries: %{customdata[0]}<extra></extra>'
        )
        fig_runner.update_layout(xaxis_title=None, showlegend=False)
        st.plotly_chart(style_fig(fig_runner, height=500), width="stretch", config=PLOT_CONFIG)
        show_description("runaway")

    # --- TAB 4: EVOLUTION ---
    with tab4:
        st.subheader("📈 Meta Evolution over Time")
        st.warning("Double click the legend items to isolate specific teams.")
        # Get Top 5 Teams
        top_teams = team_df['Team_Comp'].value_counts().head(5).index.tolist()
        
        if top_teams:
            # 1. Get Daily Totals (For % Calculation)
            daily_totals = team_df.groupby(['Round', 'Day']).size().reset_index(name='Total_Daily_Sessions')
            
            # 2. Filter & Group Specific Teams
            evo_df = team_df[team_df['Team_Comp'].isin(top_teams)]
            evo_stats = evo_df.groupby(['Round', 'Day', 'Team_Comp']).size().reset_index(name='Count')
            
            # 3. Merge to calculate Percentage
            evo_stats = evo_stats.merge(daily_totals, on=['Round', 'Day'])
            evo_stats['Pick_Rate'] = (evo_stats['Count'] / evo_stats['Total_Daily_Sessions']) * 100
            evo_stats['Session'] = evo_stats['Round'] + ' ' + evo_stats['Day']
            
            # 4. Plot
            fig_evo = px.line(
                evo_stats, 
                x='Session', 
                y='Pick_Rate', # <--- Now Percent!
                color='Team_Comp',
                title="Top 5 Teams: Daily Pick Rate %",
                markers=True, 
                template='plotly_dark',
                labels={'Pick_Rate': 'Pick Rate (%)', 'Team_Comp': 'Team Composition'}
            )
            fig_evo.update_layout(hovermode="x unified", yaxis_title="Pick Rate (%)")
            st.plotly_chart(style_fig(fig_evo, height=500), width="stretch", config=PLOT_CONFIG)
            show_description("evolution")
        else:
            st.info("Not enough data to track evolution.")