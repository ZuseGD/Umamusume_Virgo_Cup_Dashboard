import streamlit as st
import plotly.express as px
from utils import style_fig, PLOT_CONFIG

def show_view(df, team_df):
    st.header("⚔️ Team & Strategy")
    
    tab1, tab2, tab3 = st.tabs(["Ideal Teams", "Running Style", "Runaway Impact"])
    
    # Filter Teams
    comp_counts = team_df['Team_Comp'].value_counts()
    valid_comps = comp_counts[comp_counts > 7].index.tolist()
    filtered_team_df = team_df[team_df['Team_Comp'].isin(valid_comps)]

    with tab1:
        st.subheader("🏆 Meta Team Compositions")
        if not filtered_team_df.empty:
            comp_stats = filtered_team_df.groupby('Team_Comp').agg({'Calculated_WinRate': 'mean', 'Clean_Races': 'count'}).reset_index().rename(columns={'Clean_Races': 'Usage Count'})
            fig_comps = px.bar(
                comp_stats.sort_values('Calculated_WinRate', ascending=False).head(15),
                x='Calculated_WinRate', y='Team_Comp', orientation='h', color='Calculated_WinRate',
                color_continuous_scale='Plasma', text='Usage Count', template='plotly_dark', height=700
            )
            fig_comps.update_layout(yaxis_title=None, xaxis_title="Avg Win Rate (%)")
            fig_comps.update_traces(texttemplate='%{text} Entries', textposition='inside')
            st.plotly_chart(style_fig(fig_comps, height=700), use_container_width=True, config=PLOT_CONFIG)
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
        st.plotly_chart(style_fig(fig_style, height=500), use_container_width=True, config=PLOT_CONFIG)

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
        st.plotly_chart(style_fig(fig_runner, height=500), use_container_width=True, config=PLOT_CONFIG)