import streamlit as st
import plotly.express as px
from utils import style_fig, PLOT_CONFIG, dynamic_height

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
            comp_stats = filtered_team_df.groupby('Team_Comp').agg({'Calculated_WinRate': 'mean', 'Clean_Races': 'count'}).reset_index().rename(columns={'Clean_Races': 'Usage Count'})
            # Create a short version: "Uma1, Uma2..."
            comp_stats['Short_Comp'] = comp_stats['Team_Comp'].apply(
                lambda x: x[:25] + "..." if len(x) > 25 else x
            )
            # Get number of items to plot
            n_items = len(comp_stats.head(15))
            # Calculate dynamic height
            chart_height = dynamic_height(n_items, min_height=500, per_item=50)
            fig_comps = px.bar(
                comp_stats.sort_values('Calculated_WinRate', ascending=True).head(15),
                x='Calculated_WinRate', y='Short_Comp', orientation='h', color='Calculated_WinRate',
                color_continuous_scale='Plasma', text='Usage Count', template='plotly_dark', height=chart_height, 
                hover_data={'Team_Comp': True, 'Calculated_WinRate': ':.2f', 'Usage Count': True, 'Short_Comp': False}
            )
            fig_comps.update_layout(yaxis_title=None, xaxis_title="Avg Win Rate (%)")
            fig_comps.update_traces(texttemplate='%{text} Entries', textposition='inside')
            st.plotly_chart(style_fig(fig_comps, height=chart_height), width="stretch", config=PLOT_CONFIG)
        else:
            st.info("Not enough data.")

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
        
        style_df = df.copy()
        style_df['Standard_Style'] = style_df['Clean_Style'].apply(standardize_style)
        style_stats = style_df.groupby('Standard_Style').agg({'Calculated_WinRate': 'mean', 'Clean_Races': 'count'}).reset_index()
        style_stats = style_stats[(style_stats['Clean_Races'] > 20) & (style_stats['Standard_Style'] != 'Unknown')]
        desired_order = ['Runaway', 'Front Runner', 'Pace Chaser', 'Late Surger', 'End Closer']
        
        fig_style = px.bar(
            style_stats, x='Calculated_WinRate', y='Standard_Style', orientation='h', color='Calculated_WinRate',
            template='plotly_dark', title="Win Rate by Running Style", text='Calculated_WinRate', color_continuous_scale='Viridis', height=500
        )
        fig_style.update_layout(yaxis={'categoryorder':'array', 'categoryarray': desired_order[::-1]}, xaxis_title="Avg Win Rate (%)", yaxis_title=None)
        fig_style.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        st.plotly_chart(style_fig(fig_style, height=500), width="stretch", config=PLOT_CONFIG)

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

    with tab4:
        st.subheader("📈 Meta Evolution over Time")
        
        # Get Top 10 Teams
        top_teams = team_df['Team_Comp'].value_counts().head(10).index.tolist()
        
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
        else:
            st.info("Not enough data to track evolution.")