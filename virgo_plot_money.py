# %%
import plotly.express as px
import plotly.io as pio
from virgo_core import team_df # Import data from core

pio.renderers.default = "browser"

# %%
if not team_df.empty:
    print("📊 Plotting Money Box Plot...")
    team_df = team_df.sort_values('Sort_Money')
    fig_money = px.box(
        team_df, 
        x='Original_Spent', 
        y='Calculated_WinRate', 
        color='Original_Spent', 
        points="all", 
        title="Win Rate Distribution by Spending Tier", 
        template='plotly_dark', 
        color_discrete_sequence=px.colors.qualitative.Bold
    )
    fig_money.update_layout(showlegend=False)
    fig_money.show()