# %%
import os

# List of plot files to include
PLOT_FILES = [
    "virgo_plot_money.py",
    "virgo_plot_teams.py",
    "virgo_plot_leaderboard.py", 
    # Add other plot files here if you create them (umas, strategy, etc)
]

def read_clean(filename):
    """Reads file and strips 'from virgo_core' lines and 'fig.show()'"""
    if not os.path.exists(filename): return ""
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    clean_lines = []
    for line in lines:
        if "from virgo_core" in line: continue  # Strip local import
        if "pio.renderers" in line: continue    # Strip renderer config
        if ".show()" in line:                   # Convert show to streamlit
            var_name = line.split(".show()")[0].strip()
            clean_lines.append(f"st.plotly_chart({var_name}, width='stretch')\n")
        else:
            clean_lines.append(line)
    return "".join(clean_lines)

# 1. Read Core Logic (We need the functions, but we skip the execution at bottom)
with open("virgo_core.py", "r") as f:
    core_raw = f.read()
    # Hacky split to get functions but not the execution block
    core_logic = core_raw.split("# --- EXPOSE DATA")[0]

# 2. Assemble Dashboard
dashboard_code = f"""
import streamlit as st
import pandas as pd
import plotly.express as px
import re
import numpy as np

# --- CONFIGURATION ---
st.set_page_config(page_title="Virgo Cup CM5", page_icon="🏆", layout="wide")

{core_logic}

# --- APP EXECUTION ---
# Copying the execution logic from core, but wrapped in Streamlit cache
@st.cache_data(ttl=60)
def get_data():
    return load_data()

df = get_data()

if not df.empty:
    # Reconstruct Teams (Logic copied from core execution)
    team_df = df.groupby(['Clean_IGN', 'Display_IGN', 'Clean_Group', 'Round', 'Day', 'Original_Spent', 'Sort_Money']).agg({{
        'Clean_Uma': lambda x: sorted(list(x)), 
        'Clean_Style': lambda x: list(x),       
        'Calculated_WinRate': 'mean',           
        'Clean_Races': 'mean',
        'Clean_Wins': 'mean'
    }}).reset_index()
    team_df['Score'] = team_df.apply(lambda x: calculate_score(x['Clean_Wins'], x['Clean_Races']), axis=1)
    team_df['Uma_Count'] = team_df['Clean_Uma'].apply(len)
    team_df = team_df[team_df['Uma_Count'] == 3]
    team_df['Team_Comp'] = team_df['Clean_Uma'].apply(lambda x: ", ".join(x))
    
    comp_counts = team_df['Team_Comp'].value_counts()
    filtered_team_df = team_df[team_df['Team_Comp'].isin(comp_counts[comp_counts > 7].index)]

    st.title("🏆 Virgo Cup Analytics")
    
    # --- PLOTS ---
    tab1, tab2, tab3 = st.tabs(["Money", "Teams", "Leaderboard"])
    
    with tab1:
        {read_clean("virgo_plot_money.py")}
        
    with tab2:
        {read_clean("virgo_plot_teams.py")}
        
    with tab3:
        {read_clean("virgo_plot_leaderboard.py")}

"""

with open("dashboard.py", "w", encoding="utf-8") as f:
    f.write(dashboard_code)

print("✅ dashboard.py generated successfully!")