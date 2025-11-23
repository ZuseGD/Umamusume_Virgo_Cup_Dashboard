# %%
import plotly.express as px
import plotly.io as pio
from virgo_core import team_df, calculate_score 

pio.renderers.default = "browser"

# %%
if not team_df.empty:
    print("📊 Plotting Leaderboard...")
    named_teams = team_df[team_df['Display_IGN'] != "Anonymous Trainer"].copy()
    
    leaderboard = named_teams.groupby(['Display_IGN', 'Team_Comp']).agg({
        'Clean_Wins': 'sum', 
        'Clean_Races': 'sum'
    }).reset_index()
    
    leaderboard['Global_WinRate'] = (leaderboard['Clean_Wins'] / leaderboard['Clean_Races']) * 100
    leaderboard['Score'] = leaderboard.apply(lambda x: calculate_score(x['Clean_Wins'], x['Clean_Races']), axis=1)
    leaderboard = leaderboard[leaderboard['Clean_Races'] >= 15]
    
    top_leaders = leaderboard.sort_values('Score', ascending=False).head(10)
    top_leaders['Label'] = top_leaders['Display_IGN'] + " (" + top_leaders['Team_Comp'] + ")"
    
    fig_leader = px.bar(
        top_leaders, 
        x='Score', 
        y='Label', 
        orientation='h', 
        color='Global_WinRate', 
        title="Top 10 Trainers (Sorted by Performance Score)", 
        text='Clean_Wins', 
        labels={'Score': 'Performance Score', 'Label': '', 'Global_WinRate': 'Win Rate'}, 
        template='plotly_dark', 
        color_continuous_scale='Turbo'
    )
    fig_leader.update_traces(texttemplate='Wins: %{text} | WR: %{marker.color:.1f}%', textposition='inside')
    fig_leader.update_layout(yaxis={'categoryorder':'total ascending'})
    fig_leader.show()