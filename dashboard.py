import streamlit as st
from utils import load_data, footer_html, DESCRIPTIONS
from PIL import Image
import os

# 1. Page Config
page_icon = "🏆"
if os.path.exists("images/moologo2.jpg"):
    page_icon = Image.open("images/moologo2.jpg")

st.set_page_config(
    page_title="Virgo Cup CM5", 
    page_icon=page_icon, 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# 2. CSS
st.markdown("""
<style>
    [data-testid="stSidebar"] {display: none;}
    [data-testid="collapsedControl"] {display: none;}
    div[data-testid="stVerticalBlock"] > div:has(div[data-testid="stRadio"]) {
        position: sticky; top: 0; z-index: 999; background: #0E1117; padding-bottom: 10px; border-bottom: 1px solid #333;
    }
</style>
""", unsafe_allow_html=True)

# 3. Load Data
try:
    df, team_df = load_data()
except:
    st.error("Database Connection Failed")
    st.stop()

# 4. GLOBAL SIDEBAR FILTERS
st.sidebar.header("⚙️ Global Filters")

# Group Filter
groups = list(df['Clean_Group'].unique())
selected_group = st.sidebar.multiselect("CM Group", groups, default=groups)

# Round/Day Filter
rounds = sorted(list(df['Round'].unique()))
days = sorted(list(df['Day'].unique()))
selected_round = st.sidebar.multiselect("Round", rounds, default=rounds)
selected_day = st.sidebar.multiselect("Day", days, default=days)

# APPLY FILTERS
if selected_group:
    df = df[df['Clean_Group'].isin(selected_group)]
    team_df = team_df[team_df['Clean_Group'].isin(selected_group)]
if selected_round:
    df = df[df['Round'].isin(selected_round)]
    team_df = team_df[team_df['Round'].isin(selected_round)]
if selected_day:
    df = df[df['Day'].isin(selected_day)]
    team_df = team_df[team_df['Day'].isin(selected_day)]

# 5. TOP NAVIGATION
st.markdown("## 🏆 Virgo Cup Analytics")
nav_cols = st.columns([1, 1, 1, 1, 1])

if 'current_page' not in st.session_state:
    st.session_state.current_page = "Home"

def set_page(page_name):
    st.session_state.current_page = page_name

with nav_cols[0]:
    if st.button("🌍 Home", use_container_width=True): set_page("Home")
with nav_cols[1]:
    if st.button("⚔️ Teams", use_container_width=True): set_page("Teams")
with nav_cols[2]:
    if st.button("🐴 Umas", use_container_width=True): set_page("Umas")
with nav_cols[3]:
    if st.button("🃏 Resources", use_container_width=True): set_page("Resources")
with nav_cols[4]:
    if st.button("ℹ️ Credits", use_container_width=True): set_page("Credits")

st.markdown("---")

# 6. DISCLAIMER (Global)
with st.expander("⚠️ Data Disclaimer (Survivorship Bias)"):
    st.markdown(DESCRIPTIONS["bias"])

# 7. ROUTING
if st.session_state.current_page == "Home":
    from views import home
    home.show_view(df, team_df)

elif st.session_state.current_page == "Teams":
    from views import teams
    teams.show_view(df, team_df)

elif st.session_state.current_page == "Umas":
    from views import umas
    umas.show_view(df, team_df)

elif st.session_state.current_page == "Resources":
    from views import resources
    resources.show_view(df, team_df)

elif st.session_state.current_page == "Credits":
    from views import credits
    credits.show_view()

# 8. FOOTER
st.markdown(footer_html, unsafe_allow_html=True)